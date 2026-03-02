# Invoice Tool - Future Fabrik

**AI-Powered Invoice Generator for Video Production Services**

Version: 2.0 (Cleaned & Consolidated - March 2, 2026)

---

## 🚀 Quick Start

```bash
cd /Users/markburnett/DevPro/invoice-tool
./start.sh
```

**Access the app:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:5001

---

## 📋 Features

### 1. Previous Rechnung (153 PDF Invoices)
- Searchable list of all historical invoices
- Click 👁️ to preview any invoice
- Click invoice name to load as template
- Real-time search filtering

### 2. Previous Customers (63 Customers)
- Live searchable customer database
- Shows invoice count and contact details
- Click to auto-fill customer data
- Extracted from historical invoices

### 3. Drag & Drop Zones (Full-Width Header)
- 📄 Example Invoice PDF - Add training data
- 📎 Reference Files - Upload supporting documents
- ✍️ Signature Image - Add signature to invoices

### 4. PDF Generation
- Manual invoice creation
- AI-assisted generation
- Auto-numbering (Rechnung/Angebot)
- PDF viewer with zoom & navigation
- Automatic customer database updates

### 5. Invoice Management
- Custom invoice numbering formats
- Client database with autocomplete
- Item management with descriptions
- Multiple signatures support
- Google Sheets integration (optional)

---

## 🛠 Installation

### Prerequisites
- Python 3.14+
- Node.js 18+
- npm or yarn

### Setup

1. **Backend Setup:**
```bash
cd /Users/markburnett/DevPro/invoice-tool
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Frontend Setup:**
```bash
cd frontend
npm install
```

3. **Environment Variables:**
Create `.env` file in root:
```
OPENAI_API_KEY=your_key_here
```

4. **Start Application:**
```bash
./start.sh
```

---

## 📁 Project Structure

```
invoice-tool/
├── backend/
│   ├── app.py                    # Main Flask API
│   ├── invoice_generator.py     # PDF generation
│   ├── invoice_parser.py        # Parse example invoices
│   ├── customer_db.py            # Customer management
│   ├── invoice_numbering.py     # Auto-numbering logic
│   └── ai_invoice_assistant.py  # AI integration
├── frontend/
│   ├── src/
│   │   ├── NewApp.jsx           # Main application (ACTIVE)
│   │   └── components/
│   │       ├── PDFViewer.jsx    # PDF viewing
│   │       └── ...
│   └── vite.config.js           # Dev server config
├── data/
│   ├── customers.json           # 63 customers
│   └── invoice_numbering.json   # Numbering state
├── example-invoices/            # 153 PDF training data
├── output/                      # Generated invoices
├── templates/                   # Invoice templates
│   └── logo.png
└── signatures/                  # Signature images
```

---

## 🔧 Configuration

### Invoice Numbering
Edit `data/invoice_numbering.json`:
```json
{
  "rechnung": {
    "format": "AFF{counter:06d}",
    "counter": 250999
  },
  "angebot": {
    "format": "AFF{counter:06d}",
    "counter": 250105
  }
}
```

### Customer Database
Located in `data/customers.json` - auto-updates when invoices are created.

### Backend Port
Port 5001 (changed from 5000 to avoid macOS AirPlay conflict)

---

## 🎯 Usage Guide

### Creating an Invoice

1. **Search Previous Customers:**
   - Type customer name in search box
   - Click customer to load their data

2. **Or Search Previous Invoices:**
   - Find similar invoice
   - Click to load as template

3. **Fill Invoice Details:**
   - Client information
   - Invoice items (description + amount)
   - Select signature

4. **Generate PDF:**
   - Click "📥 Generate PDF"
   - PDF opens automatically in viewer
   - Saved to `output/` directory

### Using Drag & Drop

**Example Invoice:**
- Drag PDF to first dropzone
- Adds to training data
- Becomes searchable in list

**Reference Files:**
- Drag any documents
- Attached to invoice context
- Used by AI assistant

**Signature:**
- Drag PNG/JPG image
- Added to signatures list
- Available for invoices

---

## 🔌 API Endpoints

### Examples
- `GET /api/parse-examples` - Get all 153 parsed invoices
- `GET /api/examples/<filename>` - Serve specific example PDF

### Customers
- `GET /api/customers` - Get all 63 customers
- `GET /api/customers/search?q=<query>` - Search customers

### Invoice Generation
- `POST /api/invoice/create` - Generate new invoice
- `GET /api/invoice/download/<id>` - Download invoice
- `GET /output/<filename>` - Serve generated PDF

### Health
- `GET /api/health` - Check backend status

---

## 🐛 Troubleshooting

### Port Issues
**Error:** "Address already in use: 5001"
```bash
lsof -ti:5001 | xargs kill -9
```

### Backend Won't Start
- Check Python dependencies: `pip install -r requirements.txt`
- Activate venv: `source venv/bin/activate`

### Frontend Shows Old Interface
- Hard refresh: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
- Clear cache: `rm -rf frontend/node_modules/.vite frontend/dist`

### PDFs Not Showing
- Check backend is running on port 5001
- Verify `example-invoices/` has PDF files
- Check browser console for errors

### Customer Dropdown Empty
- Verify `data/customers.json` exists
- Check `/api/customers` endpoint works
- Reload customers from backend

---

## 📊 Data

### Current Statistics
- **PDF Examples:** 153 invoices
- **Customers:** 63 in database
- **Generated Invoices:** Check `output/` directory
- **Signatures:** Check `signatures/` directory

### Backup
Automatic backup created before cleanup:
```bash
invoice-tool-backup-YYYYMMDD-HHMMSS.tar.gz
```

---

## 🔄 Recent Changes (March 2, 2026)

### Major Fixes
1. ✅ Port changed from 5000 to 5001 (macOS AirPlay conflict)
2. ✅ Example invoices list restored with search
3. ✅ Customer dropdown with live search
4. ✅ Drag & drop zones moved to full-width header
5. ✅ PDF generation access denied error fixed
6. ✅ Repository cleaned and consolidated

### Files Cleaned
- Removed duplicate documentation (22 → 1 main README)
- Removed non-PDF files from example-invoices
- Removed unused frontend components
- Consolidated all fixes into single document

---

## 📝 License & Credits

**Created for:** Future Fabrik  
**Purpose:** Video Production Invoice Management  
**Technology:** Python Flask + React + ReportLab + OpenAI

---

## 🆘 Support

For issues or questions, check:
1. This README
2. Browser console (F12) for errors
3. Backend logs in terminal
4. `data/` files for configuration

---

**Last Updated:** March 2, 2026  
**Status:** ✅ Fully Operational
