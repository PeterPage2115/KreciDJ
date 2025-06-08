"""Enhanced configuration with comprehensive validation"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()


class Config:
    """Enhanced configuration class with validation and smart defaults"""
    
    # Environment Settings
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'
    
    # FIXED: Proper command prefix handling - usunięto @property i @classmethod
    @classmethod
    def get_command_prefix(cls):
        """Get command prefix based on environment"""
        if cls.ENVIRONMENT == 'development':
            return os.getenv('COMMAND_PREFIX_DEV', '?')
        else:
            return os.getenv('COMMAND_PREFIX_PROD', '!')
    
    # FIXED: Prosty property bez dekoratorów
    COMMAND_PREFIX = os.getenv('COMMAND_PREFIX_DEV', '?') if ENVIRONMENT == 'development' else os.getenv('COMMAND_PREFIX_PROD', '!')
    
    # Rate Limiting & Security
    RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    COMMAND_COOLDOWN = int(os.getenv('COMMAND_COOLDOWN', '3'))
    OWNER_ONLY_ADMIN_COMMANDS = os.getenv('OWNER_ONLY_ADMIN_COMMANDS', 'true').lower() == 'true'
    
    # Queue & Music Limits
    MAX_QUEUE_SIZE = int(os.getenv('MAX_QUEUE_SIZE', '50'))
    MAX_TRACK_DURATION = int(os.getenv('MAX_TRACK_DURATION', '1800'))  # 30 minutes
    AUTO_DISCONNECT_TIMEOUT = int(os.getenv('AUTO_DISCONNECT_TIMEOUT', '300'))  # 5 minutes
    
    # Lavalink Configuration - UPDATED dla publicznego serwera
    LAVALINK_HOST = os.getenv('LAVALINK_HOST', 'lava-v4.ajieblogs.eu.org')
    LAVALINK_PORT = int(os.getenv('LAVALINK_PORT', '80'))
    LAVALINK_PASSWORD = os.getenv('LAVALINK_PASSWORD', 'https://dsc.gg/ajidevserver')
    LAVALINK_HTTPS = os.getenv('LAVALINK_HTTPS', 'false').lower() == 'true'
    
    # Fallback Lavalink servers
    LAVALINK_FALLBACK_SERVERS = [
        {
            'host': 'lavalink.oops.wtf',
            'port': 443,
            'password': 'www.freelavalink.ga',
            'https': True
        },
        {
            'host': 'lavalink.devz.cloud',
            'port': 80, 
            'password': 'youshallnotpass',
            'https': False
        }
    ]
    
    # Database Configuration
    DATABASE_FILE = os.getenv('DATABASE_FILE', 'data/bot.db')
    BACKUP_ENABLED = os.getenv('BACKUP_ENABLED', 'true').lower() == 'true'
    BACKUP_INTERVAL_HOURS = int(os.getenv('BACKUP_INTERVAL_HOURS', '24'))
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_TO_FILE = os.getenv('LOG_TO_FILE', 'false').lower() == 'true'
    LOG_ROTATION_SIZE = int(os.getenv('LOG_ROTATION_SIZE', '10485760'))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    
    # Monitoring & Analytics
    HEALTH_CHECK_PORT = int(os.getenv('HEALTH_CHECK_PORT', '9090'))  # CHANGED: 8080 → 9090
    ENABLE_ANALYTICS = os.getenv('ENABLE_ANALYTICS', 'true').lower() == 'true'
    ENABLE_PERFORMANCE_MONITORING = os.getenv('ENABLE_PERFORMANCE_MONITORING', 'true').lower() == 'true'
    
    # Auto-Update Configuration (Production only)
    AUTO_UPDATE_ENABLED = os.getenv('AUTO_UPDATE_ENABLED', 'false').lower() == 'true'
    GITHUB_REPO = os.getenv('GITHUB_REPO', '')
    GITHUB_BRANCH = os.getenv('GITHUB_BRANCH', 'main')
    UPDATE_CHECK_INTERVAL = int(os.getenv('UPDATE_CHECK_INTERVAL', '600'))  # 10 minutes
    
    # Docker specific
    CONTAINER_TIMEZONE = os.getenv('CONTAINER_TIMEZONE', 'Europe/Warsaw')
    
    @classmethod
    def get_lavalink_uri(cls) -> str:
        """Generate primary Lavalink URI"""
        protocol = 'https' if cls.LAVALINK_HTTPS else 'http'
        return f"{protocol}://{cls.LAVALINK_HOST}:{cls.LAVALINK_PORT}"
    
    @classmethod
    def get_lavalink_nodes(cls):
        """Get all Lavalink nodes (primary + fallbacks)"""
        nodes = []
        
        # Primary node
        primary = {
            'host': cls.LAVALINK_HOST,
            'port': cls.LAVALINK_PORT,
            'password': cls.LAVALINK_PASSWORD,
            'https': cls.LAVALINK_HTTPS,
            'identifier': 'primary'
        }
        nodes.append(primary)
        
        # Fallback nodes
        for i, fallback in enumerate(cls.LAVALINK_FALLBACK_SERVERS):
            fallback['identifier'] = f'fallback_{i+1}'
            nodes.append(fallback)
            
        return nodes
    
    @classmethod
    def get_discord_token(cls) -> str:
        """Get Discord token with comprehensive validation"""
        environment = os.getenv('ENVIRONMENT', 'development')
        
        if environment == 'development':
            token = os.getenv('DISCORD_TOKEN_DEV') or os.getenv('DISCORD_TOKEN')
            if not token:
                raise ValueError(
                    "DISCORD_TOKEN_DEV or DISCORD_TOKEN is required for development environment. "
                    "Check your .env file."
                )
        else:
            token = os.getenv('DISCORD_TOKEN_PROD') or os.getenv('DISCORD_TOKEN')
            if not token:
                raise ValueError(
                    "DISCORD_TOKEN_PROD or DISCORD_TOKEN is required for production environment. "
                    "Check your .env file."
                )
        
        # Basic token validation
        if len(token) < 50:
            raise ValueError(f"Discord token appears invalid (too short: {len(token)} chars)")
        
        if not token.count('.') >= 2:
            raise ValueError("Discord token format appears invalid")
            
        return token
    
    @classmethod
    def validate_config(cls) -> bool:
        """Comprehensive configuration validation"""
        try:
            print("🔍 Validating bot configuration...")
            
            # Validate token
            token = cls.get_discord_token()
            
            # Validate environment
            environment = os.getenv('ENVIRONMENT', 'development')
            if environment not in ['development', 'production']:
                raise ValueError("ENVIRONMENT must be 'development' or 'production'")
            
            # Validate numeric values
            if cls.MAX_QUEUE_SIZE <= 0 or cls.MAX_QUEUE_SIZE > 100:
                raise ValueError("MAX_QUEUE_SIZE must be between 1-100")
            
            if cls.COMMAND_COOLDOWN < 0 or cls.COMMAND_COOLDOWN > 60:
                raise ValueError("COMMAND_COOLDOWN must be between 0-60 seconds")
            
            if cls.MAX_TRACK_DURATION <= 0 or cls.MAX_TRACK_DURATION > 7200:
                raise ValueError("MAX_TRACK_DURATION must be between 1-7200 seconds (2 hours)")
            
            if cls.AUTO_DISCONNECT_TIMEOUT < 60 or cls.AUTO_DISCONNECT_TIMEOUT > 3600:
                raise ValueError("AUTO_DISCONNECT_TIMEOUT must be between 60-3600 seconds")
            
            # Validate paths
            Path(cls.DATABASE_FILE).parent.mkdir(parents=True, exist_ok=True)
            
            # Validate auto-update settings
            if cls.AUTO_UPDATE_ENABLED and environment == 'production':
                if not cls.GITHUB_REPO:
                    raise ValueError("GITHUB_REPO required when AUTO_UPDATE_ENABLED=true")
            
            # Success message
            prefix = cls.get_command_prefix()
            print(f"✅ Configuration validated successfully!")
            print(f"   Environment: {environment}")
            print(f"   Discord token: {'*' * 20}...{token[-4:]}")
            print(f"   Command prefix: {prefix}")
            print(f"   Lavalink: {cls.LAVALINK_HOST}:{cls.LAVALINK_PORT}")
            print(f"   Queue limits: {cls.MAX_QUEUE_SIZE} songs, {cls.MAX_TRACK_DURATION}s max")
            print(f"   Auto-disconnect: {cls.AUTO_DISCONNECT_TIMEOUT}s")
            print(f"   Rate limiting: {'enabled' if cls.RATE_LIMIT_ENABLED else 'disabled'}")
            
            return True
            
        except Exception as e:
            print(f"❌ Configuration validation failed: {e}")
            raise

    @classmethod  
    def create_sample_env(cls):
        """Create sample .env file if it doesn't exist"""
        if not Path('.env').exists():
            print("📝 Creating sample .env file...")
            sample_content = f"""# Discord Configuration (REQUIRED)
DISCORD_TOKEN_DEV=your_dev_bot_token_here
DISCORD_TOKEN_PROD=your_prod_bot_token_here

# Environment Settings
ENVIRONMENT=development
DEBUG=true

# Command Configuration
COMMAND_PREFIX_DEV=?
COMMAND_PREFIX_PROD=!

# Rate Limiting
RATE_LIMIT_ENABLED=true
COMMAND_COOLDOWN=3

# Music Limits
MAX_QUEUE_SIZE=50
MAX_TRACK_DURATION=1800
AUTO_DISCONNECT_TIMEOUT=300

# Lavalink Configuration
LAVALINK_HOST=lava-v4.ajieblogs.eu.org
LAVALINK_PORT=80
LAVALINK_PASSWORD=https://dsc.gg/ajidevserver
LAVALINK_HTTPS=false

# Logging
LOG_LEVEL=INFO
LOG_TO_FILE=false

# Monitoring
HEALTH_CHECK_PORT=8080
ENABLE_ANALYTICS=true
"""
            
            with open('.env', 'w') as f:
                f.write(sample_content)
            
            print("✅ Sample .env created! Please edit it with your tokens.")


# Auto-validate on import (with helpful error messages)
if __name__ != '__main__':
    try:
        Config.validate_config()
    except Exception as e:
        print(f"⚠️ Configuration validation failed: {e}")
        print("💡 Run 'python -c \"from src.config import Config; Config.create_sample_env()\"' to create a sample .env file")
        # Don't raise in production to allow graceful handling