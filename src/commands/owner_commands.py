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
from datetime import datetime, timedelta
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
            # Now with Docker access, we can get real container info
            result = subprocess.run([
                'docker', 'ps', '--filter', 'name=kreci-dj-bot', 
                '--format', '{{.Status}}'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                status = result.stdout.strip()
                embed.add_field(name="📊 Container Status", value=f"```{status}```", inline=False)
                
                # Get detailed container info
                detail_result = subprocess.run([
                    'docker', 'inspect', 'kreci-dj-bot', 
                    '--format', '{{.State.Status}} | {{.Config.Image}} | {{.RestartCount}}'
                ], capture_output=True, text=True, timeout=10)
                
                if detail_result.returncode == 0:
                    details = detail_result.stdout.strip().split(' | ')
                    embed.add_field(name="🔍 Details", value=f"State: `{details[0]}`\nImage: `{details[1]}`\nRestarts: `{details[2]}`", inline=True)
            else:
                embed.add_field(name="📊 Container Status", value="❌ Container not found", inline=False)
                
        except Exception as e:
            # Fallback to container-internal checks
            if os.path.exists('/.dockerenv'):
                embed.add_field(name="📊 Container Status", value="✅ Running in Docker", inline=False)
            else:
                embed.add_field(name="📊 Container Status", value=f"❌ Docker error: {e}", inline=False)
        
        # Health check - use internal port since we're inside container
        try:
            health = subprocess.run(['curl', '-f', 'http://localhost:8080/health'], 
                                  capture_output=True, timeout=5)
            health_status = "✅ Healthy" if health.returncode == 0 else "❌ Unhealthy"
        except:
            health_status = "⚠️ Unknown"
            
        embed.add_field(name="🏥 Health", value=health_status, inline=True)
        
        # Port mapping info
        embed.add_field(name="🌐 Ports", value="Host: `9090` → Container: `8080`", inline=True)
        
        # Version
        try:
            with open('/app/version.txt', 'r') as f:
                version = f.read().strip()
        except:
            try:
                with open('version.txt', 'r') as f:
                    version = f.read().strip()
            except:
                version = "unknown"
                
        embed.add_field(name="📦 Version", value=f"`{version}`", inline=True)
        
        # Environment info
        embed.add_field(
            name="🔧 Environment", 
            value=f"ENV: {os.getenv('ENVIRONMENT', 'unknown')}\n"
                  f"Network: bot-network\n"
                  f"Subnet: 172.20.0.0/16", 
            inline=True
        )
        
        # Container filesystem info
        try:
            with open('/etc/hostname', 'r') as f:
                container_id = f.read().strip()
            embed.add_field(name="🆔 Container ID", value=f"`{container_id}`", inline=True)
        except:
            pass
        
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
    async def admin_update(self, ctx, force: Optional[str] = None):
        """🔄 Update bot from GitHub - Enhanced with Real-Time Updates"""
        force_update = force is not None and force.lower() in ['force', 'nuclear']
        nuclear_mode = force is not None and force.lower() == 'nuclear'
        
        embed = discord.Embed(
            title="🔄 KreciDJ Update System v2.1",
            description="🔍 Checking for updates...",
            color=0x00ff00,
            timestamp=datetime.utcnow()
        )
        
        msg = await ctx.send(embed=embed)
        
        try:
            # Step 1: Git fetch (from inside container)
            embed.description = "📡 Fetching latest changes..."
            await msg.edit(embed=embed)
            
            fetch_process = subprocess.run(
                ['git', 'fetch', 'origin', 'main'], 
                capture_output=True, text=True, timeout=30
            )
            
            if fetch_process.returncode != 0:
                embed.description = "❌ Failed to fetch updates"
                embed.color = 0xff0000
                return await msg.edit(embed=embed)
            
            # Step 2: Compare versions
            local = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], 
                                 capture_output=True, text=True).stdout.strip()
            remote = subprocess.run(['git', 'rev-parse', '--short', 'origin/main'], 
                                  capture_output=True, text=True).stdout.strip()
            
            # Clear previous fields and add new ones
            embed.clear_fields()
            embed.add_field(name="📊 Current", value=f"`{local}`", inline=True)
            embed.add_field(name="📊 Latest", value=f"`{remote}`", inline=True)
            embed.add_field(name="🔧 Mode", value="Nuclear" if nuclear_mode else "Standard", inline=True)
            
            if local == remote and not force_update:
                embed.description = "✅ Already up to date!"
                embed.color = 0x00ff00
                embed.add_field(name="✅ Status", value="No updates needed", inline=False)
                return await msg.edit(embed=embed)
            
            # Step 3: Prepare update with progress indicator
            embed.description = "🚀 Preparing update..."
            embed.add_field(name="⏱️ Status", value="Creating update trigger...", inline=False)
            embed.color = 0xffaa00
            await msg.edit(embed=embed)
            
            # Step 4: Create update info with estimated time
            update_info = {
                "timestamp": datetime.utcnow().isoformat(),
                "requested_by": str(ctx.author.id),
                "current_version": local,
                "target_version": remote,
                "mode": "nuclear" if nuclear_mode else "standard",
                "channel_id": str(ctx.channel.id),
                "message_id": str(msg.id)
            }
            
            # Write update request to shared volume
            with open('/app/data/update_request.json', 'w') as f:
                json.dump(update_info, f, indent=2)
            
            # Step 5: Final update message with progress tracking
            embed.description = "🔄 Update in progress..."
            embed.fields[-1].value = f"Updating from `{local}` to `{remote}`\n\n" \
                                   f"**Mode:** {'🔥 Nuclear' if nuclear_mode else '🔄 Standard'}\n" \
                                   f"**Estimated time:** {'3-4 minutes' if nuclear_mode else '2-3 minutes'}\n" \
                                   f"**Status:** Monitor will detect and execute update\n\n" \
                                   "⏰ **Progress tracking:**\n" \
                                   "└ 🔍 Update request created\n" \
                                   "└ ⏳ Waiting for monitor detection...\n" \
                                   "└ 🚀 Container rebuild will begin shortly"
            
            embed.color = 0xff9900
            await msg.edit(embed=embed)
            
            # Step 6: Send follow-up message that will survive restart
            follow_up = discord.Embed(
                title="🔄 Update Monitor Active",
                description=f"**Update Process Started**\n\n"
                           f"📋 **Request Details:**\n"
                           f"• Version: `{local}` → `{remote}`\n"
                           f"• Mode: {'Nuclear' if nuclear_mode else 'Standard'}\n"
                           f"• Time: {datetime.utcnow().strftime('%H:%M:%S UTC')}\n\n"
                           f"🤖 **Expected Process:**\n"
                           f"1. Monitor detects request (10s)\n"
                           f"2. Execute update script\n"
                           f"3. {'Complete rebuild' if nuclear_mode else 'Standard rebuild'}\n"
                           f"4. Health checks\n"
                           f"5. Bot returns online\n\n"
                           f"⏱️ **Estimated completion:** {(datetime.utcnow() + timedelta(minutes=4 if nuclear_mode else 3)).strftime('%H:%M UTC')}",
                color=0x3498db,
                timestamp=datetime.utcnow()
            )
            
            follow_up.set_footer(text="Monitor this channel for bot return status")
            await ctx.send(embed=follow_up)
            
            # Give time for messages to send, then exit to trigger restart
            await asyncio.sleep(3)
            await self.bot.close()
            
        except Exception as e:
            embed.description = f"❌ Update error: {str(e)}"
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