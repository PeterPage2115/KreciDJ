#!/bin/bash

echo "🚀 Discord Music Bot - Production Deployment"

# Configuration
BOT_USER="botuser"
BOT_DIR="/home/$BOT_USER/discord-music-bot"
SERVICE_NAME="discord-bot"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as botuser
if [ "$USER" != "$BOT_USER" ]; then
    log_error "Must run as $BOT_USER user"
    echo "Switch user: sudo su - $BOT_USER"
    exit 1
fi

# Check if bot directory exists
if [ ! -d "$BOT_DIR" ]; then
    log_error "Bot directory not found: $BOT_DIR"
    exit 1
fi

cd "$BOT_DIR"

log_info "Starting deployment process..."

# Step 1: Create backup
log_info "Creating backup..."
BACKUP_DIR="backups/deploy_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup important files
if [ -f .env ]; then
    cp .env "$BACKUP_DIR/"
    log_info "Backed up .env"
fi

if [ -d data ]; then
    cp -r data "$BACKUP_DIR/"
    log_info "Backed up data directory"
fi

# Step 2: Update code
log_info "Updating code from repository..."
git fetch origin
git reset --hard origin/main

if [ $? -ne 0 ]; then
    log_error "Git update failed"
    exit 1
fi

# Step 3: Update dependencies
log_info "Updating Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Step 4: Install/update systemd service
log_info "Installing systemd service..."
sudo cp scripts/discord-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable discord-bot

# Step 5: Restart service
log_info "Restarting Discord Bot service..."
sudo systemctl restart discord-bot

# Step 6: Wait and verify
log_info "Waiting for service to start..."
sleep 10

# Check service status
if sudo systemctl is-active --quiet discord-bot; then
    log_info "✅ Service is running"
else
    log_error "❌ Service failed to start"
    echo "Check logs: sudo journalctl -u discord-bot --since '2 minutes ago'"
    exit 1
fi

# Step 7: Health check
log_info "Performing health check..."
sleep 5

if curl -f http://localhost:8080/health >/dev/null 2>&1; then
    log_info "✅ Health check passed"
else
    log_warn "⚠️ Health check failed - service may still be starting"
fi

log_info "🎉 Deployment completed!"
echo ""
echo "📋 Next steps:"
echo "  - Monitor logs: sudo journalctl -u discord-bot -f"
echo "  - Check health: curl http://localhost:8080/health"
echo "  - Test bot: Try !help command in Discord"