from flask import Flask, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
from flask_cors import CORS
import os
from dotenv import load_dotenv
from invoice_generator import InvoiceGenerator
from invoice_parser import InvoiceParser
from customer_db import CustomerDatabase
from ai_invoice_assistant import AIInvoiceAssistant
import json
import re
import statistics
from datetime import datetime

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)

# Debug: Check if key is loaded
api_key_status = "✅ LOADED" if os.getenv('OPENAI_API_KEY') else "❌ NOT FOUND"
print(f"OPENAI_API_KEY status: {api_key_status}")
if os.getenv('OPENAI_API_KEY'):
    print(f"Key preview: {os.getenv('OPENAI_API_KEY')[:20]}...")

app = Flask(__name__, static_folder='../dist', static_url_path='')
CORS(app)

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLE_DIR = os.path.join(BASE_DIR, 'example-invoices')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
DATA_DIR = os.path.join(BASE_DIR, 'data')
SIGNATURES_DIR = os.path.join(BASE_DIR, 'signatures')
CUSTOMER_DB_PATH = os.path.join(DATA_DIR, 'customers.json')
ITEM_DB_PATH = os.path.join(DATA_DIR, 'items_catalog.json')
SIGNATURES_META_PATH = os.path.join(DATA_DIR, 'signatures_meta.json')

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SIGNATURES_DIR, exist_ok=True)

invoice_generator = InvoiceGenerator(TEMPLATES_DIR, OUTPUT_DIR)
invoice_parser = InvoiceParser(EXAMPLE_DIR)
customer_db = CustomerDatabase(CUSTOMER_DB_PATH)

