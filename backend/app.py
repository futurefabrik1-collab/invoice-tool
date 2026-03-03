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

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SIGNATURES_DIR, exist_ok=True)

invoice_generator = InvoiceGenerator(TEMPLATES_DIR, OUTPUT_DIR)
invoice_parser = InvoiceParser(EXAMPLE_DIR)
customer_db = CustomerDatabase(CUSTOMER_DB_PATH)

# Initialize AI assistant - it will now pick up the API key from environment
print(f"Initializing AI Assistant with key: {os.getenv('OPENAI_API_KEY')[:20]}..." if os.getenv('OPENAI_API_KEY') else "Initializing AI Assistant without key")
ai_assistant = AIInvoiceAssistant()

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
    """Get all customers from database"""
    try:
        customers = customer_db.get_all_customers()
        return jsonify({'success': True, 'customers': customers})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/customers/search', methods=['GET'])
def search_customers():
    """Search customers by name"""
    try:
        query = request.args.get('q', '')
        customers = customer_db.search_customers(query)
        return jsonify({'success': True, 'customers': customers})
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
        base_name = secure_filename(file.filename)
        if not base_name:
            return jsonify({'success': False, 'error': 'Invalid filename'}), 400
        name_no_ext, ext = os.path.splitext(base_name)
        safe_filename = f"{name_no_ext}_{int(datetime.now().timestamp())}{ext}"
        file_path = os.path.join(SIGNATURES_DIR, safe_filename)
        file.save(file_path)
        
        return jsonify({
            'success': True, 
            'filename': safe_filename,
            'path': file_path
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/signatures/list', methods=['GET'])
def list_signatures():
    """List all uploaded signatures"""
    try:
        signatures = []
        for filename in os.listdir(SIGNATURES_DIR):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                file_path = os.path.join(SIGNATURES_DIR, filename)
                signatures.append({
                    'filename': filename,
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
        
        return jsonify({
            'success': True, 
            'filename': file.filename,
            'path': file_path
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
