# DigitalOcean Deployment Guide

Deploy your Invoice Tool to DigitalOcean using App Platform or Droplets.

---

## 🚀 Deployment Options

### Option 1: App Platform (Recommended - PaaS)
- **Easiest:** Similar to Railway/Heroku
- **Auto-scaling:** Handles traffic automatically
- **Managed:** No server management
- **Cost:** Starting at $5/month

### Option 2: Droplet (VPS)
- **Full Control:** Your own virtual server
- **Customizable:** Install anything you need
- **Cost:** Starting at $4/month
- **Requires:** More setup and maintenance

---

## 📋 Option 1: App Platform Deployment

### Prerequisites
- DigitalOcean account (https://digitalocean.com)
- GitHub account
- OpenAI API key

### Step-by-Step Guide

#### 1. Push to GitHub

```bash
cd /Users/markburnett/DevPro/invoice-tool
git init
git add .
git commit -m "Ready for DigitalOcean deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/invoice-tool.git
git push -u origin main
```

#### 2. Create App on DigitalOcean

**Method A: Using Web Console**

1. Go to https://cloud.digitalocean.com/apps
2. Click **"Create App"**
3. Select **"GitHub"** as source
4. Authorize DigitalOcean to access your GitHub
5. Select your `invoice-tool` repository
6. Select `main` branch
7. Click **"Next"**

**Method B: Using CLI (doctl)**

```bash
# Install doctl
brew install doctl  # macOS
# or download from https://docs.digitalocean.com/reference/doctl/

# Authenticate
doctl auth init

# Deploy
cd /Users/markburnett/DevPro/invoice-tool
doctl apps create --spec .do/app.yaml
```

#### 3. Configure App Settings

DigitalOcean will auto-detect Python, but verify:

- **Environment:** Python
- **Build Command:** 
  ```bash
  pip install -r requirements.txt && cd frontend && npm install && npm run build
  ```
- **Run Command:**
  ```bash
  gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 backend.app:app
  ```
- **HTTP Port:** 8080

#### 4. Set Environment Variables

In App Platform console → Settings → Environment Variables:

```
OPENAI_API_KEY=sk-proj-your-actual-key-here
FLASK_ENV=production
PORT=8080
```

#### 5. Deploy!

- Click **"Create Resources"**
- DigitalOcean builds and deploys your app
- You'll get a URL like: `https://invoice-tool-xxxxx.ondigitalocean.app`

---

## 🐳 Option 2: Droplet Deployment (VPS)

### A. Create Droplet

1. **Create Droplet:**
   - Go to https://cloud.digitalocean.com/droplets/new
   - Choose **Ubuntu 22.04 LTS**
   - Select **Basic** plan ($4-6/month)
   - Choose region (Frankfurt recommended)
   - Add SSH key
   - Click **Create Droplet**

### B. Connect to Droplet

```bash
ssh root@your_droplet_ip
```

### C. Install Dependencies

```bash
# Update system
apt update && apt upgrade -y

# Install Python 3.11
apt install -y python3.11 python3.11-venv python3-pip

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Install Nginx
apt install -y nginx

# Install Tesseract OCR
apt install -y tesseract-ocr tesseract-ocr-deu libtesseract-dev

# Install Git
apt install -y git
```

### D. Deploy Application

```bash
# Clone repository
cd /var/www
git clone https://github.com/YOUR_USERNAME/invoice-tool.git
cd invoice-tool

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Build frontend
cd frontend
npm install
npm run build
cd ..

# Create .env file
nano .env
```

Add to `.env`:
```
OPENAI_API_KEY=sk-proj-your-key
FLASK_ENV=production
PORT=8080
```

### E. Set Up Systemd Service

```bash
nano /etc/systemd/system/invoice-tool.service
```

Add:
```ini
[Unit]
Description=Invoice Tool - Future Fabrik
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/invoice-tool
Environment="PATH=/var/www/invoice-tool/venv/bin"
ExecStart=/var/www/invoice-tool/venv/bin/gunicorn --bind 127.0.0.1:8080 --workers 2 --timeout 120 backend.app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Start service:
```bash
systemctl daemon-reload
systemctl enable invoice-tool
systemctl start invoice-tool
systemctl status invoice-tool
```

### F. Configure Nginx

```bash
nano /etc/nginx/sites-available/invoice-tool
```

Add:
```nginx
server {
    listen 80;
    server_name your-domain.com;  # or your_droplet_ip

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    location /static {
        alias /var/www/invoice-tool/frontend/dist;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable site:
```bash
ln -s /etc/nginx/sites-available/invoice-tool /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### G. Set Up SSL (Optional but Recommended)

```bash
# Install Certbot
apt install -y certbot python3-certbot-nginx

# Get SSL certificate
certbot --nginx -d your-domain.com

# Auto-renewal is set up automatically
```

### H. Set Up Firewall

```bash
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable
```

---

## 💾 Data Persistence

### App Platform

**Problem:** App Platform uses ephemeral storage.

**Solutions:**

1. **Managed Database (Recommended):**
   ```yaml
   # Add to .do/app.yaml
   databases:
     - name: invoice-db
       engine: PG
       version: "15"
       production: false
       size: db-s-1vcpu-1gb
   ```

2. **Spaces (Object Storage):**
   - Create DigitalOcean Space
   - Store PDFs and data files
   - Use boto3 to interact

### Droplet

Data persists automatically:
- `/var/www/invoice-tool/data/`
- `/var/www/invoice-tool/output/`
- `/var/www/invoice-tool/example-invoices/`

**Backup recommended:**
```bash
# Create backup script
nano /root/backup-invoice-tool.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf /root/backups/invoice-tool-$DATE.tar.gz /var/www/invoice-tool/data /var/www/invoice-tool/output
find /root/backups -name "invoice-tool-*.tar.gz" -mtime +30 -delete
```

```bash
chmod +x /root/backup-invoice-tool.sh
crontab -e
```

Add daily backup:
```
0 2 * * * /root/backup-invoice-tool.sh
```

---

## 💰 Cost Comparison

### App Platform
- **Basic:** $5/month (512MB RAM, 1 vCPU)
- **Professional:** $12/month (1GB RAM, 1 vCPU)
- **Managed Database:** +$15/month (optional)
- **Total:** $5-27/month

### Droplet
- **Basic:** $4/month (512MB RAM, 1 vCPU, 10GB SSD)
- **Regular:** $6/month (1GB RAM, 1 vCPU, 25GB SSD)
- **Total:** $4-6/month

**Recommendation:** 
- **App Platform** for ease of use
- **Droplet** for cost savings and control

---

## 🔧 Configuration Files

### App Platform Uses:
- `.do/app.yaml` - App configuration
- `Dockerfile` - Container build (optional)
- `requirements.txt` - Python deps
- `frontend/package.json` - Node deps

### Droplet Uses:
- Systemd service file
- Nginx configuration
- Environment file (.env)

---

## 🧪 Testing Deployment

### App Platform
```bash
# Health check
curl https://invoice-tool-xxxxx.ondigitalocean.app/api/health

# Examples
curl https://invoice-tool-xxxxx.ondigitalocean.app/api/parse-examples
```

### Droplet
```bash
# From droplet
curl http://localhost:8080/api/health

# From browser
http://your_droplet_ip/api/health
```

---

## 🆘 Troubleshooting

### App Platform

**Build Fails:**
```bash
doctl apps logs YOUR_APP_ID --type BUILD
```

**Runtime Errors:**
```bash
doctl apps logs YOUR_APP_ID --type RUN
```

**Common Issues:**
- Missing `OPENAI_API_KEY` → Add in settings
- Port mismatch → Ensure PORT=8080
- Build timeout → Increase timeout in app.yaml

### Droplet

**Service won't start:**
```bash
journalctl -u invoice-tool -n 50
```

**Nginx errors:**
```bash
nginx -t
tail -f /var/log/nginx/error.log
```

**Permission issues:**
```bash
chown -R www-data:www-data /var/www/invoice-tool
chmod -R 755 /var/www/invoice-tool
```

---

## 🔄 Updates and Redeployment

### App Platform
**Automatic (GitHub connected):**
- Push to `main` branch
- App Platform auto-deploys

**Manual:**
```bash
doctl apps create-deployment YOUR_APP_ID
```

### Droplet
```bash
cd /var/www/invoice-tool
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
cd frontend && npm install && npm run build
systemctl restart invoice-tool
```

---

## 📊 Monitoring

### App Platform
- View logs in console
- Set up alerts for errors
- Monitor resource usage

### Droplet
**Install monitoring:**
```bash
curl -sSL https://repos.insights.digitalocean.com/install.sh | bash
```

**Check resources:**
```bash
htop
df -h
free -m
```

---

## ✅ Deployment Checklist

### App Platform
- [ ] GitHub repo created and pushed
- [ ] DigitalOcean account set up
- [ ] App created from GitHub
- [ ] Environment variables set
- [ ] Build successful
- [ ] Health check passes
- [ ] Frontend loads
- [ ] PDF generation works

### Droplet
- [ ] Droplet created
- [ ] SSH access confirmed
- [ ] Dependencies installed
- [ ] App cloned and built
- [ ] Systemd service running
- [ ] Nginx configured
- [ ] SSL certificate installed (optional)
- [ ] Firewall configured
- [ ] Backup script set up

---

## 📚 Resources

- **App Platform Docs:** https://docs.digitalocean.com/products/app-platform/
- **Droplet Docs:** https://docs.digitalocean.com/products/droplets/
- **doctl CLI:** https://docs.digitalocean.com/reference/doctl/
- **This Project:** See `README.md`

---

**Status:** ✅ Ready for DigitalOcean Deployment  
**Recommended:** App Platform for ease, Droplet for cost  
**Estimated Time:** 10-30 minutes depending on option

