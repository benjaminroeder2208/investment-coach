#!/bin/bash
# investment-coach-vps-deploy-production.sh
# Production-Ready Deployment für Investment Coach VPS
# Ubuntu 24.04 LTS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Investment Coach VPS Deployment${NC}"
echo -e "${BLUE}Production Ready${NC}"
echo -e "${BLUE}========================================${NC}\n"

# ===== INTERACTIVE SETUP =====

echo -e "${YELLOW}📋 Bitte gib folgende Informationen ein:${NC}\n"

read -p "👤 VPS User Name (default: investment-coach): " VPS_USER
VPS_USER=${VPS_USER:-"investment-coach"}

read -p "🏠 VPS Home Verzeichnis (default: /home/${VPS_USER}): " VPS_HOME
VPS_HOME=${VPS_HOME:-"/home/${VPS_USER}"}

read -p "📦 App Verzeichnis (default: ${VPS_HOME}/investment-coach): " APP_DIR
APP_DIR=${APP_DIR:-"${VPS_HOME}/investment-coach"}

read -p "🌐 Domain Name (z.B. investment-coach.example.com): " DOMAIN
if [ -z "$DOMAIN" ]; then
    echo -e "${RED}❌ Domain ist erforderlich!${NC}"
    exit 1
fi

read -p "🤖 Telegram Bot Token: " TELEGRAM_TOKEN
if [ -z "$TELEGRAM_TOKEN" ]; then
    echo -e "${YELLOW}⚠️ Telegram Token wird später benötigt${NC}"
    TELEGRAM_TOKEN="PLACEHOLDER_TELEGRAM_TOKEN"
fi

read -p "🔑 Scalable Client ID (optional): " SCALABLE_CLIENT_ID
SCALABLE_CLIENT_ID=${SCALABLE_CLIENT_ID:-"PLACEHOLDER_CLIENT_ID"}

read -p "🔐 Scalable Client Secret (optional): " SCALABLE_CLIENT_SECRET
SCALABLE_CLIENT_SECRET=${SCALABLE_CLIENT_SECRET:-"PLACEHOLDER_CLIENT_SECRET"}

read -p "🔗 GitHub Repo URL (default: https://github.com/benjaminroeder2208/investment-coach.git): " GITHUB_REPO
GITHUB_REPO=${GITHUB_REPO:-"https://github.com/benjaminroeder2208/investment-coach.git"}

echo -e "\n${BLUE}✅ Konfiguration:${NC}"
echo "  User: $VPS_USER"
echo "  Home: $VPS_HOME"
echo "  App: $APP_DIR"
echo "  Domain: $DOMAIN"
echo "  Repo: $GITHUB_REPO"
echo ""

read -p "Fortfahren? (ja/nein): " CONFIRM
if [ "$CONFIRM" != "ja" ]; then
    echo "Abgebrochen."
    exit 1
fi

# ===== STEP 1: System Update =====

echo -e "\n${YELLOW}[1/8] System Update...${NC}"
apt-get update
apt-get upgrade -y
apt-get install -y \
    build-essential wget curl git zsh vim \
    python3.10 python3.10-venv python3-pip \
    postgresql postgresql-contrib \
    redis-server \
    nginx certbot python3-certbot-nginx \
    ufw fail2ban \
    postgresql-client htop

echo -e "${GREEN}✓ System aktualisiert${NC}\n"

# ===== STEP 2: Create User & Directories =====

echo -e "${YELLOW}[2/8] Erstelle User & Verzeichnisse...${NC}"

if ! id "$VPS_USER" &>/dev/null; then
    useradd -m -s /bin/bash $VPS_USER
    echo -e "${GREEN}✓ User erstellt: $VPS_USER${NC}"
else
    echo -e "${GREEN}✓ User existiert bereits: $VPS_USER${NC}"
fi

# Create directory structure
sudo -u $VPS_USER mkdir -p $APP_DIR
sudo -u $VPS_USER mkdir -p $VPS_HOME/backups
sudo -u $VPS_USER mkdir -p $VPS_HOME/logs
sudo -u $VPS_USER mkdir -p $VPS_HOME/scripts

echo -e "${GREEN}✓ Verzeichnisse erstellt${NC}\n"

# ===== STEP 3: PostgreSQL Setup =====

echo -e "${YELLOW}[3/8] PostgreSQL Setup...${NC}"

systemctl start postgresql
systemctl enable postgresql

DB_PASSWORD=$(openssl rand -base64 16)

sudo -u postgres psql << EOF
DO \$\$ BEGIN
  CREATE USER $VPS_USER WITH PASSWORD '$DB_PASSWORD';
EXCEPTION WHEN duplicate_object THEN RAISE NOTICE 'User already exists'; END
\$\$;

ALTER USER $VPS_USER CREATEDB;

DROP DATABASE IF EXISTS investment_coach;
CREATE DATABASE investment_coach OWNER $VPS_USER;

GRANT ALL PRIVILEGES ON DATABASE investment_coach TO $VPS_USER;
EOF

echo -e "${GREEN}✓ PostgreSQL konfiguriert${NC}"
echo "  Database: investment_coach"
echo "  User: $VPS_USER"
echo "  Password: $DB_PASSWORD"
echo ""

# ===== STEP 4: Redis Setup =====

