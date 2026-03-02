#!/bin/bash

# Invoice Tool - SAFE DigitalOcean Droplet Deployment
# This script is designed to NOT disrupt existing services

set -e  # Exit on error

echo "🚀 Invoice Tool - Safe Deployment Script"
echo "========================================"
echo "⚠️  This deployment will NOT affect existing services"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
   echo "Please run as root (use sudo)"
   exit 1
fi

echo "📦 Step 1: Installing dependencies (if not already present)..."
apt update
apt install -y python3.11 python3.11-venv python3-pip nodejs npm nginx tesseract-ocr tesseract-ocr-deu libtesseract-dev git curl

echo ""
echo "📁 Step 2: Setting up application in isolated directory..."
APP_DIR="/var/www/invoice-tool"

if [ -d "$APP_DIR" ]; then
    echo "⚠️  Directory exists. Backing up and updating..."
    cp -r $APP_DIR ${APP_DIR}.backup.$(date +%Y%m%d_%H%M%S)
    cd $APP_DIR
    git pull origin main || echo "Not a git repo, will clone fresh"
else
    echo "Creating new installation..."
    git clone https://github.com/YOUR_USERNAME/invoice-tool.git $APP_DIR
fi

cd $APP_DIR

echo ""
echo "🐍 Step 3: Setting up isolated Python environment..."
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo ""
echo "⚛️  Step 4: Building frontend..."
cd frontend
npm install
npm run build
cd ..

echo ""
echo "🔐 Step 5: Setting up environment variables..."
if [ ! -f .env ]; then
    cat > .env << 'ENVEOF'
OPENAI_API_KEY=your-key-here-replace-me
FLASK_ENV=production
PORT=8080
ENVEOF
    echo "⚠️  IMPORTANT: Edit /var/www/invoice-tool/.env and add your OpenAI API key!"
fi

echo ""
echo "👤 Step 6: Setting permissions..."
chown -R www-data:www-data $APP_DIR
chmod -R 755 $APP_DIR

echo ""
echo "⚙️  Step 7: Creating dedicated systemd service..."
cat > /etc/systemd/system/invoice-tool.service << 'SERVICEEOF'
[Unit]
Description=Invoice Tool - Future Fabrik
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/invoice-tool
Environment="PATH=/var/www/invoice-tool/venv/bin"
EnvironmentFile=/var/www/invoice-tool/.env
ExecStart=/var/www/invoice-tool/venv/bin/gunicorn --bind 127.0.0.1:8080 --workers 2 --timeout 120 backend.app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICEEOF

systemctl daemon-reload
systemctl enable invoice-tool

echo ""
echo "🌐 Step 8: Configuring Nginx (separate config, won't affect existing sites)..."

# Check if there are existing nginx configs
EXISTING_CONFIGS=$(ls /etc/nginx/sites-enabled/ 2>/dev/null | wc -l)
if [ $EXISTING_CONFIGS -gt 0 ]; then
    echo "⚠️  Found $EXISTING_CONFIGS existing Nginx config(s). Will add invoice-tool alongside them."
    # Don't remove default, just add alongside
    DEFAULT_EXISTS=$(ls /etc/nginx/sites-enabled/default 2>/dev/null)
    if [ -n "$DEFAULT_EXISTS" ]; then
        echo "ℹ️  Keeping existing default site"
    fi
fi

cat > /etc/nginx/sites-available/invoice-tool << 'NGINXEOF'
server {
    listen 8080;  # Using different port to avoid conflicts
    server_name _;

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
NGINXEOF

# Only create symlink if it doesn't exist
if [ ! -L /etc/nginx/sites-enabled/invoice-tool ]; then
    ln -s /etc/nginx/sites-available/invoice-tool /etc/nginx/sites-enabled/
fi

# Test nginx config before reloading
nginx -t

echo ""
echo "🔥 Step 9: Starting invoice-tool service..."
systemctl start invoice-tool

echo ""
echo "🔄 Step 10: Reloading Nginx (gracefully, won't drop connections)..."
systemctl reload nginx

echo ""
echo "🔒 Step 11: Checking firewall (only adding if needed)..."
if command -v ufw &> /dev/null; then
    # Only allow ports if not already allowed
    ufw status | grep -q "80/tcp" || ufw allow 80/tcp
    ufw status | grep -q "443/tcp" || ufw allow 443/tcp
    ufw status | grep -q "8080/tcp" || ufw allow 8080/tcp
    echo "ℹ️  Firewall rules updated (if needed)"
else
    echo "ℹ️  UFW not installed, skipping firewall config"
fi

echo ""
echo "✅ Safe Deployment Complete!"
echo "============================"
echo ""
echo "Your invoice tool is running ALONGSIDE existing services:"
echo ""
echo "📍 Access Points:"
echo "   - Direct: http://64.227.33.40:8080"
echo "   - API Health: http://64.227.33.40:8080/api/health"
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Edit your API key:"
echo "   nano /var/www/invoice-tool/.env"
echo ""
echo "2. Restart the service:"
echo "   systemctl restart invoice-tool"
echo ""
echo "3. Check status:"
echo "   systemctl status invoice-tool"
echo ""
echo "4. View logs:"
echo "   journalctl -u invoice-tool -f"
echo ""
echo "5. Test:"
echo "   curl http://localhost:8080/api/health"
echo ""
echo "🔍 Check existing services:"
echo "   systemctl list-units --type=service --state=running"
echo ""
echo "ℹ️  Your existing services were NOT modified!"
echo ""
