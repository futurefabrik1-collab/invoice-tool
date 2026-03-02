# Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Install Dependencies

```bash
cd /Users/markburnett/DevPro/invoice-tool
./setup.sh
```

This will install:
- Python packages (Flask, ReportLab, etc.)
- Node.js packages (React, Vite, etc.)

### Step 2: Run the Application

```bash
./start.sh
```

This starts both:
- Backend server on http://localhost:5001
- Frontend app on http://localhost:3000

### Step 3: Create Your First Invoice

1. Open http://localhost:3000 in your browser
2. Fill in the invoice form:
   - Invoice number (e.g., 552512)
   - Client details
   - Add line items
3. Click "Preview" to see how it looks
4. Click "Generate PDF" to download

## 📋 Example Data

Here's sample data you can use to test:

**Client:**
- Name: Klärwerk Leipzig GmbH
- Address: Augustusplatz 7
- City: 04109 Leipzig

**Line Item:**
- Description: 3D Visualisierung der 2D CAD Daten
- Quantity: 10
- Rate: 650.00

## 🎯 Features to Try

1. **Create Invoice** - Make a new Rechnung or Angebot
2. **Example Invoices** - Load data from your .pages files
3. **Generated Invoices** - View and download all created PDFs

## ⚡ Tips

- Use the "Preview" button before generating to check everything
- Line items calculate totals automatically
- Tax (19% MwSt) is added automatically
- All invoices are saved in the `output/` folder

## 🆘 Need Help?

**Backend not starting?**
```bash
cd /Users/markburnett/DevPro/invoice-tool
pip3 install -r requirements.txt
python3 backend/app.py
```

**Frontend not starting?**
```bash
cd /Users/markburnett/DevPro/invoice-tool/frontend
npm install
npm run dev
```

**Port already in use?**
- Backend uses port 5001
- Frontend uses port 3000
- Kill existing processes or change ports in config files

## 📁 Where Things Are

- **Generated PDFs:** `/Users/markburnett/DevPro/invoice-tool/output/`
- **Example Invoices:** `/Users/markburnett/DevPro/invoice-tool/example-invoices/`
- **Backend Code:** `/Users/markburnett/DevPro/invoice-tool/backend/`
- **Frontend Code:** `/Users/markburnett/DevPro/invoice-tool/frontend/src/`

Enjoy! 🎉
