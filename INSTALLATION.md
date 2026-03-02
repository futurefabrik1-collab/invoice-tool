# Installation Guide

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+** (tested with Python 3.14)
- **Node.js 16+** (for the frontend)
- **Tesseract OCR** (optional, for parsing .pages files)

### Installing Tesseract (Optional)

If you want to parse `.pages` invoice files:

```bash
# macOS
brew install tesseract tesseract-lang

# Linux (Ubuntu/Debian)
sudo apt-get install tesseract-ocr tesseract-ocr-deu

# Check installation
tesseract --version
```

## Installation Steps

### 1. Navigate to the Project Directory

```bash
cd /Users/markburnett/DevPro/invoice-tool
```

### 2. Run Setup Script

The setup script will:
- Create a Python virtual environment
- Install all Python dependencies
- Install all Node.js dependencies

```bash
./setup.sh
```

This may take a few minutes to complete.

### 3. Verify Installation

Test that everything is working:

```bash
source venv/bin/activate
python test_invoice.py
```

You should see:
```
🎉 All tests passed!
```

## Running the Application

### Quick Start

Simply run:

```bash
./start.sh
```

This will:
1. Activate the Python virtual environment
2. Start the backend server on port 5001
3. Start the frontend dev server on port 3000
4. Open your browser to http://localhost:3000

### Manual Start

If you prefer to run the servers separately:

**Terminal 1 - Backend:**
```bash
cd /Users/markburnett/DevPro/invoice-tool
source venv/bin/activate
python backend/app.py
```

**Terminal 2 - Frontend:**
```bash
cd /Users/markburnett/DevPro/invoice-tool/frontend
npm run dev
```

Then open http://localhost:3000 in your browser.

## Troubleshooting

### Port Already in Use

If port 5001 or 3000 is already in use:

**Find and kill the process:**
```bash
# For port 5001 (backend)
lsof -ti:5001 | xargs kill -9

# For port 3000 (frontend)
lsof -ti:3000 | xargs kill -9
```

### Python Dependencies Won't Install

If you encounter issues installing Python dependencies:

```bash
# Remove the virtual environment
rm -rf venv

# Recreate it
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install dependencies one by one
pip install flask flask-cors
pip install reportlab PyPDF2 python-dateutil
pip install pillow pytesseract
```

### Frontend Dependencies Won't Install

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Tesseract Errors

If you see Tesseract errors when parsing invoices:

1. Install Tesseract with German language support:
   ```bash
   brew install tesseract tesseract-lang
   ```

2. Set the TESSDATA_PREFIX environment variable:
   ```bash
   export TESSDATA_PREFIX=/opt/homebrew/share/tessdata/
   ```

3. Add to your `~/.zshrc` or `~/.bashrc` to make it permanent:
   ```bash
   echo 'export TESSDATA_PREFIX=/opt/homebrew/share/tessdata/' >> ~/.zshrc
   ```

Note: OCR is only needed for parsing `.pages` files. PDF parsing works without Tesseract.

## Updating

To update the application after pulling new changes:

```bash
# Update Python dependencies
source venv/bin/activate
pip install -r requirements.txt

# Update frontend dependencies
cd frontend
npm install
```

## Uninstalling

To completely remove the application:

```bash
cd /Users/markburnett/DevPro
rm -rf invoice-tool
```

## Next Steps

Once installed, check out:
- [Quick Start Guide](QUICKSTART.md) - Get started in 3 steps
- [README](README.md) - Full documentation
- [Usage Guide](#) - Learn all the features

Enjoy using the Invoice Tool! 🎉
