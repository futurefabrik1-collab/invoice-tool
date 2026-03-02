#!/bin/bash

# Update systemd service to use port 5001 (avoid conflict with Nginx on 8080)
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
ExecStart=/var/www/invoice-tool/venv/bin/gunicorn --bind 127.0.0.1:5001 --workers 4 --chdir /var/www/invoice-tool backend.app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SYSTEMD_EOF

# Update Nginx to proxy to port 5001
cat > /etc/nginx/sites-available/invoice-tool << 'NGINX_EOF'
server {
    listen 8080;
    server_name _;

    # Serve frontend static files
    location / {
        root /var/www/invoice-tool/dist;
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to backend on port 5001
    location /api {
        proxy_pass http://127.0.0.1:5001;
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

systemctl daemon-reload
systemctl restart invoice-tool
systemctl reload nginx

echo "✅ Fixed! Backend now on port 5001, Nginx proxies from 8080"
systemctl status invoice-tool