def load_items_catalog():
    if os.path.exists(ITEM_DB_PATH):
        try:
            with open(ITEM_DB_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _normalize_label(text: str):
    t = (text or '').strip().lower()
    t = re.sub(r'\s+', ' ', t)
    t = re.sub(r'[^a-z0-9äöüß ]', '', t)
    return t


def _clean_customer_name(name: str):
    n = (name or '').strip()
    n = re.sub(r'^AN\s+', '', n, flags=re.IGNORECASE)
    if len(n) > 3 and n[:2].lower() == 'an' and n[2].islower():
        n = n[2:]
    return n.strip()


def _normalize_customer_key(name: str):
    t = _clean_customer_name(name).lower()
    t = t.replace('&', ' und ')
    t = re.sub(r'[^a-z0-9äöüß ]', ' ', t)
    # Remove common legal/company suffix noise for dedup
    t = re.sub(r'\b(gmbh|gbr|ag|kg|ug|mbh|ohg|co|co\.kg|co kg|e k|ek)\b', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def simplify_customers(customers):
    """Merge near-duplicate customer names and keep strongest/recent record."""
    merged = {}
    for c in customers or []:
        name = _clean_customer_name(c.get('name') or '')
        if not name:
            continue
        c = {**c, 'name': name}
        k = _normalize_customer_key(name)
        if not k:
            k = _normalize_label(name)
        if k not in merged:
            merged[k] = dict(c)
            continue

        existing = merged[k]
        # Prefer record with higher usage; keep richer address/city values
        if c.get('invoice_count', 0) > existing.get('invoice_count', 0):
            existing['name'] = c.get('name', existing.get('name', ''))
        existing['invoice_count'] = max(existing.get('invoice_count', 0), c.get('invoice_count', 0))
        existing['last_used'] = max(existing.get('last_used', ''), c.get('last_used', ''))
        if len(c.get('address', '') or '') > len(existing.get('address', '') or ''):
            existing['address'] = c.get('address', '')
        if len(c.get('city', '') or '') > len(existing.get('city', '') or ''):
            existing['city'] = c.get('city', '')
        if len(c.get('email', '') or '') > len(existing.get('email', '') or ''):
            existing['email'] = c.get('email', '')

        # merge invoice history if present
        inv_existing = set(existing.get('invoices', []) or [])
        inv_new = set(c.get('invoices', []) or [])
        existing['invoices'] = sorted([x for x in (inv_existing | inv_new) if x])
        merged[k] = existing

    rows = list(merged.values())
    rows.sort(key=lambda x: (x.get('name', '') or '').lower())
    return rows


def persist_customer_cleanup():
    before = len(customer_db.get_all_customers())
    rows = simplify_customers(customer_db.get_all_customers())
    rebuilt = {r.get('name', ''): r for r in rows if r.get('name')}
    customer_db.customers = rebuilt
    customer_db._save_db()
    return {'before': before, 'after': len(rows)}


def simplify_catalog_items(catalog_items, min_use_count=2):
    """Deduplicate item options and keep only meaningful/high-signal options by default."""
    grouped = {}
    for row in catalog_items or []:
        desc = (row.get('description') or '').strip()
        if not desc:
            continue
        k = _normalize_label(desc)
        if k not in grouped:
            grouped[k] = dict(row)
            grouped[k]['variants'] = 1
            continue

        ex = grouped[k]
        ex['variants'] = ex.get('variants', 1) + 1
        ex['use_count'] = max(ex.get('use_count', 0), row.get('use_count', 0))
        ex['last_used'] = max(ex.get('last_used', ''), row.get('last_used', ''))
        if len(desc) > len(ex.get('description', '') or ''):
            ex['description'] = desc
        # Blend rates conservatively
        er = float(ex.get('curated_rate', 0) or ex.get('default_rate', 0) or 0)
        rr = float(row.get('curated_rate', 0) or row.get('default_rate', 0) or 0)
        if rr > 0 and er > 0:
            ex['curated_rate'] = round((er + rr) / 2, 2)
        elif rr > 0:
            ex['curated_rate'] = rr
        grouped[k] = ex

    rows = list(grouped.values())
    # Hide one-off noisy items unless explicitly searched
    rows = [r for r in rows if r.get('use_count', 0) >= min_use_count]
    rows.sort(key=lambda x: (x.get('description', '') or '').lower())
    return rows

def load_signatures_meta():
    if os.path.exists(SIGNATURES_META_PATH):
        try:
            with open(SIGNATURES_META_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_signatures_meta(meta):
    os.makedirs(os.path.dirname(SIGNATURES_META_PATH), exist_ok=True)
    with open(SIGNATURES_META_PATH, 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

def save_items_catalog(catalog):
    os.makedirs(os.path.dirname(ITEM_DB_PATH), exist_ok=True)
    with open(ITEM_DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

def infer_job_type(description: str):
    d = (description or '').lower()
    if any(k in d for k in ['3d', 'render', 'visualisierung', 'animation']):
        return '3D'
    if any(k in d for k in ['livestream', 'stream', 'moderation']):
        return 'Livestream'
    if any(k in d for k in ['schnitt', 'editing', 'post', 'color grading']):
        return 'Postproduktion'
    if any(k in d for k in ['video', 'filming', 'dreh', 'kamera']):
        return 'Videoproduktion'
    if any(k in d for k in ['workshop', 'training', 'seminar']):
        return 'Workshop'
    return 'Sonstiges'

def _curate_rate(samples, fallback=0.0):
    cleaned = [float(s) for s in (samples or []) if float(s) > 0]
    if not cleaned:
        return float(fallback or 0.0)
    cleaned.sort()
    # Trim extremes when enough data points exist
    if len(cleaned) >= 5:
        trim = max(1, int(len(cleaned) * 0.1))
        cleaned = cleaned[trim:len(cleaned)-trim] or cleaned
    return round(float(statistics.median(cleaned)), 2)


def upsert_item_catalog(items, source='manual'):
    catalog = load_items_catalog()
    now = datetime.now().isoformat()
    for item in items or []:
        desc = str(item.get('description', '') or '').strip()
        if not desc:
            continue
        key = re.sub(r'\s+', ' ', desc.lower())
        rate = float(item.get('rate', 0) or 0)
        job_type = infer_job_type(desc)
        if key not in catalog:
            samples = [rate] if rate > 0 else []
            curated = _curate_rate(samples, fallback=rate)
            catalog[key] = {
                'description': desc,
                'job_type': job_type,
                'default_rate': rate,
                'curated_rate': curated,
                'rate_samples': samples,
                'use_count': 1,
                'sources': [source],
                'first_seen': now,
                'last_used': now
            }
        else:
            entry = catalog[key]
            entry['description'] = desc
            entry['job_type'] = job_type or entry.get('job_type', 'Sonstiges')
            if rate > 0:
                entry['default_rate'] = rate
                samples = entry.get('rate_samples', [])
                samples.append(rate)
                # Keep DB small and recent enough
                entry['rate_samples'] = samples[-40:]
            entry['curated_rate'] = _curate_rate(entry.get('rate_samples', []), fallback=entry.get('default_rate', 0))
            entry['use_count'] = entry.get('use_count', 0) + 1
            entry['last_used'] = now
            sources = set(entry.get('sources', []))
            sources.add(source)
            entry['sources'] = sorted(list(sources))
    save_items_catalog(catalog)

# Initialize AI assistant - it will now pick up the API key from environment
print(f"Initializing AI Assistant with key: {os.getenv('OPENAI_API_KEY')[:20]}..." if os.getenv('OPENAI_API_KEY') else "Initializing AI Assistant without key")
ai_assistant = AIInvoiceAssistant()

def recurate_existing_catalog():
    catalog = load_items_catalog()
    changed = 0
    for _, entry in catalog.items():
        samples = entry.get('rate_samples', [])
        if not samples and entry.get('default_rate', 0):
            samples = [entry.get('default_rate', 0)]
            entry['rate_samples'] = samples
        new_rate = _curate_rate(samples, fallback=entry.get('default_rate', 0))
        if float(entry.get('curated_rate', 0) or 0) != float(new_rate or 0):
            entry['curated_rate'] = new_rate
            changed += 1
    save_items_catalog(catalog)
    return {'entries': len(catalog), 'updated': changed}


def apply_catalog_rates(invoice_data):
    catalog = load_items_catalog()
    if not isinstance(invoice_data, dict):
        return invoice_data
    items = invoice_data.get('items', []) or []
    for item in items:
        desc = re.sub(r'\s+', ' ', str(item.get('description', '') or '').strip().lower())
        if not desc:
            continue
        match = None
        if desc in catalog:
            match = catalog.get(desc)
        else:
            # Fuzzy contains check for partial description matches
            for k, v in catalog.items():
                if desc in k or k in desc:
                    match = v
                    break
        if match:
            curated = float(match.get('curated_rate', 0) or match.get('default_rate', 0) or 0)
            if curated > 0:
                qty = float(item.get('quantity', 1) or 1)
                item['rate'] = curated
                item['amount'] = round(qty * curated, 2)
    invoice_data['items'] = items
    return invoice_data


def extract_and_index_example_invoice(filename):
    from extract_invoice_text import get_example_invoice_text
    text = get_example_invoice_text(filename, EXAMPLE_DIR)
    if not text:
        return {'indexed': False, 'reason': 'No text extracted'}

    extraction_prompt = (
        "Extract structured invoice info from this real invoice text. "
        "Return a JSON invoice object with client, items, type, date, invoice_number, notes. "
        "Use only information present in text. Keep line items concise."
    )

    structured = ai_assistant.generate_invoice_from_prompt(
        extraction_prompt,
        example_invoice=None,
        reference_files=[text[:18000]]
    )

    client = structured.get('client', {}) if isinstance(structured, dict) else {}
    items = structured.get('items', []) if isinstance(structured, dict) else []

    if client and client.get('name'):
        customer_db.add_or_update_customer(client, structured.get('invoice_number', filename))
    upsert_item_catalog(items, source=f'example:{filename}')

    return {
        'indexed': True,
        'customer': client.get('name', ''),
        'items_indexed': len(items)
    }

# Initialize invoice numbering system
from invoice_numbering import InvoiceNumbering
invoice_numbering = InvoiceNumbering(DATA_DIR)
print(f"📋 Invoice numbering initialized - Rechnung: {invoice_numbering.get_current_number('Rechnung')}, Angebot: {invoice_numbering.get_current_number('Angebot')}")

# Initialize Google Sheets integration (optional)
sheets_tracker = None
try:
    from google_sheets_integration import GoogleSheetsInvoiceTracker
    sheets_id = os.getenv('GOOGLE_SHEETS_ID')
    if sheets_id:
        sheets_tracker = GoogleSheetsInvoiceTracker(spreadsheet_id=sheets_id)
        print(f"✅ Google Sheets integration enabled: {sheets_id[:20]}...")
    else:
        print("⚠️  GOOGLE_SHEETS_ID not set - invoice numbering will be manual")
except ImportError as e:
    print(f"⚠️  Google Sheets integration not available: {e}")
except Exception as e:
    print(f"⚠️  Error initializing Google Sheets: {e}")

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'})

@app.route('/api/parse-examples', methods=['GET'])
def parse_examples():
    """Parse all example invoices and return extracted data"""
    try:
        examples = invoice_parser.parse_all_examples()
        return jsonify({'success': True, 'examples': examples})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/examples/<path:filename>', methods=['GET'])
def serve_example_pdf(filename):
    """Serve example PDF files"""
    try:
        return send_from_directory(EXAMPLE_DIR, filename)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 404

@app.route('/output/<path:filename>', methods=['GET'])
def serve_output_pdf(filename):
    """Serve generated invoice PDF files for preview"""
    try:
        file_path = os.path.join(OUTPUT_DIR, filename)
        return send_file(file_path, mimetype='application/pdf', as_attachment=False, download_name=filename)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 404

@app.route('/download/<path:filename>', methods=['GET'])
def download_output_pdf(filename):
    """Download generated invoice PDF files"""
    try:
        file_path = os.path.join(OUTPUT_DIR, filename)
        # Allow custom download name via query parameter
        custom_name = request.args.get('name', filename)
        # Ensure it ends with .pdf
        if not custom_name.endswith('.pdf'):
            custom_name = custom_name + '.pdf'
        return send_file(file_path, mimetype='application/pdf', as_attachment=True, download_name=custom_name)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 404

@app.route('/api/customers', methods=['GET'])
def get_customers():
    """Get customers from database (simplified by default)."""
    try:
        customers = customer_db.get_all_customers()
        raw = request.args.get('raw', '0') == '1'
        limit = int(request.args.get('limit', '60'))
        if not raw:
            customers = simplify_customers(customers)
        customers = customers[:max(1, min(limit, 300))]
        customers.sort(key=lambda c: (c.get('name', '') or '').lower())
        return jsonify({'success': True, 'customers': customers})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/customers/search', methods=['GET'])
def search_customers():
    """Search customers by name"""
    try:
        query = request.args.get('q', '')
        customers = customer_db.search_customers(query)
        customers = simplify_customers(customers)
        return jsonify({'success': True, 'customers': customers})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/customers/cleanup', methods=['POST'])
def cleanup_customers():
    """Persist a deduplicated customer list using normalization logic."""
    try:
        stats = persist_customer_cleanup()
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/catalog/items', methods=['GET'])
def get_catalog_items():
    try:
        q = request.args.get('q', '').lower().strip()
        raw = request.args.get('raw', '0') == '1'
        limit = int(request.args.get('limit', '120'))

        catalog = list(load_items_catalog().values())
        for row in catalog:
            if not row.get('curated_rate'):
                row['curated_rate'] = _curate_rate(row.get('rate_samples', []), fallback=row.get('default_rate', 0))

        if q:
            # For explicit searches: include all matching rows, then simplify mildly
            catalog = [i for i in catalog if q in i.get('description', '').lower() or q in i.get('job_type', '').lower()]
            if not raw:
                catalog = simplify_catalog_items(catalog, min_use_count=1)
        else:
            # Default browsing should be clean and focused
            if not raw:
                catalog = simplify_catalog_items(catalog, min_use_count=2)

        catalog = catalog[:max(1, min(limit, 500))]
        catalog.sort(key=lambda x: (x.get('description', '') or '').lower())
        return jsonify({'success': True, 'items': catalog})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/catalog/job-types', methods=['GET'])
def get_catalog_job_types():
    try:
        types = sorted({v.get('job_type', 'Sonstiges') for v in load_items_catalog().values()})
        return jsonify({'success': True, 'job_types': types})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/catalog/rebuild', methods=['POST'])
def rebuild_catalog_from_examples():
    try:
        results = []
        for filename in os.listdir(EXAMPLE_DIR):
            if filename.lower().endswith('.pdf'):
                try:
                    results.append({'file': filename, **extract_and_index_example_invoice(filename)})
                except Exception as ex:
                    results.append({'file': filename, 'indexed': False, 'reason': str(ex)})
        curation = recurate_existing_catalog()
        return jsonify({'success': True, 'results': results, 'curation': curation})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/catalog/curate', methods=['POST'])
def curate_catalog():
    try:
        return jsonify({'success': True, 'curation': recurate_existing_catalog()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/invoice/create', methods=['POST'])
def create_invoice():
    """Create a new invoice based on provided data"""
    try:
        data = request.json
        invoice_data = {
            'invoice_number': data.get('invoice_number', ''),
            'date': data.get('date', datetime.now().strftime('%d.%m.%Y')),
            'client': data.get('client', {}),
            'items': data.get('items', []),
            'notes': data.get('notes', ''),
            'type': data.get('type', 'Rechnung'),  # Rechnung or Angebot
            # Preserve all optional fields used by the PDF layout
            'zeitraum': data.get('zeitraum', ''),
            'expiry_date': data.get('expiry_date', ''),
            'due_date': data.get('due_date', ''),
            'project_name': data.get('project_name', ''),
            'project_description': data.get('project_description', ''),
            'signature_file': data.get('signature_file', ''),
            'signature_name': data.get('signature_name', 'Florian Manhardt')
        }
        
        # Save customer to database
        if invoice_data.get('client'):
            customer_db.add_or_update_customer(
                invoice_data['client'], 
                invoice_data.get('invoice_number')
            )

        # Keep items catalog curated from real generated invoices
        upsert_item_catalog(invoice_data.get('items', []), source='generated')
        
        # Generate invoice
        output_path = invoice_generator.generate(invoice_data)
        
        return jsonify({
            'success': True,
            'invoice_id': os.path.basename(output_path),
            'path': output_path
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/invoice/preview', methods=['POST'])
def preview_invoice():
    """Generate a preview of the invoice"""
    try:
        data = request.json
        preview_data = invoice_generator.generate_preview(data)
        return jsonify({'success': True, 'preview': preview_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/invoice/download/<invoice_id>', methods=['GET'])
def download_invoice(invoice_id):
    """Download a generated invoice PDF"""
    try:
        file_path = os.path.join(OUTPUT_DIR, invoice_id)
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'Invoice not found'}), 404
        
        return send_file(file_path, as_attachment=True, download_name=invoice_id)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/pdf/view/<path:filename>', methods=['GET'])
def view_pdf(filename):
    """Serve PDF for viewing (not downloading)"""
    try:
        # Check in example-invoices first
        file_path = os.path.join(EXAMPLE_DIR, filename)
        if not os.path.exists(file_path):
            # Try in output directory
            file_path = os.path.join(OUTPUT_DIR, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'PDF not found'}), 404
        
        return send_file(file_path, mimetype='application/pdf')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/invoices/list', methods=['GET'])
def list_invoices():
    """List all generated invoices"""
    try:
        invoices = []
        for filename in os.listdir(OUTPUT_DIR):
            if filename.endswith('.pdf'):
                file_path = os.path.join(OUTPUT_DIR, filename)
                invoices.append({
                    'id': filename,
                    'name': filename,
                    'created': datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
                    'size': os.path.getsize(file_path)
                })
        
        invoices.sort(key=lambda x: x['created'], reverse=True)
        return jsonify({'success': True, 'invoices': invoices})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai/generate-invoice', methods=['POST'])
def ai_generate_invoice():
    """Generate invoice data from prompt using AI"""
    try:
        data = request.json
        prompt = data.get('prompt', '')
        example_invoice = data.get('example_invoice')
        reference_files = data.get('reference_files', [])
        example_name = data.get('example_name')

        # Inject curated DB context (customers + item catalog) so AI uses real historical patterns
        customers = customer_db.get_all_customers()[:80]
        item_catalog = list(load_items_catalog().values())
        for row in item_catalog:
            row['curated_rate'] = row.get('curated_rate') or _curate_rate(row.get('rate_samples', []), fallback=row.get('default_rate', 0))
        item_catalog.sort(key=lambda x: x.get('use_count', 0), reverse=True)
        item_catalog = item_catalog[:200]

        db_context = {
            'instruction': (
                'Use this curated database as primary guidance for suggested line items and language. '
                'Prioritize matching job types/descriptions from this catalog over generic defaults. '
                'Use curated_rate as the preferred price reference (default_rate is secondary fallback). '
                'If prompt mentions baustelle/timelapse/construction, prefer timelapse-related entries when available.'
            ),
            'customers': customers,
            'items_catalog': item_catalog
        }
        reference_files = reference_files + [f"CURATED_DATABASE_CONTEXT:\n{json.dumps(db_context, ensure_ascii=False)}"]

        # If example name provided, extract text from the PDF
        if example_name:
            from extract_invoice_text import get_example_invoice_text
            example_text = get_example_invoice_text(example_name, EXAMPLE_DIR)
            if example_text:
                # Add the example invoice text to reference files
                reference_files = reference_files + [f"Example Invoice ({example_name}):\n{example_text}"]

        invoice_data = ai_assistant.generate_invoice_from_prompt(
            prompt,
            example_invoice,
            reference_files
        )

        # Enforce curated pricing from catalog after AI draft generation
        invoice_data = apply_catalog_rates(invoice_data)

        return jsonify({'success': True, 'invoice_data': invoice_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai/update-invoice', methods=['POST'])
def ai_update_invoice():
    """Update existing invoice based on prompt"""
    try:
        data = request.json
        current_invoice = data.get('current_invoice', {})
        update_prompt = data.get('prompt', '')
        
        updated_invoice = ai_assistant.update_invoice_from_prompt(
            current_invoice, 
            update_prompt
        )
        
        return jsonify({'success': True, 'invoice_data': updated_invoice})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/examples/list-all', methods=['GET'])
def list_all_examples():
    """List all example invoices (PDFs and parsed data)"""
    try:
        examples = []
        
        # List PDFs in example-invoices folder
        if os.path.exists(EXAMPLE_DIR):
            for filename in os.listdir(EXAMPLE_DIR):
                if filename.endswith('.pdf'):
                    file_path = os.path.join(EXAMPLE_DIR, filename)
                    examples.append({
                        'id': filename,
                        'name': filename.replace('.pdf', ''),
                        'path': file_path,
                        'type': 'example'
                    })
        
        # List generated invoices in output folder
        if os.path.exists(OUTPUT_DIR):
            for filename in os.listdir(OUTPUT_DIR):
                if filename.endswith('.pdf'):
                    file_path = os.path.join(OUTPUT_DIR, filename)
                    examples.append({
                        'id': filename,
                        'name': filename.replace('.pdf', ''),
                        'path': file_path,
                        'type': 'generated'
                    })
        
        examples.sort(key=lambda x: x['name'])
        return jsonify({'success': True, 'examples': examples})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/invoice/next-number', methods=['GET'])
def get_next_invoice_number():
    """Get the next invoice number (Rechnung or Angebot)"""
    try:
        doc_type = request.args.get('type', 'Rechnung')  # Rechnung or Angebot
        prefix = request.args.get('prefix', '')
        
        # Try Google Sheets first if configured
        if sheets_tracker:
            try:
                next_number = sheets_tracker.get_next_invoice_number(prefix)
                all_numbers = sheets_tracker.get_all_invoice_numbers()
                return jsonify({
                    'success': True,
                    'next_number': next_number,
                    'source': 'google_sheets',
                    'existing_count': len(all_numbers)
                })
            except Exception as e:
                print(f"Google Sheets error: {e}, falling back to local numbering")
        
        # Fall back to local numbering system
        next_number = invoice_numbering.get_next_number(doc_type, prefix)
        
        return jsonify({
            'success': True,
            'next_number': next_number,
            'source': 'local',
            'rechnung_count': invoice_numbering.get_current_number('Rechnung'),
            'angebot_count': invoice_numbering.get_current_number('Angebot')
        })
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': str(e),
            'next_number': ''
        }), 500

@app.route('/api/upload-reference', methods=['POST'])
def upload_reference():
    """Upload and process reference files"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Empty filename'}), 400
        
        # Save file temporarily and extract text
        # For now, just return the filename
        # TODO: Add text extraction for PDFs, Word docs, etc.
        
        return jsonify({
            'success': True, 
            'filename': file.filename,
            'content': f"Reference file: {file.filename}"
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/signatures/upload', methods=['POST'])
def upload_signature():
    """Upload a signature image"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Empty filename'}), 400
        
        # Validate file type (signature images only)
        allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            return jsonify({'success': False, 'error': 'Only image files are allowed (PNG, JPG, JPEG, GIF, WEBP)'}), 400
        
        # Save to signatures directory (safe + unique filename)
        desired_name = request.form.get('desired_name', '').strip()
        chosen_name = desired_name if desired_name else file.filename

        base_name = secure_filename(chosen_name)
        if not base_name:
            return jsonify({'success': False, 'error': 'Invalid filename'}), 400
        name_no_ext, ext = os.path.splitext(base_name)
        if not ext:
            ext = file_ext
        safe_filename = f"{name_no_ext}_{int(datetime.now().timestamp())}{ext}"
        file_path = os.path.join(SIGNATURES_DIR, safe_filename)
        file.save(file_path)

        # Persist human-friendly display name separately from physical filename
        meta = load_signatures_meta()
        display_name = (desired_name or name_no_ext).strip()
        if display_name.lower().endswith(ext.lower()):
            display_name = display_name[:-len(ext)]
        meta[safe_filename] = {
            'display_name': display_name or name_no_ext,
            'created_at': datetime.now().isoformat()
        }
        save_signatures_meta(meta)
        
        return jsonify({
            'success': True, 
            'filename': safe_filename,
            'display_name': meta[safe_filename]['display_name'],
            'path': file_path
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/signatures/list', methods=['GET'])
def list_signatures():
    """List all uploaded signatures"""
    try:
        signatures = []
        meta = load_signatures_meta()
        for filename in os.listdir(SIGNATURES_DIR):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                file_path = os.path.join(SIGNATURES_DIR, filename)
                display_name = (meta.get(filename) or {}).get('display_name')
                if not display_name:
                    display_name = os.path.splitext(filename)[0]
                signatures.append({
                    'filename': filename,
                    'display_name': display_name,
                    'path': file_path,
                    'uploaded': datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
                })
        
        signatures.sort(key=lambda x: x['uploaded'], reverse=True)
        return jsonify({'success': True, 'signatures': signatures})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/signatures/view/<filename>', methods=['GET'])
def view_signature(filename):
    """View a signature image"""
    try:
        file_path = os.path.join(SIGNATURES_DIR, filename)
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'Signature not found'}), 404
        
        return send_file(file_path)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/signatures/delete/<path:filename>', methods=['DELETE'])
def delete_signature(filename):
    """Delete a signature image from pool"""
    try:
        safe_name = os.path.basename(filename)
        file_path = os.path.join(SIGNATURES_DIR, safe_name)

        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'Signature not found'}), 404

        os.remove(file_path)
        meta = load_signatures_meta()
        if safe_name in meta:
            del meta[safe_name]
            save_signatures_meta(meta)
        return jsonify({'success': True, 'filename': safe_name})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/signatures/delete', methods=['POST'])
def delete_signature_post():
    """Delete signature by JSON body for frontend compatibility"""
    try:
        data = request.get_json(silent=True) or {}
        filename = data.get('filename', '')
        safe_name = os.path.basename(str(filename))
        if not safe_name:
            return jsonify({'success': False, 'error': 'Missing filename'}), 400

        file_path = os.path.join(SIGNATURES_DIR, safe_name)
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'Signature not found'}), 404

        os.remove(file_path)
        meta = load_signatures_meta()
        if safe_name in meta:
            del meta[safe_name]
            save_signatures_meta(meta)
        return jsonify({'success': True, 'filename': safe_name})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/upload-example', methods=['POST'])
def upload_example():
    """Upload a new example invoice"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Empty filename'}), 400
        
        if not file.filename.endswith('.pdf'):
            return jsonify({'success': False, 'error': 'Only PDF files are accepted'}), 400
        
        # Save to example-invoices directory
        file_path = os.path.join(EXAMPLE_DIR, file.filename)
        file.save(file_path)
        
        index_result = extract_and_index_example_invoice(file.filename)
        return jsonify({
            'success': True, 
            'filename': file.filename,
            'path': file_path,
            'index_result': index_result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Serve React frontend
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Serve the React frontend"""
    dist_dir = os.path.join(os.path.dirname(__file__), '../dist')
    
    if path and os.path.exists(os.path.join(dist_dir, path)):
        return send_from_directory(dist_dir, path)
    else:
        return send_from_directory(dist_dir, 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port)
