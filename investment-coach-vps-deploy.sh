#!/bin/bash
# investment-coach-vps-deploy.sh
# Automated VPS Deployment Script - Run this on fresh Ubuntu 22.04

set -e  # Exit on error

echo "🚀 Investment Coach VPS Deployment Script"
echo "=========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ===== CONFIGURATION =====

VPS_USER="investment-coach"
VPS_HOME="/home/${VPS_USER}"
APP_DIR="${VPS_HOME}/investment-coach"
DOMAIN="${DOMAIN:-your-domain.com}"
TELEGRAM_TOKEN="${TELEGRAM_TOKEN:-your_token_here}"
GITHUB_REPO="${GITHUB_REPO:-https://github.com/your-org/investment-coach.git}"

echo -e "${YELLOW}Configuration:${NC}"
echo "Domain: $DOMAIN"
echo "User: $VPS_USER"
echo "App Dir: $APP_DIR"
echo ""

# ===== STEP 1: System Update =====

echo -e "${YELLOW}[1/8] System Update...${NC}"
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y \
    build-essential wget curl git zsh vim \
    python3.10 python3.10-venv python3-pip \
    postgresql postgresql-contrib \
    redis-server \
    nginx certbot python3-certbot-nginx \
    ufw fail2ban \
    postgresql-client

echo -e "${GREEN}✓ System updated${NC}\n"

# ===== STEP 2: Create User & Directories =====

echo -e "${YELLOW}[2/8] Creating User & Directories...${NC}"

if ! id "$VPS_USER" &>/dev/null; then
    sudo useradd -m -s /bin/bash $VPS_USER
    echo -e "${GREEN}✓ User created: $VPS_USER${NC}"
else
    echo -e "${GREEN}✓ User already exists: $VPS_USER${NC}"
fi

# Create directory structure
sudo -u $VPS_USER mkdir -p $APP_DIR
sudo -u $VPS_USER mkdir -p $VPS_HOME/backups
sudo -u $VPS_USER mkdir -p $VPS_HOME/logs
sudo -u $VPS_USER mkdir -p $VPS_HOME/scripts

echo -e "${GREEN}✓ Directories created${NC}\n"

# ===== STEP 3: PostgreSQL Setup =====

echo -e "${YELLOW}[3/8] Setting up PostgreSQL...${NC}"

sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
DO \$\$ BEGIN
  CREATE USER $VPS_USER WITH PASSWORD 'change_me_later';
EXCEPTION WHEN duplicate_object THEN RAISE NOTICE 'User already exists'; END
\$\$;

ALTER USER $VPS_USER CREATEDB;

SELECT 'DROP DATABASE IF EXISTS investment_coach;' | psql;
CREATE DATABASE investment_coach OWNER $VPS_USER;

GRANT ALL PRIVILEGES ON DATABASE investment_coach TO $VPS_USER;
EOF

echo -e "${GREEN}✓ PostgreSQL configured${NC}\n"

# ===== STEP 4: Redis Setup =====

echo -e "${YELLOW}[4/8] Setting up Redis...${NC}"

# Configure Redis
sudo tee /etc/redis/redis-ic.conf > /dev/null << 'EOF'
bind 127.0.0.1
port 6379
maxmemory 256mb
maxmemory-policy allkeys-lru
appendonly yes
EOF

sudo systemctl restart redis-server
sudo systemctl enable redis-server

# Test Redis
redis-cli ping > /dev/null && echo -e "${GREEN}✓ Redis configured${NC}\n" || echo -e "${RED}✗ Redis failed${NC}\n"

# ===== STEP 5: Clone App & Setup Python =====

echo -e "${YELLOW}[5/8] Cloning Application...${NC}"

sudo -u $VPS_USER git clone $GITHUB_REPO $APP_DIR 2>/dev/null || echo "Repo already cloned"

# Create venv
sudo -u $VPS_USER python3.10 -m venv $APP_DIR/venv

# Install dependencies
sudo -u $VPS_USER bash -c "source $APP_DIR/venv/bin/activate && pip install -q --upgrade pip setuptools wheel"
sudo -u $VPS_USER bash -c "source $APP_DIR/venv/bin/activate && pip install -q -r $APP_DIR/requirements.txt"

echo -e "${GREEN}✓ Application cloned & venv ready${NC}\n"

# ===== STEP 6: Environment Configuration =====

echo -e "${YELLOW}[6/8] Creating .env file...${NC}"

JWT_SECRET=$(openssl rand -base64 32)

sudo -u $VPS_USER tee $APP_DIR/.env > /dev/null << EOF
# Auth
JWT_SECRET="$JWT_SECRET"
SCALABLE_CLIENT_ID="your_client_id"
SCALABLE_CLIENT_SECRET="your_client_secret"

# Telegram
TELEGRAM_BOT_TOKEN="$TELEGRAM_TOKEN"

# Database
DATABASE_URL="postgresql://$VPS_USER:password@localhost:5432/investment_coach"

# Redis
REDIS_URL="redis://localhost:6379/0"

# Streamlit
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true

# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
EOF

sudo chown $VPS_USER:$VPS_USER $APP_DIR/.env
sudo chmod 600 $APP_DIR/.env

echo -e "${GREEN}✓ .env created (edit with your secrets)${NC}\n"

# ===== STEP 7: Systemd Services =====

echo -e "${YELLOW}[7/8] Creating Systemd Services...${NC}"

