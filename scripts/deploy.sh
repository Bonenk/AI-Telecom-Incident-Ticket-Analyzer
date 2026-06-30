#!/usr/bin/env bash
set -euo pipefail

# Telecom Ticket Analyzer - Deployment Script
# Supports Docker (Coolify / EC2) and direct (systemd) deployment.
#
# Usage:
#   Docker-based (default):
#     ./scripts/deploy.sh --user ubuntu --host <IP> [--key ~/.ssh/key.pem] [--domain example.com]
#
#   Direct systemd deployment (original):
#     ./scripts/deploy.sh --user ubuntu --host <IP> [--key ~/.ssh/key.pem] [--domain example.com] [--direct]

# --- Config ---
APP_DIR="/opt/telecom-ticket-analyzer"
REPO_URL="https://github.com/YOUR_USER/telecom-ticket-analyzer.git"
BRANCH="main"
STREAMLIT_PORT=8501
DOMAIN=""
DIRECT=false

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --user) SSH_USER="$2"; shift 2 ;;
        --host) SSH_HOST="$2"; shift 2 ;;
        --key) SSH_KEY="$2"; shift 2 ;;
        --domain) DOMAIN="$2"; shift 2 ;;
        --direct) DIRECT=true; shift ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

if [[ -z "${SSH_USER:-}" || -z "${SSH_HOST:-}" ]]; then
    echo "Usage: $0 --user ubuntu --host <IP> [--key ~/.ssh/key.pem] [--domain example.com] [--direct]"
    exit 1
fi

SSH_OPTS=""
[[ -n "${SSH_KEY:-}" ]] && SSH_OPTS="-i $SSH_KEY"

if $DIRECT; then
    # ─── Direct systemd deployment (original) ───
    REMOTE_CMDS=$(cat <<'EOF'
set -euo pipefail

sudo apt-get update -qq
sudo apt-get install -y -qq python3-pip python3-venv nginx curl git

curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

if [ -d /opt/telecom-ticket-analyzer ]; then
    cd /opt/telecom-ticket-analyzer && sudo -u ubuntu git pull
else
    sudo mkdir -p /opt/telecom-ticket-analyzer
    sudo chown ubuntu:ubuntu /opt/telecom-ticket-analyzer
    git clone --branch main https://github.com/YOUR_USER/telecom-ticket-analyzer.git /opt/telecom-ticket-analyzer
fi

cd /opt/telecom-ticket-analyzer
uv sync

if [ ! -f .env ]; then
    echo "WARNING: No .env file found. Create one before starting the app."
fi

sudo tee /etc/systemd/system/telecom-analyzer.service > /dev/null <<SERVICEEOF
[Unit]
Description=Telecom Ticket Analyzer (Streamlit)
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/telecom-ticket-analyzer
ExecStart=$HOME/.local/bin/uv run streamlit run app/streamlit_app.py --server.port $STREAMLIT_PORT --server.address 127.0.0.1
Restart=always
RestartSec=5
EnvironmentFile=/opt/telecom-ticket-analyzer/.env

[Install]
WantedBy=multi-user.target
SERVICEEOF

sudo systemctl daemon-reload
sudo systemctl enable telecom-analyzer
sudo systemctl restart telecom-analyzer

if [ -n "$DOMAIN" ]; then
    sudo tee /etc/nginx/sites-available/telecom-analyzer > /dev/null <<NGINXEOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:$STREAMLIT_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400;
    }
}
NGINXEOF

    sudo ln -sf /etc/nginx/sites-available/telecom-analyzer /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -t
    sudo systemctl reload nginx
fi

echo "=== Direct deployment complete ==="
echo "Streamlit running at http://127.0.0.1:$STREAMLIT_PORT"
EOF
)

else
    # ─── Docker-based deployment ───
    REMOTE_CMDS=$(cat <<'EOF'
set -euo pipefail

# Install Docker if not present
if ! command -v docker &>/dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq ca-certificates curl
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update -qq
    sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
    sudo usermod -aG docker ubuntu
    echo "Docker installed. You may need to re-login for group changes."
fi

if [ -d /opt/telecom-ticket-analyzer ]; then
    cd /opt/telecom-ticket-analyzer && sudo -u ubuntu git pull
else
    sudo mkdir -p /opt/telecom-ticket-analyzer
    sudo chown ubuntu:ubuntu /opt/telecom-ticket-analyzer
    git clone --branch main https://github.com/YOUR_USER/telecom-ticket-analyzer.git /opt/telecom-ticket-analyzer
fi

cd /opt/telecom-ticket-analyzer

if [ ! -f .env ]; then
    echo "WARNING: No .env file found. Create one at /opt/telecom-ticket-analyzer/.env"
fi

# Build and run with docker compose
sudo docker compose up --build -d

echo "=== Docker deployment complete ==="
echo "Container running on port $STREAMLIT_PORT"
echo "View logs: sudo docker logs telecom-ticket-analyzer -f"
echo "Restart:   sudo docker compose restart"
echo "Stop:      sudo docker compose down"
EOF
)

fi

ssh $SSH_OPTS "${SSH_USER}@${SSH_HOST}" "$REMOTE_CMDS"

echo "Deployment successful."
