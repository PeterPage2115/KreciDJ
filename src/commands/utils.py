"""Utility commands for the Discord Music Bot"""

import discord
from discord.ext import commands
import psutil
import platform
from datetime import datetime, timezone
import wavelink
import time
import asyncio
import subprocess
import re


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
            "`!join` - Dołącz do kanału głosowego",
            "`!leave` - Opuść kanał głosowy", 
            "`!play <query>` - Odtwórz muzykę",
            "`!pause` - Zatrzymaj odtwarzanie",
            "`!resume` - Wznów odtwarzanie",
            "`!stop` - Zatrzymaj i wyczyść kolejkę",
            "`!skip` - Pomiń aktualny utwór",
            "`!queue` - Pokaż kolejkę utworów",
            "`!volume <1-100>` - Zmień głośność",
            "`!shuffle` - Przetasuj kolejkę",
            "`!loop` - Zmień tryb powtarzania",
            "`!nowplaying` - Aktualnie grany utwór",
            "`!clear` - Wyczyść kolejkę"
        ]
        
        embed.add_field(
            name="🎵 Komendy Muzyczne",
            value="\n".join(music_cmds),
            inline=False
        )
        
        # Utility commands
        util_cmds = [
            "`!help` - Ta wiadomość",
            "`!ping` - Sprawdź ping bota",
            "`!stats` - Statystyki bota",
            "`!info` - Informacje o bocie"
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
        
        await ctx.send(embed=embed)
    
    @commands.command(name='ping')
    async def ping(self, ctx):
        """Check bot latency with accurate measurements"""
        # Measure response time
        start_time = time.perf_counter()
        message = await ctx.send("🏓 Measuring latency...")
        end_time = time.perf_counter()
        
        response_time = round((end_time - start_time) * 1000, 1)
        bot_latency = round(self.bot.latency * 1000, 1)
        
        # Simple and reliable Lavalink status check
        lavalink_latency = "N/A"
        lavalink_status = "❌ Disconnected"
        
        try:
            if wavelink.Pool.nodes:
                node = list(wavelink.Pool.nodes.values())[0]
                if node and node.status == wavelink.NodeStatus.CONNECTED:
                    # Simple connection check - reliable and fast
                    lavalink_latency = "Connected ✅"
                    lavalink_status = "🟢 Active"
                    
                    # Add players count if available
                    try:
                        if hasattr(node, 'players') and node.players:
                            player_count = len([p for p in node.players.values() if p.connected])
                            if player_count > 0:
                                lavalink_latency = f"Connected ✅ ({player_count} active)"
                    except:
                        pass  # Keep simple "Connected ✅" if player count fails
                else:
                    lavalink_latency = "Disconnected"
                    lavalink_status = "🔴 Inactive"
            else:
                lavalink_latency = "No nodes"
                lavalink_status = "❌ No nodes"
        except Exception as e:
            lavalink_latency = "Error"
            lavalink_status = "❌ Error"
        
        # Enhanced status indicators
        if bot_latency < 100 and "🟢" in lavalink_status:
            status = "🟢 Doskonały"
            color = 0x00ff00
        elif bot_latency < 150:
            status = "🟡 Dobry"
            color = 0xffff00
        elif bot_latency < 300:
            status = "🟠 Średni"
            color = 0xff8800
        else:
            status = "🔴 Wysoki"
            color = 0xff0000
        
        # Create enhanced embed
        embed = discord.Embed(
            title="🏓 Pong!",
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(
            name="🤖 Discord API", 
            value=f"**{bot_latency}ms**", 
            inline=True
        )
        embed.add_field(
            name="🎵 Lavalink", 
            value=f"**{lavalink_latency}**", 
            inline=True
        )
        embed.add_field(
            name="📊 Status", 
            value=f"**{status}**", 
            inline=True
        )
        embed.add_field(
            name="⚡ Response Time", 
            value=f"**{response_time}ms**", 
            inline=False
        )
        
        # Add performance indicators
        if bot_latency < 100:
            performance = "🚀 Excellent performance"
        elif bot_latency < 200:
            performance = "✅ Good performance"
        elif bot_latency < 500:
            performance = "⚠️ Moderate performance"
        else:
            performance = "🐌 Slow performance"
            
        embed.add_field(
            name="📈 Performance", 
            value=performance, 
            inline=False
        )
        
        embed.set_footer(text=f"Lavalink: {lavalink_status}")
        
        await message.edit(content="", embed=embed)
    
    @commands.command(name='stats', aliases=['statistics'])
    async def stats(self, ctx):
        """Show comprehensive bot statistics"""
        # Calculate uptime
        uptime = datetime.now(timezone.utc) - self.bot.start_time.replace(tzinfo=timezone.utc)
        uptime_str = str(uptime).split('.')[0]
        
        embed = discord.Embed(
            title="📊 Statystyki Bota",
            description="Szczegółowe informacje o działaniu bota",
            color=0x3498db,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Basic bot stats
        embed.add_field(name="🏠 Serwery", value=f"**{len(self.bot.guilds)}**", inline=True)
        embed.add_field(name="👥 Użytkownicy", value=f"**{len(self.bot.users)}**", inline=True)
        embed.add_field(name="🎵 Połączenia głosowe", value=f"**{len(self.bot.voice_clients)}**", inline=True)
        
        embed.add_field(name="⏱️ Uptime", value=f"**{uptime_str}**", inline=True)
        embed.add_field(name="💬 Komendy wykonane", value=f"**{getattr(self.bot, 'commands_executed', 0)}**", inline=True)
        embed.add_field(name="🐍 Python", value=f"**{platform.python_version()}**", inline=True)
        
        # Enhanced system stats
        memory_mb = 0  # Initialize with default value
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = round(memory_info.rss / 1024 / 1024, 1)
            cpu_percent = round(process.cpu_percent(interval=0.1), 1)
            
            # System-wide stats
            system_memory = psutil.virtual_memory()
            system_cpu = psutil.cpu_percent(interval=0.1)
            
            embed.add_field(name="💾 Bot RAM", value=f"**{memory_mb} MB**", inline=True)
            embed.add_field(name="💻 Bot CPU", value=f"**{cpu_percent}%**", inline=True)
            embed.add_field(name="🖥️ System RAM", value=f"**{system_memory.percent}%**", inline=True)
            
        except Exception as e:
            embed.add_field(name="💻 System", value="**N/A**", inline=True)
        
        # Enhanced Lavalink stats
        lavalink_info = "❌ Disconnected"
        if wavelink.Pool.nodes:
            connected_nodes = [n for n in wavelink.Pool.nodes.values() 
                             if n.status == wavelink.NodeStatus.CONNECTED]
            if connected_nodes:
                node_count = len(connected_nodes)
                total_nodes = len(wavelink.Pool.nodes)
                lavalink_info = f"✅ **{node_count}/{total_nodes}** nodes active"
            else:
                lavalink_info = "🟠 **Nodes available but disconnected**"
        
        embed.add_field(name="🎵 Lavalink", value=lavalink_info, inline=True)
        
        # Add performance indicators
        if memory_mb < 200:
            memory_status = "🟢 Low"
        elif memory_mb < 500:
            memory_status = "🟡 Normal"
        else:
            memory_status = "🔴 High"
            
        embed.add_field(name="📈 Memory Status", value=f"**{memory_status}**", inline=True)
        
        embed.set_footer(
            text=f"Bot ID: {self.bot.user.id} | {platform.system()} {platform.release()}",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='info', aliases=['about'])
    async def info(self, ctx):
        """Show comprehensive bot information"""
        embed = discord.Embed(
            title="ℹ️ Informacje o Bocie",
            description="**KreciDJ** - Zaawansowany bot muzyczny dla Discord",
            color=0x9b59b6,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Basic info
        embed.add_field(name="🔧 Wersja", value="**1.0.0 ALPHA**", inline=True)
        embed.add_field(name="👨‍💻 Developer", value="**KreciDev**", inline=True)
        embed.add_field(name="📚 Framework", value="**discord.py 2.3+**", inline=True)
        
        embed.add_field(name="🎵 Music Engine", value="**Wavelink + Lavalink**", inline=True)
        embed.add_field(name="🐍 Python", value=f"**{platform.python_version()}**", inline=True)
        embed.add_field(name="🌐 Prefix", value=f"**{self.bot.command_prefix}**", inline=True)
        
        # Enhanced features list
        features = [
            "🎵 **Multi-source music** (YouTube, Spotify, SoundCloud)",
            "📋 **Advanced queue management** (50 tracks max)", 
            "🔀 **Shuffle, loop & repeat modes**",
            "🎛️ **Volume control & equalizer**",
            "⏯️ **Interactive control panel**",
            "📊 **Real-time statistics & monitoring**",
            "🛡️ **Auto-disconnect & error recovery**",
            "⚡ **Low latency & high performance**"
        ]
        
        embed.add_field(
            name="✨ Funkcje",
            value="\n".join(features),
            inline=False
        )
        
        # Technical specs
        tech_specs = [
            f"**Environment:** {getattr(self.bot.config, 'ENVIRONMENT', 'production')}",
            f"**Lavalink Host:** {getattr(self.bot.config, 'LAVALINK_HOST', 'N/A')}",
            f"**Max Queue Size:** {getattr(self.bot.config, 'MAX_QUEUE_SIZE', 50)}",
            f"**Health Monitoring:** Port {getattr(self.bot.config, 'HEALTH_CHECK_PORT', 8080)}"
        ]
        
        embed.add_field(
            name="⚙️ Konfiguracja",
            value="\n".join(tech_specs),
            inline=False
        )
        
        # Links and support
        embed.add_field(
            name="🔗 Linki",
            value="[GitHub Repository](https://github.com/PeterPage2115/KreciDJ)\n[Support Server](https://discord.gg/your-server)",
            inline=True
        )
        
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        embed.set_footer(
            text=f"Made with ❤️ by KreciDev | Uptime: {str(datetime.now(timezone.utc) - self.bot.start_time.replace(tzinfo=timezone.utc)).split('.')[0]}"
        )
        
        await ctx.send(embed=embed)


async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(UtilityCommands(bot))