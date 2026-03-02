# Quick Deploy to Your Existing DigitalOcean Droplet

Since you already have a DigitalOcean droplet, here's the fastest way to deploy.

---

## 🚀 Super Quick Deployment (5 Commands)

### Step 1: Push to GitHub (from your Mac)

```bash
cd /Users/markburnett/DevPro/invoice-tool

# Initialize git if not already done
git init
git add .
git commit -m "Ready for droplet deployment"

# Add your GitHub repo
git remote add origin https://github.com/YOUR_USERNAME/invoice-tool.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy to Your Droplet (SSH into droplet)

```bash
# SSH into your droplet
ssh root@YOUR_DROPLET_IP

# Clone and run deployment script
git clone https://github.com/YOUR_USERNAME/invoice-tool.git /var/www/invoice-tool
cd /var/www/invoice-tool
chmod +x deploy-to-droplet.sh
sudo ./deploy-to-droplet.sh
```

### Step 3: Add Your API Key

```bash
# Edit .env file on droplet
nano /var/www/invoice-tool/.env

# Change this line:
# OPENAI_API_KEY=your-key-here-replace-me
# To your actual key:
# OPENAI_API_KEY=sk-proj-your-actual-key

# Save: Ctrl+O, Enter, Ctrl+X
```

### Step 4: Restart Service

```bash
systemctl restart invoice-tool
systemctl status invoice-tool
```

### Step 5: Test!

```bash
# On droplet
curl http://localhost:8080/api/health

# In browser (from your Mac)
# Open: http://YOUR_DROPLET_IP
```

---

## ✅ That's It!

Your invoice tool should now be running on your droplet.

---

## 🔍 Troubleshooting

### Check if service is running:
```bash
systemctl status invoice-tool
```

### View logs:
```bash
journalctl -u invoice-tool -f
```

### Restart service:
```bash
systemctl restart invoice-tool
```

### Check Nginx:
```bash
systemctl status nginx
nginx -t
```

### Test backend directly:
```bash
curl http://localhost:8080/api/health
```

---

## 🔐 Add SSL (Optional)

If you have a domain pointing to your droplet:

```bash
# Install Certbot
apt install certbot python3-certbot-nginx

# Get SSL certificate
certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
```

---

## 🔄 Updating Later

To deploy updates:

```bash
# On your Mac - push changes
git add .
git commit -m "Update"
git push

# On your droplet - pull and restart
cd /var/www/invoice-tool
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..
systemctl restart invoice-tool
```

---

## 📊 Monitor Your App

### Check resource usage:
```bash
htop
```

### Check disk space:
```bash
df -h
```

### Check memory:
```bash
free -m
```

### View all logs:
```bash
journalctl -u invoice-tool -n 100
```

---

## 🆘 Common Issues

### Port 8080 not accessible:
```bash
# Check firewall
ufw status
ufw allow 80/tcp
```

### Service won't start:
```bash
# Check logs
journalctl -u invoice-tool -n 50

# Check file permissions
chown -R www-data:www-data /var/www/invoice-tool
```

### Nginx error:
```bash
# Test config
nginx -t

# Check logs
tail -f /var/log/nginx/error.log
```

### Frontend not loading:
```bash
# Rebuild frontend
cd /var/www/invoice-tool/frontend
npm run build

# Check if dist folder exists
ls -la /var/www/invoice-tool/frontend/dist
```

---

## 💾 Backup Script (Optional)

Create automatic backups:

```bash
# Create backup directory
mkdir -p /root/backups

# Create backup script
cat > /root/backup-invoice-tool.sh << 'BACKUPEOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf /root/backups/invoice-tool-$DATE.tar.gz \
  /var/www/invoice-tool/data \
  /var/www/invoice-tool/output \
  /var/www/invoice-tool/.env
find /root/backups -name "invoice-tool-*.tar.gz" -mtime +30 -delete
BACKUPEOF

chmod +x /root/backup-invoice-tool.sh

# Add to cron (daily at 2 AM)
crontab -e
# Add this line:
# 0 2 * * * /root/backup-invoice-tool.sh
```

---

## 📋 What the Deployment Script Does

The `deploy-to-droplet.sh` script automatically:

1. ✅ Installs Python 3.11, Node.js, Nginx, Tesseract
2. ✅ Sets up virtual environment
3. ✅ Installs Python dependencies
4. ✅ Builds frontend
5. ✅ Creates systemd service
6. ✅ Configures Nginx
7. ✅ Sets up firewall
8. ✅ Starts services

---

## 🎯 Your Droplet Info

After deployment, your app will be at:

- **URL:** http://YOUR_DROPLET_IP
- **API:** http://YOUR_DROPLET_IP/api/health
- **Service:** `systemctl status invoice-tool`
- **Logs:** `journalctl -u invoice-tool -f`

---

**Ready to deploy?** Follow the 5 steps above and you'll be live in ~10 minutes! 🚀

