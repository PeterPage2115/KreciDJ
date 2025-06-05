"""Centralized error handling system"""

import discord
from discord.ext import commands
import logging
import traceback
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger('discord_bot')


class ErrorHandler:
    """Centralized error handling with retry mechanisms"""
    
    def __init__(self, bot):
        self.bot = bot
        self.error_cache: Dict[str, List[datetime]] = {}
        self.retry_delays = [1, 3, 5, 10, 30]  # Exponential backoff
        
    def is_rate_limited(self, error_key: str, max_errors: int = 5, time_window: int = 300) -> bool:
        """Check if we're being rate limited for this error type"""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=time_window)
        
        if error_key not in self.error_cache:
            self.error_cache[error_key] = []
        
        # Clean old errors
        self.error_cache[error_key] = [
            error_time for error_time in self.error_cache[error_key] 
            if error_time > cutoff
        ]
        
        # Add current error
        self.error_cache[error_key].append(now)
        
        return len(self.error_cache[error_key]) > max_errors
    
    async def handle_command_error(self, ctx, error):
        """Handle command errors with user-friendly messages"""
        error_id = f"cmd_{ctx.command.name if ctx.command else 'unknown'}_{type(error).__name__}"
        
        # Log the error
        logger.error(f"Command error in {ctx.command}: {error}")
        if hasattr(error, '__traceback__'):
            logger.debug("".join(traceback.format_exception(type(error), error, error.__traceback__)))
        
        # Don't spam users with error messages
        if self.is_rate_limited(error_id):
            return
        
        # Handle specific error types
        embed = discord.Embed(color=0xff0000)
        
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore unknown commands
            
        elif isinstance(error, commands.MissingRequiredArgument):
            embed.title = "❌ Brakuje argumentu"
            embed.description = f"Poprawne użycie: `{ctx.prefix}{ctx.command.signature}`"
            
        elif isinstance(error, commands.BadArgument):
            embed.title = "❌ Nieprawidłowy argument"
            embed.description = f"Sprawdź komendę: `{ctx.prefix}help {ctx.command.name}`"
            
        elif isinstance(error, commands.CommandOnCooldown):
            embed.title = "⏱️ Komenda na cooldown"
            embed.description = f"Spróbuj ponownie za {error.retry_after:.1f} sekund"
            
        elif isinstance(error, commands.MissingPermissions):
            embed.title = "🚫 Brak uprawnień"
            embed.description = "Nie masz uprawnień do tej komendy"
            
        elif isinstance(error, commands.BotMissingPermissions):
            embed.title = "🚫 Bot nie ma uprawnień"
            embed.description = f"Bot potrzebuje uprawnień: {', '.join(error.missing_permissions)}"
            
        elif isinstance(error, discord.HTTPException):
            embed.title = "🌐 Błąd sieci"
            embed.description = "Spróbuj ponownie za chwilę"
            
        else:
            embed.title = "❌ Nieoczekiwany błąd"
            embed.description = "Wystąpił błąd. Spróbuj ponownie lub skontaktuj się z administratorem."
            
        try:
            await ctx.send(embed=embed, delete_after=10)
        except:
            # Fallback if embed fails
            try:
                await ctx.send(f"❌ {embed.description}", delete_after=10)
            except:
                pass  # Give up if we can't send anything
    
    async def handle_wavelink_error(self, error, player=None, retry_count=0):
        """Handle Wavelink/music errors with retry mechanism"""
        error_type = type(error).__name__
        error_key = f"wavelink_{error_type}"
        
        logger.error(f"Wavelink error: {error}")
        
        # Don't retry too many times
        if retry_count >= len(self.retry_delays):
            logger.error(f"Max retries exceeded for Wavelink error: {error}")
            return False
        
        # Rate limiting check
        if self.is_rate_limited(error_key):
            logger.warning(f"Rate limited for error: {error_type}")
            return False
        
        # Retry with exponential backoff
        delay = self.retry_delays[retry_count]
        logger.info(f"Retrying Wavelink operation in {delay} seconds (attempt {retry_count + 1})")
        
        await asyncio.sleep(delay)
        return True
    
    async def handle_discord_error(self, error):
        """Handle Discord API errors"""
        error_type = type(error).__name__
        
        if isinstance(error, discord.HTTPException):
            if error.status == 429:  # Rate limited
                logger.warning(f"Discord rate limit hit: {error}")
                return
            elif error.status >= 500:  # Server error
                logger.error(f"Discord server error: {error}")
                return
        
        logger.error(f"Discord error: {error}")
    
    def setup_error_handlers(self):
        """Setup bot-wide error handlers"""
        
        @self.bot.event
        async def on_command_error(ctx, error):
            await self.handle_command_error(ctx, error)
        
        @self.bot.event
        async def on_error(event, *args, **kwargs):
            logger.error(f"Bot event error in {event}: {args}, {kwargs}")
            
        return self


# Retry decorator for functions
def retry_on_error(max_retries=3, delay=1, exceptions=(Exception,)):
    """Decorator to retry functions on error"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        raise e
                    
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}")
                    await asyncio.sleep(delay * (attempt + 1))  # Exponential backoff
                    
        return wrapper
    return decorator


# Global error handler instance
error_handler = None

def init_error_handler(bot):
    """Initialize global error handler"""
    global error_handler
    error_handler = ErrorHandler(bot)
    error_handler.setup_error_handlers()
    return error_handler

def get_error_handler():
    """Get global error handler"""
    return error_handler