#!/bin/bash

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║      Simple Invoice Tool Deployment (Like Sniper Bot Style)   ║"
echo "╚════════════════════════════════════════════════════════════════╝"

# Just run the backend directly, serve frontend as static files
cat > /etc/systemd/system/invoice-tool.service << 'SYSTEMD_EOF'
[Unit]
Description=Invoice Tool
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/invoice-tool
Environment="PATH=/var/www/invoice-tool/venv/bin"
ExecStart=/var/www/invoice-tool/venv/bin/python backend/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SYSTEMD_EOF

systemctl daemon-reload
systemctl enable invoice-tool
systemctl restart invoice-tool

echo ""
echo "✅ Done! Running on port 5001"
echo "   Access: http://YOUR_IP:5001"
systemctl status invoice-tool
