#!/bin/bash

# Invoice Tool - DigitalOcean Droplet Deployment Script
# Run this ON YOUR DROPLET after cloning the repo

set -e  # Exit on error

echo "🚀 Invoice Tool Deployment Script"
echo "=================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
   echo "Please run as root (use sudo)"
   exit 1
fi

echo "📦 Step 1: Installing system dependencies..."
apt update
apt install -y python3.11 python3.11-venv python3-pip nodejs npm nginx tesseract-ocr tesseract-ocr-deu libtesseract-dev git

echo ""
echo "📁 Step 2: Setting up application directory..."
APP_DIR="/var/www/invoice-tool"
if [ ! -d "$APP_DIR" ]; then
    echo "Cloning repository..."
    git clone https://github.com/YOUR_USERNAME/invoice-tool.git $APP_DIR
else
    echo "Directory exists, pulling latest changes..."
    cd $APP_DIR
    git pull origin main
fi

cd $APP_DIR

echo ""
echo "🐍 Step 3: Setting up Python environment..."
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
    echo "Creating .env file..."
    cat > .env << 'ENVEOF'
OPENAI_API_KEY=your-key-here-replace-me
FLASK_ENV=production
PORT=8080
ENVEOF
    echo "⚠️  IMPORTANT: Edit /var/www/invoice-tool/.env and add your OpenAI API key!"
else
    echo ".env file already exists, skipping..."
fi

echo ""
echo "👤 Step 6: Setting permissions..."
chown -R www-data:www-data $APP_DIR
chmod -R 755 $APP_DIR

echo ""
echo "⚙️  Step 7: Creating systemd service..."
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
echo "🌐 Step 8: Configuring Nginx..."
cat > /etc/nginx/sites-available/invoice-tool << 'NGINXEOF'
server {
    listen 80;
    server_name _;  # Replace with your domain or IP

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

# Enable site
ln -sf /etc/nginx/sites-available/invoice-tool /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default  # Remove default site

# Test nginx config
nginx -t

echo ""
echo "🔥 Step 9: Starting services..."
systemctl restart nginx
systemctl start invoice-tool

echo ""
echo "🔒 Step 10: Configuring firewall..."
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw --force enable

echo ""
echo "✅ Deployment Complete!"
echo "======================="
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Edit your API key:"
echo "   nano /var/www/invoice-tool/.env"
echo "   (Add your OPENAI_API_KEY)"
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
echo "5. Test the app:"
echo "   curl http://localhost:8080/api/health"
echo ""
echo "6. Access in browser:"
echo "   http://$(curl -s ifconfig.me)"
echo ""
echo "🔐 Optional: Add SSL certificate with:"
echo "   apt install certbot python3-certbot-nginx"
echo "   certbot --nginx -d your-domain.com"
echo ""
