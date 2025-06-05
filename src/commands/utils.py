"""Utility commands for the Discord Music Bot"""

import discord
from discord.ext import commands
import psutil
import platform
from datetime import datetime, timezone
import wavelink


class UtilityCommands(commands.Cog):
    """Basic utility commands"""
    
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name='help', aliases=['h'])
    async def help_command(self, ctx):
        """Show all available commands"""
        embed = discord.Embed(
            title="🎵 Muzyczny Bot - Komendy",
            description="Lista wszystkich dostępnych komend",
            color=0x00ff00
        )
        
        # Music commands
        music_cmds = [
            "`?join` - Dołącz do kanału głosowego",
            "`?leave` - Opuść kanał głoswy", 
            "`?play <query>` - Odtwórz muzykę",
            "`?pause` - Zatrzymaj odtwarzanie",
            "`?resume` - Wznów odtwarzanie",
            "`?stop` - Zatrzymaj i wyczyść kolejkę",
            "`?skip` - Pomiń aktualny utwór",
            "`?queue` - Pokaż kolejkę utworów",
            "`?volume <1-100>` - Zmień głośność",
            "`?shuffle` - Przetasuj kolejkę",
            "`?loop` - Zmień tryb powtarzania",
            "`?nowplaying` - Aktualnie grany utwór",
            "`?clear` - Wyczyść kolejkę"
        ]
        
        embed.add_field(
            name="🎵 Komendy Muzyczne",
            value="\n".join(music_cmds),
            inline=False
        )
        
        # Utility commands
        util_cmds = [
            "`?help` - Ta wiadomość",
            "`?ping` - Sprawdź ping bota",
            "`?stats` - Statystyki bota",
            "`?info` - Informacje o bocie"
        ]
        
        embed.add_field(
            name="🔧 Komendy Użytkowe", 
            value="\n".join(util_cmds),
            inline=False
        )
        
        embed.set_footer(
            text=f"Prefix: {self.bot.command_prefix} | Bot by KreciDev",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
        )
        
        # DON'T DELETE - keep help message
        await ctx.send(embed=embed)
    
    @commands.command(name='ping')
    async def ping(self, ctx):
        """Check bot latency"""
        embed = discord.Embed(
            title="🏓 Pong!",
            color=0x00ff00
        )
        
        # Bot latency
        bot_latency = round(self.bot.latency * 1000)
        embed.add_field(name="🤖 Bot Latency", value=f"{bot_latency}ms", inline=True)
        
        # Lavalink latency
        lavalink_latency = "N/A"
        try:
            if wavelink.Pool.nodes:
                node = list(wavelink.Pool.nodes.values())[0]
                if hasattr(node, 'heartbeat'):
                    lavalink_latency = f"{round(node.heartbeat * 1000)}ms"
        except:
            pass
        
        embed.add_field(name="🎵 Lavalink Latency", value=lavalink_latency, inline=True)
        
        # Status indicators
        if bot_latency < 100:
            status = "🟢 Doskonały"
        elif bot_latency < 200:
            status = "🟡 Dobry"
        else:
            status = "🔴 Wysoki"
            
        embed.add_field(name="📊 Status", value=status, inline=True)
        
        # Delete after 10 seconds
        await ctx.send(embed=embed)
    
    @commands.command(name='stats', aliases=['statistics'])
    async def stats(self, ctx):
        """Show bot statistics"""
        # FIXED: Use timezone-aware datetime
        uptime = datetime.now(timezone.utc) - self.bot.start_time.replace(tzinfo=timezone.utc)
        uptime_str = str(uptime).split('.')[0]
        
        embed = discord.Embed(
            title="📊 Statystyki Bota",
            color=0x3498db
        )
        
        # Bot stats
        embed.add_field(name="🏠 Serwery", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="👥 Użytkownicy", value=len(self.bot.users), inline=True)
        embed.add_field(name="🎵 Połączenia głosowe", value=len(self.bot.voice_clients), inline=True)
        
        embed.add_field(name="⏱️ Uptime", value=uptime_str, inline=True)
        embed.add_field(name="💬 Komendy wykonane", value=self.bot.commands_executed, inline=True)
        embed.add_field(name="🐍 Python", value=platform.python_version(), inline=True)
        
        # System stats
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            embed.add_field(name="💻 CPU", value=f"{cpu_percent}%", inline=True)
            embed.add_field(name="🧠 RAM", value=f"{memory.percent}%", inline=True)
        except:
            embed.add_field(name="💻 System", value="N/A", inline=True)
        
        # Lavalink stats
        lavalink_status = "❌ Disconnected"
        if wavelink.Pool.nodes:
            lavalink_status = "✅ Connected"
            
        embed.add_field(name="🎵 Lavalink", value=lavalink_status, inline=True)
        
        embed.set_footer(
            text=f"Bot ID: {self.bot.user.id}",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
        )
        
        # Delete after 15 seconds
        await ctx.send(embed=embed)
    
    @commands.command(name='info', aliases=['about'])
    async def info(self, ctx):
        """Show bot information"""
        embed = discord.Embed(
            title="ℹ️ Informacje o Bocie",
            description="Zaawansowany bot muzyczny dla Discord",
            color=0x9b59b6
        )
        
        embed.add_field(name="🔧 Wersja", value="1.0.0 ALPHA", inline=True)
        embed.add_field(name="👨‍💻 Developer", value="KreciDev", inline=True)
        embed.add_field(name="📚 Framework", value="discord.py 2.0+", inline=True)
        
        embed.add_field(name="🎵 Music Engine", value="Wavelink + Lavalink", inline=True)
        embed.add_field(name="🐍 Python", value=platform.python_version(), inline=True)
        embed.add_field(name="🌐 Prefix", value=self.bot.command_prefix, inline=True)
        
        features = [
            "🎵 Wysokiej jakości odtwarzanie",
            "📋 Zarządzanie kolejką", 
            "🔀 Shuffle i loop",
            "🎛️ Kontrola głośności",
            "⏯️ Interaktywne przyciski",
            "📊 Statystyki w czasie rzeczywistym"
        ]
        
        embed.add_field(
            name="✨ Funkcje",
            value="\n".join(features),
            inline=False
        )
        
        # Delete after 20 seconds
        await ctx.send(embed=embed)


async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(UtilityCommands(bot))