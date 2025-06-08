"""
KreciDJ Owner Commands - Clean Implementation
Only for bot owner: 179558415624830976
"""

import discord
from discord.ext import commands
import subprocess
import asyncio
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

class OwnerCommands(commands.Cog):
    """Owner-only commands for bot management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.owner_id = 179558415624830976  # Your Discord ID
        print(f"🔧 OwnerCommands initialized for user: {self.owner_id}")
    
    def cog_check(self, ctx) -> bool:  # FIXED: Remove async and add return type
        """Ensure only owner can use these commands"""
        return ctx.author.id == self.owner_id

    @commands.group(name="admin", invoke_without_command=True)
    async def admin(self, ctx):
        """🔧 Admin Panel - Owner Only"""
        if ctx.author.id != self.owner_id:
            return await ctx.send("❌ Owner only!")
        
        embed = discord.Embed(
            title="🔧 KreciDJ Admin Panel",
            description="Available admin commands:",
            color=0xff9900,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="📊 Status Commands",
            value="`!admin test` - Test admin functionality\n"
                  "`!admin status` - Bot status\n"
                  "`!admin docker` - Docker info\n"
                  "`!admin logs` - Recent logs",
            inline=False
        )
        
        embed.add_field(
            name="🔄 Control Commands",
            value="`!admin update` - Update from Git\n"
                  "`!admin restart` - Restart bot",
            inline=False
        )
        
        # Show current version
        try:
            with open('version.txt', 'r') as f:
                version = f.read().strip()
        except:
            version = "unknown"
            
        embed.add_field(name="Version", value=f"`{version}`", inline=True)
        embed.add_field(name="Owner", value=f"<@{ctx.author.id}>", inline=True)
        embed.set_footer(text="KreciDJ Admin System")
        
        await ctx.send(embed=embed)

    @admin.command(name="test")
    async def admin_test(self, ctx):
        """🧪 Test admin functionality"""
        embed = discord.Embed(
            title="🧪 Admin Test Results",
            color=0x00ff00,
            timestamp=datetime.utcnow()
        )
        
        # Test basic info
        embed.add_field(
            name="✅ Authentication",
            value=f"User ID: `{ctx.author.id}`\nOwner ID: `{self.owner_id}`\nMatch: {'✅' if ctx.author.id == self.owner_id else '❌'}",
            inline=False
        )
        
        # Test bot status
        embed.add_field(
            name="🤖 Bot Status", 
            value=f"Ready: {'✅' if self.bot.is_ready() else '❌'}\n"
                  f"Latency: {round(self.bot.latency * 1000)}ms\n"
                  f"Guilds: {len(self.bot.guilds)}",
            inline=True
        )
        
        # Test environment
        embed.add_field(
            name="🔧 Environment",
            value=f"ENV: {os.getenv('ENVIRONMENT', 'unknown')}\n"
                  f"Python: Working ✅\n"
                  f"Docker: {'✅' if os.path.exists('/.dockerenv') else '❌'}",
            inline=True
        )
        
        await ctx.send(embed=embed)

    @admin.command(name="docker")
    async def admin_docker(self, ctx):
        """🐳 Docker container information"""
        embed = discord.Embed(
            title="🐳 Docker Status",
            color=0x0099ff,
            timestamp=datetime.utcnow()
        )
        
        try:
            # Alternative: Check if we're running in Docker
            if os.path.exists('/.dockerenv'):
                embed.add_field(
                    name="📊 Container Status", 
                    value="✅ Running inside Docker container", 
                    inline=False
                )
                
                # Check container stats via /proc instead of docker command
                try:
                    with open('/proc/1/cgroup', 'r') as f:
                        cgroup_info = f.read()
                    if 'docker' in cgroup_info.lower():
                        embed.add_field(
                            name="🐳 Container Type", 
                            value="Docker Container", 
                            inline=True
                        )
                except:
                    pass
            else:
                embed.add_field(
                    name="📊 Container Status", 
                    value="❌ Not running in Docker", 
                    inline=False
                )
            
            # Try to get container ID from hostname
            try:
                with open('/etc/hostname', 'r') as f:
                    container_id = f.read().strip()
                embed.add_field(
                    name="🆔 Container ID", 
                    value=f"`{container_id}`", 
                    inline=True
                )
            except:
                pass
                
        except Exception as e:
            embed.add_field(name="❌ Error", value=f"Docker info error: {e}", inline=False)
        
        # Health check (this should still work)
        try:
            health = subprocess.run(['curl', '-f', 'http://localhost:8080/health'], 
                                  capture_output=True, timeout=5)
            health_status = "✅ Healthy" if health.returncode == 0 else "❌ Unhealthy"
        except:
            health_status = "⚠️ Unknown"
            
        embed.add_field(name="🏥 Health", value=health_status, inline=True)
        
        # Version
        try:
            with open('/app/version.txt', 'r') as f:  # Use /app path in container
                version = f.read().strip()
        except:
            try:
                with open('version.txt', 'r') as f:  # Fallback to relative path
                    version = f.read().strip()
            except:
                version = "unknown"
                
        embed.add_field(name="📦 Version", value=f"`{version}`", inline=True)
        
        # Environment info
        embed.add_field(
            name="🔧 Environment", 
            value=f"ENV: {os.getenv('ENVIRONMENT', 'unknown')}\n"
                  f"PWD: {os.getcwd()}\n"
                  f"User: {os.getenv('USER', 'unknown')}", 
            inline=True
        )
        
        await ctx.send(embed=embed)

    @admin.command(name="status")
    async def admin_status(self, ctx):
        """📊 Comprehensive bot status"""
        embed = discord.Embed(
            title="📊 Bot Status Dashboard",
            color=0x00ff00 if self.bot.is_ready() else 0xff0000,
            timestamp=datetime.utcnow()
        )
        
        # Basic stats
        embed.add_field(
            name="🤖 Bot Info",
            value=f"Status: {'🟢 Online' if self.bot.is_ready() else '🔴 Offline'}\n"
                  f"Latency: {round(self.bot.latency * 1000)}ms\n"
                  f"Guilds: {len(self.bot.guilds)}\n"
                  f"Voice: {len(self.bot.voice_clients)}",
            inline=True
        )
        
        # Environment info
        embed.add_field(
            name="🔧 Environment",
            value=f"ENV: {os.getenv('ENVIRONMENT', 'development')}\n"
                  f"Docker: {'✅' if os.path.exists('/.dockerenv') else '❌'}\n"
                  f"Health: {'✅' if os.path.exists('/app') else '❌'}",
            inline=True
        )
        
        # Version info
        try:
            with open('version.txt', 'r') as f:
                version = f.read().strip()
        except:
            version = "unknown"
            
        embed.add_field(
            name="📦 Version",
            value=f"Current: `{version}`\nOwner: <@{self.owner_id}>",
            inline=True
        )
        
        await ctx.send(embed=embed)

    @admin.command(name="logs")
    async def admin_logs(self, ctx, lines: int = 20):
        """📋 Show recent logs"""
        if lines > 50:
            lines = 50
            
        try:
            result = subprocess.run([
                'docker-compose', 'logs', '--tail', str(lines), 'discord-bot'
            ], capture_output=True, text=True, timeout=15)
            
            logs = result.stdout
            if not logs.strip():
                return await ctx.send("📋 No recent logs found")
                
            # Truncate for Discord
            if len(logs) > 1800:
                logs = "...\n" + logs[-1800:]
                
            embed = discord.Embed(
                title=f"📋 Recent Logs ({lines} lines)",
                description=f"```{logs}```",
                color=0x00ffff,
                timestamp=datetime.utcnow()
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error getting logs: {e}")

    @admin.command(name="update")
    async def admin_update(self, ctx, force: Optional[str] = None):  # FIXED: Add Optional type hint
        """🔄 Update bot from GitHub"""
        force_update = force is not None and force.lower() == 'force'  # FIXED: Check for None properly
        
        embed = discord.Embed(
            title="🔄 Update System",
            description="Checking for updates...",
            color=0x00ff00
        )
        
        msg = await ctx.send(embed=embed)
        
        try:
            # Check git status
            subprocess.run(['git', 'fetch', 'origin', 'main'], timeout=30)
            
            local = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], 
                                 capture_output=True, text=True).stdout.strip()
            remote = subprocess.run(['git', 'rev-parse', '--short', 'origin/main'], 
                                  capture_output=True, text=True).stdout.strip()
            
            embed.add_field(name="Current", value=f"`{local}`", inline=True)
            embed.add_field(name="Remote", value=f"`{remote}`", inline=True)
            
            if local == remote and not force_update:
                embed.description = "✅ Already up to date!"
                return await msg.edit(embed=embed)
            
            # Execute update
            embed.description = "📥 Updating..."
            embed.add_field(name="Status", value="Running update script...", inline=False)
            await msg.edit(embed=embed)
            
            # Run update script
            if os.path.exists('./scripts/docker-update.sh'):
                result = subprocess.run(['bash', './scripts/docker-update.sh'], 
                                      capture_output=True, text=True, timeout=180)
                
                if result.returncode == 0:
                    embed.description = "✅ Update successful!"
                    embed.color = 0x00ff00
                else:
                    embed.description = "❌ Update failed!"
                    embed.color = 0xff0000
                    # FIXED: Handle potential None stderr
                    error_text = result.stderr[-500:] if result.stderr else "No error details"
                    embed.fields[-1].value = f"Error: {error_text}"
            else:
                embed.description = "❌ Update script not found!"
                embed.color = 0xff0000
            
            await msg.edit(embed=embed)
            
        except Exception as e:
            embed.description = f"❌ Update error: {e}"
            embed.color = 0xff0000
            await msg.edit(embed=embed)

    @admin.command(name="restart")
    async def admin_restart(self, ctx):
        """🔄 Restart the bot"""
        embed = discord.Embed(
            title="🔄 Restarting Bot",
            description="Bot will restart in 5 seconds...",
            color=0xffaa00
        )
        
        await ctx.send(embed=embed)
        await asyncio.sleep(5)
        
        # Log restart
        print(f"🔄 Bot restart initiated by {ctx.author} ({ctx.author.id})")
        
        # Exit - Docker will restart the container
        await self.bot.close()

async def setup(bot):
    """Load the OwnerCommands cog"""
    await bot.add_cog(OwnerCommands(bot))
    print("✅ OwnerCommands cog loaded successfully")