# 🎵 KreciDJ - Discord Music Bot

Advanced Discord music bot with Wavelink integration, persistent controls, and production-ready deployment.

## ✨ Features

- 🎵 **Multi-source Music**: YouTube, Spotify search → YouTube, SoundCloud
- 📋 **Advanced Queue Management**: 50 track limit, duration controls
- 🎛️ **Persistent Control Panel**: Always-visible music controls with buttons
- 🔄 **Auto-reconnect**: Automatic Lavalink failover and error recovery
- 📊 **Health Monitoring**: Built-in health checks and metrics endpoint
- 🚀 **Production Ready**: Systemd service, logging, auto-deployment
- 🛡️ **Security**: Rate limiting, cooldowns, input validation

## 🎮 Commands

### Music Commands
- `!play <song>` - Play music (auto-joins voice channel)
- `!pause` - Pause current track
- `!resume` - Resume playback
- `!skip` - Skip current track
- `!stop` - Stop playback and clear queue
- `!queue` - Show current queue
- `!volume <0-100>` - Set volume
- `!nowplaying` - Show current track info
- `!shuffle` - Shuffle queue

### Utility Commands
- `!help` - Show command list
- `!ping` - Check bot latency

## 🚀 Quick Start

### Development Setup
```bash
# Clone repository
git clone https://github.com/PeterPage2115/KreciDJ.git
cd KreciDJ

# Setup environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure bot
cp .env.example .env
# Edit .env with your bot token

# Run bot
python src/bot.py
```

### Production Deployment

See [Production Deployment Guide](#production-deployment) below.

## ⚙️ Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Discord Configuration
DISCORD_TOKEN=your_bot_token_here
OWNER_ID=your_discord_user_id

# Environment
ENVIRONMENT=development  # or production
COMMAND_PREFIX=!

# Lavalink Configuration  
LAVALINK_HOST=lava-v4.ajieblogs.eu.org
LAVALINK_PORT=80
LAVALINK_PASSWORD=https://dsc.gg/ajidevserver
```

## 🐳 Production Deployment

### Requirements
- Linux server (Ubuntu 22.04+ recommended)
- Python 3.11+
- 2GB RAM, 2 CPU cores minimum
- Internet connection for Lavalink

### Quick Deployment

1. **Setup System** (as root):
```bash
curl -o system_setup.sh https://raw.githubusercontent.com/PeterPage2115/KreciDJ/main/scripts/system_setup.sh
chmod +x system_setup.sh
./system_setup.sh
```

2. **Setup Bot** (as botuser):
```bash
su - botuser
curl -o bot_setup.sh https://raw.githubusercontent.com/PeterPage2115/KreciDJ/main/scripts/bot_setup.sh
chmod +x bot_setup.sh
./bot_setup.sh
```

3. **Configure Bot**:
```bash
cd /home/botuser/discord-music-bot
nano .env
# Set your production Discord token and owner ID
```

4. **Deploy**:
```bash
./scripts/deploy_production.sh
```

5. **Verify**:
```bash
# Check service status
sudo systemctl status discord-bot

# Check health
curl http://localhost:8080/health

# View logs
sudo journalctl -u discord-bot -f
```

## 📊 Monitoring

### Health Endpoints
- `http://localhost:8080/health` - Basic health check
- `http://localhost:8080/metrics` - Detailed metrics
- `http://localhost:8080/status` - Simple OK response

### Service Management
```bash
# Start/stop/restart service
sudo systemctl start discord-bot
sudo systemctl stop discord-bot
sudo systemctl restart discord-bot

# View logs
sudo journalctl -u discord-bot -f
sudo journalctl -u discord-bot --since "1 hour ago"

# Check status
sudo systemctl status discord-bot
```

## 🔧 Troubleshooting

### Common Issues

**Bot doesn't respond to commands:**
- Check bot is online in Discord
- Verify bot has proper permissions in server
- Check logs: `sudo journalctl -u discord-bot`

**Music playback issues:**
- Verify Lavalink connection in logs
- Check voice channel permissions
- Try different music source

**High memory usage:**
- Normal: 100-300MB
- High (>500MB): restart service
- Check for memory leaks in logs

### Log Analysis
```bash
# Recent errors
sudo journalctl -u discord-bot --since "1 hour ago" | grep ERROR

# Memory usage
ps aux | grep python | grep bot

# Health status
curl localhost:8080/health | python -m json.tool
```

## 🏗️ Architecture

```
src/
├── bot.py              # Main bot application
├── config.py           # Configuration management
├── commands/           # Command modules
│   ├── music.py        # Music commands
│   ├── owner_commands.py # Owner-only commands
│   └── utils.py        # Utility commands
├── utils/              # Utility modules
│   ├── formatters.py   # Message formatting
│   ├── error_handler.py # Error handling
│   └── logger.py       # Logging configuration
├── views/              # Discord UI components
│   └── controls.py     # Music control buttons
└── health/             # Health monitoring
    └── monitor.py      # Health check endpoints
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- Create an issue on GitHub for bug reports
- Join our Discord server for support
- Check the troubleshooting guide above

## ⭐ Acknowledgments

- discord.py library
- Wavelink library  
- Lavalink audio server
- Contributors and testers