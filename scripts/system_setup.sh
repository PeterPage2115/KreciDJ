#!/bin/bash

echo "🚀 Discord Music Bot - System Setup"

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install essential packages
echo "📦 Installing essential packages..."
apt install -y \
    git \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    htop \
    nano \
    systemd \
    fail2ban \
    ufw \
    logrotate \
    wget

# Create bot user
echo "👤 Creating bot user..."
useradd -m -s /bin/bash botuser
usermod -aG sudo botuser

# Configure firewall
echo "🔥 Configuring firewall..."
ufw allow ssh
ufw allow 8080/tcp  # Health check port
ufw --force enable

# Setup fail2ban for SSH protection
echo "🛡️ Setting up fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban

echo "✅ System setup complete"
echo ""
echo "📋 Next steps:"
echo "1. su - botuser"
echo "2. Run bot setup script"