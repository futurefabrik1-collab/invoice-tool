# Railway Deployment Guide

Deploy your Invoice Tool to Railway.app for production use.

---

## 🚀 Quick Deploy

### Prerequisites
- Railway account (https://railway.app)
- GitHub account (recommended) or Railway CLI
- OpenAI API key (for AI features)

---

## 📋 Deployment Steps

### Option 1: Deploy from GitHub (Recommended)

1. **Push to GitHub:**
   ```bash
   cd /Users/markburnett/DevPro/invoice-tool
   git init
   git add .
   git commit -m "Initial commit - Ready for Railway deployment"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/invoice-tool.git
   git push -u origin main
   ```

2. **Deploy on Railway:**
   - Go to https://railway.app
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `invoice-tool` repository
   - Railway will auto-detect the configuration

3. **Set Environment Variables:**
   In Railway dashboard, add these variables:
   ```
   OPENAI_API_KEY=sk-proj-your-key-here
   FLASK_ENV=production
   PORT=5001
   ```

4. **Deploy:**
   - Railway will automatically build and deploy
   - You'll get a URL like: `https://invoice-tool-production.up.railway.app`

---

### Option 2: Deploy with Railway CLI

1. **Install Railway CLI:**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login:**
   ```bash
   railway login
   ```

3. **Initialize Project:**
   ```bash
   cd /Users/markburnett/DevPro/invoice-tool
   railway init
   ```

4. **Set Environment Variables:**
   ```bash
   railway variables set OPENAI_API_KEY=sk-proj-your-key-here
   railway variables set FLASK_ENV=production
   ```

5. **Deploy:**
   ```bash
   railway up
   ```

---

## 🔧 Configuration Files

Railway uses these files (already created):

### `Procfile`
Tells Railway how to start the app:
```
web: gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 backend.app:app
```

### `railway.json`
Railway-specific configuration:
- Build commands
- Start commands
- Restart policies

### `nixpacks.toml`
Build environment configuration:
- Python 3.11
- Node.js 18
- Tesseract OCR
- Build steps

### `requirements.txt`
Python dependencies including:
- Flask & Flask-CORS
- ReportLab (PDF generation)
- OpenAI
- Gunicorn (production server)
- Pytesseract
- PyPDF2

---

## 🌍 Environment Variables

Required variables for Railway:

| Variable | Value | Description |
|----------|-------|-------------|
| `OPENAI_API_KEY` | `sk-proj-...` | Your OpenAI API key (required for AI features) |
| `FLASK_ENV` | `production` | Sets Flask to production mode |
| `PORT` | Auto-set by Railway | Web server port |

Optional variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `GOOGLE_SHEETS_ID` | Your sheet ID | For Google Sheets integration |
| `GOOGLE_CREDENTIALS` | JSON credentials | Google service account |

---

## 📁 What Gets Deployed

### Backend (Python/Flask)
- API endpoints on `/api/*`
- PDF generation
- Customer management
- Invoice numbering
- Serves built frontend

### Frontend (React/Vite)
- Built to static files in `frontend/dist/`
- Served by Flask backend
- All features included

### Data Persistence
⚠️ **Important:** Railway uses ephemeral storage. Data in these directories will reset on restart:
- `data/` (customers.json, invoice_numbering.json)
- `output/` (generated invoices)
- `example-invoices/` (training data)

**Solutions:**
1. Use Railway's Volume storage
2. Use external database (PostgreSQL)
3. Use cloud storage (S3, Google Cloud Storage)

---

## 🔒 Production Considerations

### 1. Add Volume Storage

In Railway dashboard:
- Add a Volume
- Mount to `/app/data`
- This persists customer and numbering data

### 2. Database Migration (Recommended)

Replace JSON files with PostgreSQL:
```bash
railway add postgresql
```

Update `customer_db.py` to use database instead of JSON.

### 3. File Storage

For generated invoices and examples:
- Use Railway Volume for small scale
- Use S3/GCS for production scale

### 4. Security

Add these to `.env` (never commit):
```
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-api-key
```

Update `.gitignore`:
```
.env
data/customers.json
data/invoice_numbering.json
output/*.pdf
```

---

## 🧪 Testing Deployment

After deployment:

1. **Check Health:**
   ```bash
   curl https://your-app.railway.app/api/health
   ```

2. **Test Examples API:**
   ```bash
   curl https://your-app.railway.app/api/parse-examples
   ```

3. **Test Frontend:**
   Open `https://your-app.railway.app` in browser

4. **Test Invoice Generation:**
   - Fill out form
   - Click "Generate PDF"
   - Should work without errors

---

## 📊 Monitoring

Railway provides:
- **Logs:** View in Railway dashboard
- **Metrics:** CPU, Memory, Network
- **Deployments:** Track versions
- **Crash Detection:** Auto-restart on failure

---

## 🐛 Troubleshooting

### Build Fails

**Error:** "No module named 'reportlab'"
- Check `requirements.txt` is in root
- Verify Python version in `nixpacks.toml`

**Error:** "npm: command not found"
- Ensure Node.js is in `nixpacks.toml`

### Runtime Errors

**Error:** "Address already in use"
- Railway sets `$PORT` automatically
- Don't hardcode port 5001

**Error:** "OPENAI_API_KEY not set"
- Add environment variable in Railway dashboard

### Data Loss

**Problem:** Customers/invoices disappear on restart
- Add Railway Volume storage
- Or migrate to PostgreSQL

### CORS Errors

**Problem:** Frontend can't reach backend
- CORS is already configured
- Check Railway URL is correct
- Verify both frontend and backend deployed

---

## 💰 Cost Estimate

Railway pricing (as of 2026):

- **Hobby Plan:** $5/month
  - 500 hours execution time
  - 8GB RAM
  - 8GB Disk
  - Perfect for this app

- **Pro Plan:** $20/month
  - Unlimited execution
  - More resources
  - Priority support

**Estimated usage for this app:**
- ~$5-10/month depending on usage
- OpenAI API costs separate

---

## 🔄 Updates and Redeploy

### Automatic Deploys (GitHub)
- Push to `main` branch
- Railway auto-deploys

### Manual Deploy (CLI)
```bash
railway up
```

### Rollback
```bash
railway rollback
```

---

## 📚 Additional Resources

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- This Project README: See `README.md`

---

## ✅ Deployment Checklist

Before deploying:
- [ ] Push code to GitHub
- [ ] Create Railway account
- [ ] Get OpenAI API key
- [ ] Review environment variables
- [ ] Test locally first
- [ ] Configure volume storage (optional)
- [ ] Set up database (optional)

After deploying:
- [ ] Test health endpoint
- [ ] Test frontend loads
- [ ] Test PDF generation
- [ ] Test customer search
- [ ] Test invoice search
- [ ] Verify PDF viewer works
- [ ] Check logs for errors

---

**Status:** ✅ Ready for Railway Deployment  
**Estimated Deploy Time:** 5-10 minutes  
**Difficulty:** Easy (Railway auto-detects everything)

