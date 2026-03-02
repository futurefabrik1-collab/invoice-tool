# 📊 Google Sheets Integration Setup

## Overview

The invoice tool can now automatically assign the correct invoice number by reading your existing invoices from a Google Sheets spreadsheet.

## 📋 Setup Steps

### 1. Prepare Your Google Sheet

Create or use an existing Google Sheet with your invoices. Format should be:

| Invoice Number | Date | Client | Amount |
|----------------|------|--------|--------|
| 552512 | 2025-01-15 | Client A | 6500 |
| 552513 | 2025-01-20 | Client B | 3200 |
| 552514 | 2025-02-01 | Client C | 8900 |

**Important:**
- First column must contain invoice numbers
- First row is treated as header (will be skipped)
- Other columns are optional

### 2. Get Google Sheets API Credentials

1. **Go to Google Cloud Console:**
   - Visit: https://console.cloud.google.com/

2. **Create a New Project:**
   - Click "Select a project" → "New Project"
   - Name it: "Invoice Tool"
   - Click "Create"

3. **Enable Google Sheets API:**
   - Go to: APIs & Services → Library
   - Search for "Google Sheets API"
   - Click "Enable"

4. **Create Credentials:**
   - Go to: APIs & Services → Credentials
   - Click "Create Credentials" → "OAuth client ID"
   - If prompted, configure OAuth consent screen:
     - User Type: External
     - App name: Invoice Tool
     - User support email: your email
     - Developer contact: your email
     - Click "Save and Continue" through all steps
   - Back to Create Credentials:
     - Application type: "Desktop app"
     - Name: "Invoice Tool Desktop"
     - Click "Create"

5. **Download Credentials:**
   - Click the download icon next to your OAuth client
   - Save as `credentials.json`
   - Move it to: `DevPro/invoice-tool/backend/credentials.json`

### 3. Get Your Spreadsheet ID

1. Open your Google Sheet
2. Look at the URL:
   ```
   https://docs.google.com/spreadsheets/d/1abc123XYZ.../edit
                                      ^^^^^^^^^
                                   This is your ID
   ```
3. Copy the long string between `/d/` and `/edit`

### 4. Configure the Tool

Add to your `.env` file:

```bash
cd ~/DevPro/invoice-tool
echo "GOOGLE_SHEETS_ID=your-spreadsheet-id-here" >> .env
```

Example:
```
GOOGLE_SHEETS_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
```

### 5. First-Time Authentication

When you first use the feature:
1. A browser window will open
2. Sign in with your Google account
3. Click "Allow" to grant access
4. A token will be saved for future use

## 🎯 How It Works

### Automatic Invoice Numbering

When creating a new invoice:
1. Tool reads all invoice numbers from your Google Sheet
2. Finds the highest number
3. Increments by 1
4. Auto-fills the invoice number field

**Example:**
- Existing invoices: 552512, 552513, 552514
- Next invoice: **552515** (auto-assigned!)

### Smart Number Detection

The tool handles various formats:
- `552512` → next: `552513`
- `2025-001` → next: `2025-002`
- `INV-0045` → next: `INV-0046`

## 📝 Usage

### Via API:

```bash
curl http://127.0.0.1:5001/api/invoice/next-number
```

Returns:
```json
{
  "success": true,
  "next_number": "552515",
  "existing_count": 42
}
```

### In the UI:

When you open the invoice tool, the invoice number field will:
1. Show a "🔄" loading indicator
2. Automatically fetch the next number
3. Pre-fill the field

## 🔧 Troubleshooting

### "credentials.json not found"
- Download from Google Cloud Console
- Place in: `DevPro/invoice-tool/backend/credentials.json`

### "GOOGLE_SHEETS_ID not set"
- Add to `.env` file
- Restart backend

### "Permission denied" / "Access not configured"
- Make sure you enabled Google Sheets API
- Check OAuth consent screen is configured
- Re-download credentials if needed

### "No data found"
- Check your spreadsheet has data
- Verify the sheet name (default is "Sheet1")
- Check range in code if using different columns

## 🎨 Advanced Configuration

### Custom Range

If your data is in a different location:

```python
# In backend/app.py, change:
sheets_tracker = GoogleSheetsInvoiceTracker(
    spreadsheet_id=SHEETS_ID,
    range_name='Invoices!A2:D'  # Custom sheet and range
)
```

### Different Column Layout

If invoice numbers are NOT in column A:

```python
# Modify google_sheets_integration.py
# Update the column index in get_all_invoice_numbers()
```

## 📂 Files Created

After setup:
```
DevPro/invoice-tool/backend/
├── credentials.json     # Your OAuth credentials (from Google)
├── token.pickle        # Auto-generated after first auth
└── google_sheets_integration.py
```

**⚠️ Important:** 
- Add `credentials.json` and `token.pickle` to `.gitignore`
- Never commit these files to git
- Keep them secure

## ✅ Test It

```bash
cd ~/DevPro/invoice-tool
source venv/bin/activate
python3 -c "
from backend.google_sheets_integration import GoogleSheetsInvoiceTracker
tracker = GoogleSheetsInvoiceTracker()
tracker.authenticate()
numbers = tracker.get_all_invoice_numbers()
print(f'Found {len(numbers)} invoices')
print(f'Next number: {tracker.get_next_invoice_number()}')
"
```

You should see your invoice count and next number!

## 🔐 Security Notes

- Credentials file contains sensitive data
- Token file contains access tokens
- Both should be in `.gitignore`
- Spreadsheet must be accessible by your Google account
- You can revoke access anytime at: https://myaccount.google.com/permissions

Ready to set it up? Start with step 1! 🚀
