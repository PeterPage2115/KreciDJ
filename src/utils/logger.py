"""Enhanced logging system with Unicode support and analytics"""

import logging
import sys
import os
import json
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pathlib import Path


class BotLogger:
    """Enhanced logger with analytics and safe Unicode handling"""
    
    def __init__(self, config):
        self.config = config
        self.setup_directories()
        self.logger = self.setup_logger()
        self.command_count = 0
        
    def setup_directories(self):
        """Create necessary log directories"""
        Path("logs").mkdir(exist_ok=True)
        Path("data").mkdir(exist_ok=True)
        
    def setup_logger(self):
        """Setup comprehensive logging with Windows Unicode support"""
        logger = logging.getLogger('discord_bot')
        logger.setLevel(logging.DEBUG if self.config.DEBUG else logging.INFO)
        
        # Clear existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Console handler (Windows Unicode safe)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Safe console format (no emoji for Windows compatibility)
        console_format = logging.Formatter(
            '%(asctime)s - [%(levelname)s] - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)
        
        # File handler (UTF-8 with emoji support)
        if self.config.LOG_TO_FILE or self.config.ENVIRONMENT == 'production':
            file_handler = RotatingFileHandler(
                'logs/bot.log',
                maxBytes=getattr(self.config, 'LOG_ROTATION_SIZE', 10*1024*1024),
                backupCount=getattr(self.config, 'LOG_BACKUP_COUNT', 5),
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            
            # Detailed file format with emoji
            file_format = logging.Formatter(
                '%(asctime)s - [%(levelname)s] - %(name)s.%(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_format)
            logger.addHandler(file_handler)
            
        return logger
    
    def log_startup(self, bot_name, environment):
        """Log bot startup with environment info"""
        self.logger.info(f"=== BOT STARTUP ===")
        self.logger.info(f"Bot: {bot_name}")
        self.logger.info(f"Environment: {environment}")
        self.logger.info(f"Python: {sys.version.split()[0]}")
        self.logger.info(f"Platform: {os.name}")
        
    def log_command_usage(self, ctx, command_name, execution_time_ms=None, error=None):
        """Log command usage with analytics"""
        self.command_count += 1
        
        # Basic command log
        user_info = f"{ctx.author} ({ctx.author.id})"
        guild_info = f"{ctx.guild.name} ({ctx.guild.id})" if ctx.guild else "DM"
        
        if error:
            self.logger.error(f"COMMAND FAILED: {command_name} by {user_info} in {guild_info} - {error}")
        else:
            time_info = f" ({execution_time_ms}ms)" if execution_time_ms else ""
            self.logger.info(f"COMMAND: {command_name} by {user_info} in {guild_info}{time_info}")
        
        # Analytics (production only)
        if self.config.ENABLE_ANALYTICS and self.config.ENVIRONMENT == 'production':
            analytics_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'command': command_name,
                'user_id': str(ctx.author.id),
                'guild_id': str(ctx.guild.id) if ctx.guild else None,
                'execution_time_ms': execution_time_ms,
                'error': str(error) if error else None,
                'total_commands': self.command_count
            }
            self.logger.info(f"ANALYTICS: {json.dumps(analytics_data)}")
    
    def log_music_event(self, event_type, track_info=None, guild_id=None, error=None):
        """Log music-related events"""
        if error:
            self.logger.error(f"MUSIC ERROR [{event_type}]: {error}")
        else:
            track_name = getattr(track_info, 'title', 'Unknown') if track_info else 'N/A'
            self.logger.info(f"MUSIC [{event_type}]: {track_name} in guild {guild_id}")
    
    def log_system_event(self, event_type, details=None, level='info'):
        """Log system events (startup, shutdown, errors)"""
        message = f"SYSTEM [{event_type}]"
        if details:
            message += f": {details}"
            
        if level == 'error':
            self.logger.error(message)
        elif level == 'warning':
            self.logger.warning(message)
        else:
            self.logger.info(message)


# Global convenience functions
_bot_logger = None

def init_logger(config):
    """Initialize global logger"""
    global _bot_logger
    _bot_logger = BotLogger(config)
    return _bot_logger

def get_logger():
    """Get the global logger instance"""
    return _bot_logger

# Safe logging functions (Windows compatible)
def log_info(message, emoji=None):
    """Safe info logging"""
    if _bot_logger:
        prefix = f"[{emoji}] " if emoji else ""
        _bot_logger.logger.info(f"{prefix}{message}")

def log_error(message, emoji=None):
    """Safe error logging"""
    if _bot_logger:
        prefix = f"[{emoji}] " if emoji else ""
        _bot_logger.logger.error(f"{prefix}{message}")

def log_warning(message, emoji=None):
    """Safe warning logging"""
    if _bot_logger:
        prefix = f"[{emoji}] " if emoji else ""
        _bot_logger.logger.warning(f"{prefix}{message}")

def log_debug(message, emoji=None):
    """Safe debug logging"""
    if _bot_logger:
        prefix = f"[{emoji}] " if emoji else ""
        _bot_logger.logger.debug(f"{prefix}{message}")