# Streamlit Service
sudo tee /etc/systemd/system/investment-coach-streamlit.service > /dev/null << EOF
[Unit]
Description=Investment Coach Streamlit UI
After=network.target postgresql.service redis-server.service
Wants=postgresql.service redis-server.service

[Service]
Type=simple
User=$VPS_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/streamlit run app_combined.py

Restart=always
RestartSec=10

StandardOutput=journal
StandardError=journal
SyslogIdentifier=streamlit

MemoryLimit=1G
CPUQuota=50%

NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

# Telegram Bot Service
sudo tee /etc/systemd/system/investment-coach-telegram.service > /dev/null << EOF
[Unit]
Description=Investment Coach Telegram Bot
After=network.target postgresql.service redis-server.service
Wants=postgresql.service redis-server.service

[Service]
Type=simple
User=$VPS_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/python telegram_coach_bot.py

Restart=always
RestartSec=5

StandardOutput=journal
StandardError=journal
SyslogIdentifier=telegram-bot

MemoryLimit=512M
CPUQuota=25%

NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable investment-coach-streamlit
sudo systemctl enable investment-coach-telegram

echo -e "${GREEN}✓ Systemd services created${NC}\n"

# ===== STEP 8: Nginx & SSL =====

echo -e "${YELLOW}[8/8] Setting up Nginx & SSL...${NC}"

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Create Nginx config
sudo tee /etc/nginx/sites-available/investment-coach > /dev/null << EOF
upstream streamlit_backend {
    server 127.0.0.1:8501;
}

server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    # SSL placeholder (will be updated by certbot)
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    access_log /var/log/nginx/investment-coach-access.log;
    error_log /var/log/nginx/investment-coach-error.log;

    location / {
        proxy_pass http://streamlit_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
        proxy_buffering off;
    }

    gzip on;
    gzip_types text/plain text/css text/javascript application/json;
}
EOF

sudo ln -sf /etc/nginx/sites-available/investment-coach /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx

# Create SSL certificate
echo -e "${YELLOW}Requesting SSL certificate for $DOMAIN...${NC}"
sudo certbot certonly --nginx -d $DOMAIN --non-interactive --agree-tos -m admin@$DOMAIN || echo "Please manually run: sudo certbot certonly --nginx -d $DOMAIN"

sudo systemctl reload nginx

echo -e "${GREEN}✓ Nginx & SSL configured${NC}\n"

# ===== Create Helper Scripts =====

echo -e "${YELLOW}Creating helper scripts...${NC}"

# Deploy script
sudo -u $VPS_USER tee $VPS_HOME/scripts/deploy.sh > /dev/null << 'SCRIPT'
#!/bin/bash
set -e

cd /home/investment-coach/investment-coach
source venv/bin/activate

echo "📦 Deploying Investment Coach..."
git pull origin production
pip install -q -r requirements.txt
alembic upgrade head

sudo systemctl restart investment-coach-streamlit investment-coach-telegram
sleep 3

sudo systemctl status investment-coach-streamlit --no-pager
echo "✅ Deployment complete!"
SCRIPT

# Health check script
sudo -u $VPS_USER tee $VPS_HOME/scripts/health_check.sh > /dev/null << 'SCRIPT'
#!/bin/bash

echo "=== Investment Coach Health Check ==="
echo "Time: $(date)"

echo -e "\n📊 Services:"
systemctl is-active --quiet investment-coach-streamlit && echo "✓ Streamlit" || echo "✗ Streamlit DOWN"
systemctl is-active --quiet investment-coach-telegram && echo "✓ Telegram" || echo "✗ Telegram DOWN"

echo -e "\n🗄️ Database:"
pg_isready -h localhost -U investment-coach -d investment_coach > /dev/null 2>&1 && echo "✓ PostgreSQL" || echo "✗ PostgreSQL DOWN"

echo -e "\n💾 Cache:"
redis-cli ping > /dev/null 2>&1 && echo "✓ Redis" || echo "✗ Redis DOWN"

echo -e "\n🌐 Web:"
curl -s -o /dev/null -w "HTTP %{http_code}\n" https://localhost 2>/dev/null || echo "Not accessible"

echo ""
SCRIPT

sudo chmod +x $VPS_HOME/scripts/deploy.sh $VPS_HOME/scripts/health_check.sh

echo -e "${GREEN}✓ Helper scripts created${NC}\n"

# ===== Final Status =====

echo ""
echo "=========================================="
echo -e "${GREEN}✅ VPS Deployment Complete!${NC}"
echo "=========================================="
echo ""
echo "📋 Next steps:"
echo ""
echo "1️⃣ Edit configuration:"
echo "   sudo nano /home/$VPS_USER/investment-coach/.env"
echo "   - Set SCALABLE_CLIENT_ID & SECRET"
echo "   - Set TELEGRAM_BOT_TOKEN"
echo "   - Set database password"
echo ""
echo "2️⃣ Start services:"
echo "   sudo systemctl start investment-coach-streamlit"
echo "   sudo systemctl start investment-coach-telegram"
echo ""
echo "3️⃣ Check status:"
echo "   /home/$VPS_USER/scripts/health_check.sh"
echo ""
echo "4️⃣ View logs:"
echo "   sudo journalctl -u investment-coach-streamlit -f"
echo "   sudo journalctl -u investment-coach-telegram -f"
echo ""
echo "5️⃣ Access web UI:"
echo "   https://$DOMAIN"
echo ""
echo "📚 Full documentation:"
echo "   /outputs/VPS_DEPLOYMENT_AND_BOT_AUTOMATION.md"
echo ""