echo -e "${YELLOW}[4/8] Redis Setup...${NC}"

systemctl start redis-server
systemctl enable redis-server

redis-cli ping > /dev/null && echo -e "${GREEN}✓ Redis ist aktiv${NC}" || echo -e "${RED}✗ Redis Fehler${NC}"
echo ""

# ===== STEP 5: Clone App & Setup Python =====

echo -e "${YELLOW}[5/8] Klone Application...${NC}"

sudo -u $VPS_USER git clone $GITHUB_REPO $APP_DIR 2>/dev/null || echo "Repo bereits geklont"

sudo -u $VPS_USER python3.10 -m venv $APP_DIR/venv

sudo -u $VPS_USER bash -c "source $APP_DIR/venv/bin/activate && pip install -q --upgrade pip setuptools wheel"
sudo -u $VPS_USER bash -c "source $APP_DIR/venv/bin/activate && pip install -q -r $APP_DIR/requirements.txt"

echo -e "${GREEN}✓ Application geklont & venv ready${NC}\n"

# ===== STEP 6: Environment Configuration =====

echo -e "${YELLOW}[6/8] Erstelle .env Datei...${NC}"

JWT_SECRET=$(openssl rand -base64 32)

sudo -u $VPS_USER tee $APP_DIR/.env > /dev/null << ENVFILE
# Auth
JWT_SECRET="$JWT_SECRET"
SCALABLE_CLIENT_ID="$SCALABLE_CLIENT_ID"
SCALABLE_CLIENT_SECRET="$SCALABLE_CLIENT_SECRET"

# Telegram
TELEGRAM_BOT_TOKEN="$TELEGRAM_TOKEN"

# Database
DATABASE_URL="postgresql://$VPS_USER:$DB_PASSWORD@localhost:5432/investment_coach"

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
ENVFILE

chmod 600 $APP_DIR/.env

echo -e "${GREEN}✓ .env erstellt${NC}"
echo "  JWT_SECRET: ${JWT_SECRET:0:20}..."
echo "  DATABASE_URL: postgresql://$VPS_USER:***@localhost:5432/investment_coach"
echo ""

# ===== STEP 7: Systemd Services =====

echo -e "${YELLOW}[7/8] Erstelle Systemd Services...${NC}"

# Streamlit Service
tee /etc/systemd/system/investment-coach-streamlit.service > /dev/null << SVCFILE
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
SVCFILE

# Telegram Bot Service
tee /etc/systemd/system/investment-coach-telegram.service > /dev/null << SVCFILE
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
SVCFILE

systemctl daemon-reload
systemctl enable investment-coach-streamlit
systemctl enable investment-coach-telegram

echo -e "${GREEN}✓ Systemd Services erstellt${NC}\n"

# ===== STEP 8: Nginx & SSL =====

echo -e "${YELLOW}[8/8] Nginx & SSL Setup...${NC}"

rm -f /etc/nginx/sites-enabled/default

tee /etc/nginx/sites-available/investment-coach > /dev/null << NGINXFILE
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
NGINXFILE

ln -sf /etc/nginx/sites-available/investment-coach /etc/nginx/sites-enabled/
nginx -t
systemctl enable nginx
systemctl restart nginx

echo -e "${GREEN}✓ Nginx konfiguriert${NC}"
echo ""

# ===== SUMMARY =====

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ VPS Deployment erfolgreich!${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo -e "${YELLOW}📋 Wichtige Informationen:${NC}\n"

echo "🔐 DATABASE CREDENTIALS:"
echo "  URL: postgresql://$VPS_USER:$DB_PASSWORD@localhost:5432/investment_coach"
echo "  (Bereits in .env gespeichert)\n"

echo "🌐 DOMAIN SETUP:"
echo "  Domain: $DOMAIN"
echo "  IP: 217.160.26.220"
echo "  TODO: DNS A-Record auf diese IP zeigen lassen\n"

echo "📄 CONFIG FILE:"
echo "  Location: $APP_DIR/.env"
echo "  TODO: TELEGRAM_TOKEN und SCALABLE Secrets updaten\n"

echo "🚀 NÄCHSTE SCHRITTE:\n"

echo "1️⃣ DNS konfigurieren:"
echo "   A Record: $DOMAIN → 217.160.26.220\n"

echo "2️⃣ .env Secrets updaten:"
echo "   nano $APP_DIR/.env"
echo "   - TELEGRAM_BOT_TOKEN eingeben"
echo "   - SCALABLE_CLIENT_ID eingeben"
echo "   - SCALABLE_CLIENT_SECRET eingeben\n"

echo "3️⃣ SSL-Zertifikat erstellen:"
echo "   certbot certonly --nginx -d $DOMAIN\n"

echo "4️⃣ Services starten:"
echo "   systemctl start investment-coach-streamlit"
echo "   systemctl start investment-coach-telegram\n"

echo "5️⃣ Status prüfen:"
echo "   systemctl status investment-coach-streamlit"
echo "   systemctl status investment-coach-telegram\n"

echo "6️⃣ Logs ansehen:"
echo "   journalctl -u investment-coach-streamlit -f"
echo "   journalctl -u investment-coach-telegram -f\n"

echo -e "${GREEN}✅ Setup komplett! Weiter geht's...${NC}\n"
