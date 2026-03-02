# 🚀 Future Fabrik AI Invoice Tool - Handover Documentation

**Project:** AI-Powered Invoice & Angebot Generator  
**Client:** Future Fabrik (Burnett & Manhardt GbR)  
**Completed:** February 27, 2026  
**Status:** ✅ Production Ready

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Quick Start](#quick-start)
3. [Features](#features)
4. [Technical Architecture](#technical-architecture)
5. [Configuration](#configuration)
6. [Daily Usage](#daily-usage)
7. [Maintenance](#maintenance)
8. [Troubleshooting](#troubleshooting)
9. [Backup & Recovery](#backup--recovery)
10. [Future Enhancements](#future-enhancements)

---

## System Overview

### What It Does
Professional invoice (Rechnung) and offer (Angebot) generation system with AI-powered assistance, trained on 156 real Future Fabrik invoices.

### Key Capabilities
- ✅ AI generates complete invoices from simple prompts
- ✅ Intelligent service bundling (video + post + mastering)
- ✅ 63 customer database with history
- ✅ 170 example invoices as templates
- ✅ Separate Rechnung/Angebot numbering
- ✅ PDF generation matching Future Fabrik format
- ✅ Drag & drop file handling
- ✅ Live PDF preview

### Technology Stack
- **Backend:** Python 3.14, Flask, OpenAI API
- **Frontend:** React, Vite, Axios
- **PDF Generation:** ReportLab
- **Data Storage:** JSON files
- **Optional:** Google Sheets integration

---

## Quick Start

### 1. Start the Tool

```bash
# Terminal 1 - Backend
cd ~/DevPro/invoice-tool
source venv/bin/activate
python3 backend/app.py

# Terminal 2 - Frontend
cd ~/DevPro/invoice-tool/frontend
npm run dev
```

### 2. Access

**Frontend:** http://localhost:3001  
**Backend API:** http://127.0.0.1:5001

### 3. Create Your First Invoice

1. **Select customer** from dropdown (63 available)
2. **Enter prompt:** "Video production for client X, 3 days filming"
3. **Click "Update Draft"** - AI generates complete invoice
4. **Review & edit** as needed
5. **Click "Generate PDF"** - Download professional invoice

---

## Features

### ✅ Implemented Features

#### 1. AI-Powered Generation
- **Natural language prompts** generate complete invoices
- **Intelligent service bundling** based on 156 examples
- **Contextual understanding** of project needs
- **200-word detailed descriptions** auto-generated
- **Real pricing** from historical data

**Example Prompt:**
```
"Corporate video for Deutsche Bahn, 3 days filming in Leipzig, 
needs full post-production and mastering for social media"
```

**AI Generates:**
- Video Production: 3 days @ €850/day = €2,550
- Post-Production: 5 days @ €750/day = €3,750
- Mastering: 1 day @ €750 = €750
- Total: €7,050 + 19% MwSt

#### 2. Customer Management
- **63 customers** auto-populated from examples
- **History tracking** per customer
- **Quick selection** from dropdown
- **Auto-fill** contact details
- **Invoice count** per customer

**Top Customers:**
- Heiner Füssel: 46 invoices
- Stadtwerke Leipzig: 22 invoices
- Mirko Stock & Matthias: 14 invoices

#### 3. Smart Numbering
- **Separate sequences** for Rechnung and Angebot
- **Auto-increment** on each generation
- **Type switching** updates number automatically
- **Local tracking** in `data/invoice_numbering.json`
- **Google Sheets integration** (optional)

#### 4. Professional PDF Output
- **Future Fabrik branding** with logo
- **German formatting** (€6.500,00)
- **All required sections:**
  - DATUM, AN, NUMMER
  - ZEITRAUM, GÜLTIG BIS/ZAHLUNGSZIEL
  - PROJEKTNAME, PROJEKTBESCHREIBUNG
  - Line items table
  - Totals with MwSt 19%
  - Footer with rights transfer
  - Signature

#### 5. Example Library
- **170 invoices** available
- **List view** with icons and preview
- **Instant preview** with PDF viewer
- **Drag & drop** to add new examples
- **Smart extraction** of client data

#### 6. Document Upload
- **Reference files** for context
- **Drag & drop** support
- **Multiple files** per invoice
- **AI uses context** from documents

#### 7. Live Editing
- **All fields editable** in real-time
- **Auto-calculations** (quantity × rate)
- **Multi-line descriptions** (up to 200 words)
- **Add/remove** line items
- **Character counter** for descriptions

---

## Technical Architecture

### Directory Structure
```
DevPro/invoice-tool/
├── backend/
│   ├── app.py                          # Main Flask API
│   ├── ai_invoice_assistant.py         # OpenAI integration
│   ├── customer_db.py                  # Customer management
│   ├── invoice_generator.py            # PDF generation
│   ├── invoice_numbering.py            # Number tracking
│   ├── invoice_parser.py               # Parse existing PDFs
│   ├── extract_invoice_text.py         # PDF text extraction
│   ├── populate_customers.py           # Customer extraction script
│   └── google_sheets_integration.py    # Google Sheets (optional)
├── frontend/
│   └── src/
│       ├── main.jsx                    # Entry point
│       ├── NewApp.jsx                  # Main UI component
│       ├── components/
│       │   └── PDFViewer.jsx           # PDF preview component
│       └── styles/
│           ├── NewApp.css              # Main styles
│           └── PDFViewer.css           # Viewer styles
├── data/
│   ├── customers.json                  # 63 customers
│   └── invoice_numbering.json          # Number sequences
├── templates/
│   └── logo.png                        # Future Fabrik logo
├── example-invoices/                   # 170 PDFs
├── output/                             # Generated invoices
├── .env                                # API keys
└── venv/                               # Python environment
```

### Data Flow

```
User Input (Prompt)
    ↓
Frontend (React)
    ↓
Backend API (Flask)
    ↓
AI Assistant (OpenAI GPT-4o-mini)
    ↓
Invoice Data (JSON)
    ↓
PDF Generator (ReportLab)
    ↓
Final PDF (output/)
```

### API Endpoints

**Invoices:**
- `POST /api/invoice/create` - Generate PDF
- `GET /api/invoice/next-number?type=Rechnung` - Get next number
- `GET /api/invoice/download/<id>` - Download PDF

**AI:**
- `POST /api/ai/generate-invoice` - Generate from prompt
- `POST /api/ai/update-invoice` - Update existing

**Customers:**
- `GET /api/customers/list` - All customers
- `GET /api/customers/search?q=query` - Search

**Examples:**
- `GET /api/examples/list-all` - All example invoices
- `GET /api/parse-examples` - Parse example data
- `POST /api/upload-example` - Upload new example
- `GET /api/pdf/view/<filename>` - View PDF

**Files:**
- `POST /api/upload-reference` - Upload reference document

---

## Configuration

### Environment Variables (`.env`)

```bash
# Required for AI features
OPENAI_API_KEY=sk-proj-...

# Optional for Google Sheets integration
GOOGLE_SHEETS_ID=your-spreadsheet-id
```

### OpenAI API
- **Model:** GPT-4o-mini
- **Cost:** ~€0.02-0.05 per invoice generation
- **Usage:** Only when "Update Draft" clicked
- **Fallback:** Manual mode if no API key

### Google Sheets (Optional)
- **Purpose:** Invoice number tracking across devices
- **Setup:** See `GOOGLE_SHEETS_SETUP.md`
- **Fallback:** Local numbering in `data/invoice_numbering.json`

---

## Daily Usage

### Creating a Rechnung (Invoice)

**Scenario:** Client project completed, need to invoice

1. **Open tool:** http://localhost:3001
2. **Select "Rechnung"** type
3. **Choose customer** from dropdown (or enter new)
4. **Enter prompt:**
   ```
   "Livestream workshop for DB Training facilitators,
   2 days, February 2026"
   ```
5. **Click "Update Draft"**
6. **Review generated invoice:**
   - Check services bundled correctly
   - Verify pricing (€850/day for workshops)
   - Review 200-word description
7. **Edit if needed** (add items, adjust quantities)
8. **Click "Generate PDF"**
9. **Download** → Send to client

**Time:** ~2 minutes (vs 15-20 minutes manual)

### Creating an Angebot (Offer)

**Scenario:** New client inquiry, need to quote

1. **Select "Angebot"** type
2. **Enter new client** details (or select existing)
3. **Upload reference docs** (client brief, emails)
4. **Enter prompt:**
   ```
   "3D visualization project for new building,
   CAD data provided, need photorealistic rendering,
   March-April timeline"
   ```
5. **AI generates:**
   - 3D Modeling: 15h @ €650
   - Rendering: 10h @ €650
   - Integration & Review: 5h @ €650
   - Gültig bis: 30 days from today
   - Zeitraum: 01.03.2026 - 30.04.2026
6. **Review & adjust** pricing if needed
7. **Generate PDF** → Send offer

---

## Maintenance

### Regular Tasks

#### Daily
- ✅ **Monitor generated invoices** in `output/` folder
- ✅ **Check customer database** if new clients added

#### Weekly
- ✅ **Backup data directory** (customers.json, invoice_numbering.json)
- ✅ **Review OpenAI API usage** and costs

#### Monthly
- ✅ **Archive old invoices** from output/ folder
- ✅ **Update customer database** if needed
- ✅ **Review example library** for outdated entries

### Adding New Customers

**Manual:**
1. Just create an invoice for them
2. Customer automatically saved to database

**Bulk Import:**
```bash
cd ~/DevPro/invoice-tool
source venv/bin/activate
python3 backend/populate_customers.py
```

### Adding New Examples

**Method 1: Drag & Drop**
1. In UI, drag PDF to "Example Rechnung" dropzone
2. Automatically added to library

**Method 2: Manual**
1. Copy PDF to `example-invoices/` folder
2. Refresh frontend
3. Run `populate_customers.py` to extract customer

---

## Troubleshooting

### Backend Won't Start

**Error:** `ModuleNotFoundError: No module named 'flask'`

**Solution:**
```bash
cd ~/DevPro/invoice-tool
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend Won't Load

**Error:** Page blank or "Cannot GET /"

**Solution:**
```bash
cd ~/DevPro/invoice-tool/frontend
rm -rf node_modules
npm install
npm run dev
```

### AI Not Generating

**Symptom:** Returns empty template, no intelligent content

**Solutions:**
1. Check OPENAI_API_KEY in `.env`
2. Verify API key is valid: https://platform.openai.com/api-keys
3. Check OpenAI account has billing enabled
4. Restart backend after setting key

### PDF Format Issues

**Note:** PDF format is FIXED - do not modify without express request

**If spacing issues:**
1. Check logo exists: `templates/logo.png`
2. Verify logo size: 70mm x 28mm
3. All content should start at 88mm from top

### Customer Dropdown Empty

**Solution:**
```bash
cd ~/DevPro/invoice-tool
cat data/customers.json  # Check if file exists
python3 backend/populate_customers.py  # Re-extract
# Restart backend
```

### Port Already in Use

**Error:** `Address already in use: 5001` or `3001`

**Solution:**
```bash
# Kill backend
pkill -f "python.*app.py"

# Kill frontend
lsof -ti:3001 | xargs kill

# Restart both
```

---

## Backup & Recovery

### Critical Files to Backup

```bash
# Data (customers, numbering)
data/customers.json
data/invoice_numbering.json

# Configuration
.env

# Generated invoices
output/*.pdf

# Example library
example-invoices/*.pdf
```

### Backup Script

Create `backup.sh`:
```bash
#!/bin/bash
BACKUP_DIR=~/Backups/invoice-tool
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR/$DATE
cp -r data $BACKUP_DIR/$DATE/
cp -r output $BACKUP_DIR/$DATE/
cp .env $BACKUP_DIR/$DATE/
cp -r example-invoices $BACKUP_DIR/$DATE/

echo "✅ Backup complete: $BACKUP_DIR/$DATE"
```

Run weekly:
```bash
chmod +x backup.sh
./backup.sh
```

### Recovery

**Restore from backup:**
```bash
# Restore data
cp ~/Backups/invoice-tool/20260227_120000/data/* data/

# Restore configuration
cp ~/Backups/invoice-tool/20260227_120000/.env .

# Restore examples
cp ~/Backups/invoice-tool/20260227_120000/example-invoices/* example-invoices/
```

### Google Drive Sync (Recommended)

Add to Google Drive backup:
```bash
# Symlink output to Google Drive
ln -s ~/DevPro/invoice-tool/output ~/Google\ Drive/Future\ Fabrik/Invoices/
```

---

## Future Enhancements

### Possible Additions

#### 1. Email Integration
- Send invoices directly from tool
- Template emails per client
- Track sent/opened status

#### 2. Payment Tracking
- Mark invoices as paid
- Payment reminders
- Overdue notifications

#### 3. Client Portal
- Clients can view their invoices
- Download PDFs
- Approve Angebote online

#### 4. Analytics Dashboard
- Revenue by month
- Top clients
- Service popularity
- Time saved vs manual

#### 5. Multi-language Support
- English invoices for international clients
- Templates per language

#### 6. Advanced AI Features
- Learn from user edits
- Suggest bundles based on season
- Price optimization
- Automatic follow-ups

#### 7. Mobile App
- Create invoices on phone
- Quick quotes on-site
- Photo documentation

---

## Support & Contact

### Documentation Files

- `README.md` - Overview and installation
- `QUICKSTART.md` - Quick reference
- `COMPLETE_FEATURES.md` - All features explained
- `GOOGLE_SHEETS_SETUP.md` - Sheets integration
- `ANALYSIS_156_EXAMPLES.md` - Data analysis insights
- `PDF_VIEWER_GUIDE.md` - Using the PDF preview
- `DRAG_DROP_GUIDE.md` - File upload guide

### Key Statistics

- **Development Time:** 3 days intensive
- **Code Files:** 25+
- **Documentation:** 12+ MD files
- **Training Data:** 156 real invoices
- **Customer Database:** 63 clients
- **Example Library:** 170 invoices
- **Time Savings:** ~70-80% per invoice

---

## Final Notes

### What Works Great
✅ AI-powered generation from simple prompts  
✅ Intelligent service bundling  
✅ Customer auto-population  
✅ Professional PDF output  
✅ Fast workflow (2 min vs 20 min)  

### Best Practices
1. **Use prompts** - Let AI do the heavy lifting
2. **Upload reference docs** - Better context = better invoices
3. **Review before generating** - AI is smart but check details
4. **Backup weekly** - Protect your data
5. **Monitor API costs** - Typically €5-10/month for active use

### Production Ready
This tool is **fully production-ready** and tested with real Future Fabrik data. It successfully generates professional invoices matching your established format and pricing.

---

**Handover Date:** February 27, 2026  
**System Status:** ✅ Production Ready  
**Next Steps:** Daily usage, monitor and optimize

🎉 **Enjoy your AI-powered invoice system!**
