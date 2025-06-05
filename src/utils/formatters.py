"""Utility functions for formatting data with enhanced features"""

import discord
from datetime import timedelta
import re


def format_duration(milliseconds):
    """Format duration from milliseconds to readable format"""
    if not milliseconds or milliseconds <= 0:
        return "0:00"
    
    seconds = milliseconds // 1000
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"


def format_progress_bar(current_ms, total_ms, length=20):
    """Create a progress bar for track position"""
    if not total_ms or total_ms <= 0:
        return "▱" * length
    
    progress = min(current_ms / total_ms, 1.0)
    filled_length = int(progress * length)
    
    bar = "▰" * filled_length + "▱" * (length - filled_length)
    return bar


def truncate_string(text, max_length):
    """Truncate string with ellipsis if too long"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."


def format_track_info(track):
    """Format track information for display"""
    if not track:
        return "Nieznany utwór"
    
    title = getattr(track, 'title', 'Nieznany tytuł')
    author = getattr(track, 'author', None)
    
    if author:
        return f"{title} - {author}"
    return title


def format_queue_position(position, total):
    """Format queue position display"""
    return f"{position}/{total}"


def format_embed_color(status="default"):
    """Get color for embed based on status"""
    colors = {
        "success": 0x00ff00,
        "error": 0xff0000,
        "warning": 0xffaa00,
        "info": 0x00aaff,
        "music": 0x9932cc,
        "default": 0x36393f
    }
    return colors.get(status, colors["default"])


def create_music_embed(title, description=None, color="music"):
    """Create a standardized music embed"""
    embed = discord.Embed(
        title=title,
        description=description,
        color=format_embed_color(color)
    )
    return embed


def format_file_size(bytes_size):
    """Format file size to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"


def clean_url_for_display(url, max_length=50):
    """Clean and truncate URL for display"""
    if not url:
        return "N/A"
    
    # Remove common prefixes
    url = re.sub(r'^https?://(www\.)?', '', url)
    
    return truncate_string(url, max_length)


def format_time_ago(timestamp):
    """Format timestamp to 'time ago' format"""
    from datetime import datetime, timezone
    
    if not timestamp:
        return "Nieznany czas"
    
    try:
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        now = datetime.now(timezone.utc)
        diff = now - timestamp
        
        if diff.days > 0:
            return f"{diff.days} dni temu"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} godzin temu"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minut temu"
        else:
            return "Przed chwilą"
            
    except Exception:
        return "Nieznany czas"


def format_user_mention(user):
    """Safe format user mention"""
    if not user:
        return "Nieznany użytkownik"
    
    if hasattr(user, 'mention'):
        return user.mention
    elif hasattr(user, 'display_name'):
        return user.display_name
    else:
        return str(user)


def sanitize_text_for_embed(text, max_length=1024):
    """Sanitize text for Discord embed fields"""
    if not text:
        return "N/A"
    
    # Remove Discord markdown that might break
    text = re.sub(r'[`*_~|]', '', str(text))
    
    # Truncate if too long
    return truncate_string(text, max_length)


def format_list_with_numbers(items, start=1, max_items=10):
    """Format a list with numbers"""
    if not items:
        return "Brak elementów"
    
    formatted_items = []
    for i, item in enumerate(items[:max_items], start=start):
        formatted_items.append(f"`{i}.` {item}")
    
    if len(items) > max_items:
        formatted_items.append(f"... i {len(items) - max_items} więcej")
    
    return "\n".join(formatted_items)