#!/bin/bash

set -e  # Exit on error

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Invoice Tool Deployment (Safe Mode - Won't Affect Existing Services)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⚠️  This deployment will NOT affect existing services"
echo ""

# Step 1: Update package lists
echo "📦 Step 1: Updating package lists..."
apt-get update

# Step 2: Install system dependencies
echo "📦 Step 2: Installing system dependencies..."
apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    nginx \
    tesseract-ocr \
    poppler-utils \
    git \
    curl

# Check if node/npm are available
if ! command -v node &> /dev/null || ! command -v npm &> /dev/null; then
    echo "⚠️  Node.js/npm not properly installed. Installing from nodesource..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi

echo "✅ Node version: $(node --version)"
echo "✅ NPM version: $(npm --version)"

# Step 3: Set up Python virtual environment
echo "🐍 Step 3: Setting up Python virtual environment..."
cd /var/www/invoice-tool
python3.11 -m venv venv
source venv/bin/activate

# Step 4: Install Python dependencies
echo "📦 Step 4: Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Step 5: Install frontend dependencies
echo "📦 Step 5: Installing frontend dependencies..."
cd frontend
npm install

# Step 6: Build frontend
echo "🏗️  Step 6: Building frontend..."
npm run build

# Move build files to dist at project root
cd ..
if [ -d "frontend/dist" ]; then
    rm -rf dist
    cp -r frontend/dist dist
    echo "✅ Frontend build copied to /var/www/invoice-tool/dist"
fi

# Step 7: Create .env file if it doesn't exist
echo "⚙️  Step 7: Setting up environment file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file - YOU MUST ADD YOUR OPENAI_API_KEY!"
else
    echo "✅ .env file already exists"
fi

# Step 8: Create systemd service (using Flask app correctly)
echo "⚙️  Step 8: Creating systemd service..."
cat > /etc/systemd/system/invoice-tool.service << 'SYSTEMD_EOF'
[Unit]
Description=Invoice Tool Backend (Flask)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/invoice-tool
Environment="PATH=/var/www/invoice-tool/venv/bin"
Environment="FLASK_APP=backend/app.py"
ExecStart=/var/www/invoice-tool/venv/bin/gunicorn --bind 0.0.0.0:8080 --workers 4 --chdir /var/www/invoice-tool backend.app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SYSTEMD_EOF

# Step 9: Configure Nginx
echo "🌐 Step 9: Configuring Nginx..."
cat > /etc/nginx/sites-available/invoice-tool << 'NGINX_EOF'
server {
    listen 80;
    server_name _;

    # Serve frontend static files
    location / {
        root /var/www/invoice-tool/dist;
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to backend
    location /api {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # File upload size limit
    client_max_body_size 10M;
}
NGINX_EOF

# Enable the site
ln -sf /etc/nginx/sites-available/invoice-tool /etc/nginx/sites-enabled/invoice-tool

# Test Nginx configuration
nginx -t

# Step 10: Set up firewall (only if ufw is active)
if ufw status | grep -q "Status: active"; then
    echo "🔒 Step 10: Configuring firewall..."
    ufw allow 80/tcp || true
    ufw allow 443/tcp || true
else
    echo "⏭️  Step 10: Firewall not active, skipping..."
fi

# Step 11: Start services
echo "🚀 Step 11: Starting services..."
systemctl daemon-reload
systemctl enable invoice-tool
systemctl restart invoice-tool
systemctl reload nginx

# Step 12: Check status
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Deployment Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Service Status:"
systemctl status invoice-tool --no-pager -l || true
echo ""
echo "⚠️  IMPORTANT: Add your OpenAI API key!"
echo "   Run: nano /var/www/invoice-tool/.env"
echo "   Then: systemctl restart invoice-tool"
echo ""
echo "🌐 Access your app at: http://YOUR_DROPLET_IP"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
