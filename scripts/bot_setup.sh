#!/bin/bash

echo "🤖 Discord Music Bot - Bot Environment Setup"

# Check if running as botuser
if [ "$USER" != "botuser" ]; then
    echo "❌ Must run as botuser"
    echo "Switch: sudo su - botuser"
    exit 1
fi

# Navigate to home
cd /home/botuser

# Clone repository
echo "📥 Cloning repository..."
git clone https://github.com/PeterPage2115/KreciDJ.git discord-music-bot
cd discord-music-bot

# Create Python virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data logs backups

# Copy environment template
echo "⚙️ Setting up configuration..."
cp .env.example .env

# Set proper permissions
echo "🔐 Setting permissions..."
chown -R botuser:botuser /home/botuser/discord-music-bot
chmod +x scripts/*.sh

echo "✅ Bot environment ready"
echo ""
echo "📝 IMPORTANT: Edit configuration file"
echo "📁 File: /home/botuser/discord-music-bot/.env"
echo ""
echo "📋 Required changes:"
echo "  - DISCORD_TOKEN=your_production_bot_token"
echo "  - OWNER_ID=your_discord_user_id"
echo "  - ENVIRONMENT=production"
echo ""
echo "🔧 Edit with: nano .env"