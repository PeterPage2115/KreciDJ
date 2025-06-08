"""Enhanced owner/admin commands for bot management"""

import discord
from discord.ext import commands, tasks
import asyncio
import logging
import subprocess
import aiohttp
import json
import shutil
import os
from datetime import datetime, timedelta
from pathlib import Path

# Import psutil with fallback - FIXED: Proper import
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None  # Set to None for consistent checking
    logging.warning("psutil not available - system metrics will be limited")

logger = logging.getLogger('discord_bot')


class OwnerCommands(commands.Cog):
    """Enhanced owner commands with comprehensive management features"""
    
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.utcnow()
        self.last_update_check = None
        self.update_available = False
        self.latest_version = None
        
        # Start update checker if enabled
        if hasattr(bot, 'config') and getattr(bot.config, 'AUTO_UPDATE_ENABLED', False):
            self.update_checker.start()
    
    async def cog_unload(self):
        """Cleanup when cog is unloaded - FIXED: async method"""
        if hasattr(self, 'update_checker'):
            self.update_checker.cancel()
    
    @commands.group(name="admin", hidden=True)
    @commands.is_owner()
    async def admin_commands(self, ctx):  # FIXED: Added self parameter
        """Admin commands for bot management"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="🔧 KreciDJ Admin Panel",
                description="Docker-aware admin commands:",
                color=0xff9900,
                timestamp=datetime.utcnow()
            )
            embed.add_field(
                name="🔄 Update Commands", 
                value="`!admin update [force]` - Update from GitHub\n`!admin restart` - Restart container", 
                inline=False
            )
            embed.add_field(
                name="📊 Status Commands", 
                value="`!admin status` - Full bot status\n`!admin docker` - Container info\n`!admin logs [lines]` - Recent logs", 
                inline=False
            )
            embed.add_field(
                name="💾 Maintenance", 
                value="`!admin backup` - Manual backup\n`!admin cleanup` - Clean old files", 
                inline=False
            )
            
            # Add current status
            try:
                with open('version.txt', 'r') as f:
                    version = f.read().strip()
                embed.add_field(name="Current Version", value=f"`{version}`", inline=True)
            except:
                embed.add_field(name="Current Version", value="`unknown`", inline=True)
                
            embed.set_footer(text="KreciDJ Admin System")
            await ctx.send(embed=embed)

    @admin_commands.command(name="status")  # FIXED: Proper subcommand syntax
    async def status(self, ctx):
        """Comprehensive bot status with detailed metrics"""
        try:
            uptime = datetime.utcnow() - self.start_time
            
            embed = discord.Embed(
                title="🤖 Bot Status Dashboard",
                color=0x00ff00 if self.bot.is_ready() else 0xff0000,
                timestamp=datetime.utcnow()
            )
            
            # Basic Information
            status_emoji = "🟢" if self.bot.is_ready() else "🔴"
            latency_ms = round(self.bot.latency * 1000)
            latency_emoji = "🟢" if latency_ms < 100 else "🟡" if latency_ms < 300 else "🔴"
            
            embed.add_field(
                name="📊 Basic Status",
                value=f"{status_emoji} Status: {'Online' if self.bot.is_ready() else 'Offline'}\n"
                      f"⏱️ Uptime: {str(uptime).split('.')[0]}\n"
                      f"{latency_emoji} Latency: {latency_ms}ms\n"
                      f"🔄 Environment: {self.bot.config.ENVIRONMENT}",
                inline=True
            )
            
            # Server & User Information
            total_members = sum(guild.member_count or 0 for guild in self.bot.guilds)
            voice_connections = len(self.bot.voice_clients)
            
            embed.add_field(
                name="🏠 Server Info",
                value=f"🏛️ Guilds: {len(self.bot.guilds)}\n"
                      f"👥 Members: {total_members:,}\n"
                      f"🎵 Voice Connections: {voice_connections}\n"
                      f"📋 Commands Executed: {getattr(self.bot, 'commands_executed', 0)}",
                inline=True
            )
            
            # System Resources
            if PSUTIL_AVAILABLE and psutil is not None:
                try:
                    process = psutil.Process()
                    memory_mb = process.memory_info().rss / 1024 / 1024
                    cpu_percent = process.cpu_percent()
                    
                    memory_emoji = "🟢" if memory_mb < 200 else "🟡" if memory_mb < 500 else "🔴"
                    cpu_emoji = "🟢" if cpu_percent < 30 else "🟡" if cpu_percent < 70 else "🔴"
                    
                    embed.add_field(
                        name="⚙️ System Resources",
                        value=f"{memory_emoji} Memory: {memory_mb:.1f} MB\n"
                              f"{cpu_emoji} CPU: {cpu_percent:.1f}%\n"
                              f"🖥️ Platform: {os.name}\n"
                              f"🐍 Python: {'.'.join(map(str, __import__('sys').version_info[:2]))}",
                        inline=True
                    )
                except Exception as e:
                    embed.add_field(
                        name="⚙️ System Resources",
                        value=f"❌ Unable to get system info: {e}",
                        inline=True
                    )
            else:
                embed.add_field(
                    name="⚙️ System Resources",
                    value="❌ psutil not installed - install with 'pip install psutil'",
                    inline=True
                )
            
            # Lavalink Status - FIXED: Use wavelink.Pool instead of NodePool
            try:
                import wavelink
                # Check if Pool has nodes
                if hasattr(wavelink.Pool, 'nodes') and wavelink.Pool.nodes:
                    node_status = []
                    for node in wavelink.Pool.nodes.values():
                        status_emoji = "🟢" if node.status == wavelink.NodeStatus.CONNECTED else "🔴"
                        node_status.append(f"{status_emoji} {node.identifier}: {node.status.name}")
                    
                    embed.add_field(
                        name="🎵 Lavalink Nodes",
                        value="\n".join(node_status) or "No nodes connected",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="🎵 Lavalink Nodes",
                        value="❌ No Lavalink nodes connected",
                        inline=False
                    )
            except Exception as e:
                embed.add_field(
                    name="🎵 Lavalink Nodes",
                    value=f"❌ Error checking Lavalink: {e}",
                    inline=False
                )
            
            # Update Status
            if hasattr(self.bot, 'config') and getattr(self.bot.config, 'AUTO_UPDATE_ENABLED', False):
                update_emoji = "🔄" if self.update_available else "✅"
                last_check = self.last_update_check.strftime('%H:%M:%S') if self.last_update_check else 'Never'
                
                embed.add_field(
                    name="📦 Update Status",
                    value=f"{update_emoji} Updates: {'Available' if self.update_available else 'Current'}\n"
                          f"🕐 Last Check: {last_check}\n"
                          f"📍 Version: {self.get_current_version()}",
                    inline=False
                )
            
            embed.set_footer(text=f"Bot ID: {self.bot.user.id}")
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error generating status: {e}")
            logger.error(f"Status command error: {e}")

    @admin_commands.command(name="logs")  # FIXED: Proper subcommand syntax
    async def logs(self, ctx, lines: int = 20):
        """Show recent log entries with filtering options"""
        try:
            if lines > 100:
                lines = 100
                await ctx.send("⚠️ Maximum 100 lines allowed, showing last 100.")
            
            log_file = Path('logs/bot.log')
            if not log_file.exists():
                await ctx.send("❌ Log file not found. Logging to file might be disabled.")
                return
            
            # Read log file
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                recent_logs = all_lines[-lines:]
            
            if not recent_logs:
                await ctx.send("📋 Log file is empty.")
                return
            
            # Create log content with smart truncation
            log_content = ''.join(recent_logs)
            
            # Discord message limit handling
            max_length = 1900  # Leave room for embed formatting
            if len(log_content) > max_length:
                log_content = "...\n" + log_content[-(max_length-10):]
            
            # Count error/warning lines for summary
            error_count = sum(1 for line in recent_logs if '[ERROR]' in line)
            warning_count = sum(1 for line in recent_logs if '[WARNING]' in line)
            
            embed = discord.Embed(
                title=f"📋 Recent Logs ({lines} lines)",
                color=0xff0000 if error_count > 0 else 0xffaa00 if warning_count > 0 else 0x00ff00
            )
            
            embed.add_field(
                name="📊 Summary",
                value=f"❌ Errors: {error_count}\n⚠️ Warnings: {warning_count}",
                inline=True
            )
            
            embed.add_field(
                name="📝 Log Content",
                value=f"```\n{log_content}\n```",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error reading logs: {e}")
            logger.error(f"Logs command error: {e}")

    @admin_commands.command(name="health")  # FIXED: Proper subcommand syntax
    async def health(self, ctx):
        """Comprehensive health check with diagnostics"""
        embed = discord.Embed(
            title="🏥 Health Check Dashboard",
            color=0x00ff00,
            timestamp=datetime.utcnow()
        )
        
        checks = []
        overall_health = True
        
        # Discord API Health
        try:
            start_time = datetime.utcnow()
            await self.bot.fetch_user(self.bot.user.id)
            api_latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            if api_latency < 500:
                checks.append("🟢 Discord API: Healthy")
            else:
                checks.append(f"🟡 Discord API: Slow ({api_latency:.0f}ms)")
                overall_health = False
        except Exception as e:
            checks.append(f"🔴 Discord API: Failed - {e}")
            overall_health = False
        
        # Lavalink Health - FIXED: Use wavelink.Pool
        try:
            import wavelink
            if hasattr(wavelink.Pool, 'nodes') and wavelink.Pool.nodes:
                connected_nodes = sum(1 for node in wavelink.Pool.nodes.values() 
                                    if node.status == wavelink.NodeStatus.CONNECTED)
                total_nodes = len(wavelink.Pool.nodes)
                
                if connected_nodes > 0:
                    checks.append(f"🟢 Lavalink: {connected_nodes}/{total_nodes} nodes connected")
                else:
                    checks.append("🔴 Lavalink: No nodes connected")
                    overall_health = False
            else:
                checks.append("🔴 Lavalink: No nodes configured")
                overall_health = False
        except Exception as e:
            checks.append(f"🔴 Lavalink: Error - {e}")
            overall_health = False
        
        # Database Health
        try:
            db_path = Path(self.bot.config.DATABASE_FILE)
            if db_path.exists():
                db_size = db_path.stat().st_size / 1024  # KB
                checks.append(f"🟢 Database: Connected ({db_size:.1f} KB)")
            else:
                checks.append("🟡 Database: File not found (will be created)")
        except Exception as e:
            checks.append(f"🔴 Database: Error - {e}")
            overall_health = False
        
        # Memory Health
        if PSUTIL_AVAILABLE and psutil is not None:
            try:
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                
                if memory_mb < 300:
                    checks.append(f"🟢 Memory: Normal ({memory_mb:.1f} MB)")
                elif memory_mb < 600:
                    checks.append(f"🟡 Memory: High ({memory_mb:.1f} MB)")
                else:
                    checks.append(f"🔴 Memory: Critical ({memory_mb:.1f} MB)")
                    overall_health = False
            except Exception as e:
                checks.append(f"🔴 Memory: Error - {e}")
                overall_health = False
        else:
            checks.append("🟡 Memory: psutil not available")
        
        # Configuration Health
        try:
            self.bot.config.validate_config()
            checks.append("🟢 Configuration: Valid")
        except Exception as e:
            checks.append(f"🔴 Configuration: Invalid - {e}")
            overall_health = False
        
        # Overall Status
        status_emoji = "🟢" if overall_health else "🔴"
        embed.add_field(
            name=f"{status_emoji} Overall Health",
            value="All systems operational" if overall_health else "Issues detected",
            inline=False
        )
        
        # Individual Checks
        embed.add_field(
            name="🔍 System Checks",
            value="\n".join(checks),
            inline=False
        )
        
        # Recommendations
        if not overall_health:
            recommendations = []
            if any("Lavalink" in check and "🔴" in check for check in checks):
                recommendations.append("• Check Lavalink server connectivity")
            if any("Memory" in check and ("🔴" in check or "🟡" in check) for check in checks):
                recommendations.append("• Consider restarting bot to free memory")
            if any("Discord API" in check and "🔴" in check for check in checks):
                recommendations.append("• Check internet connection and Discord status")
            
            if recommendations:
                embed.add_field(
                    name="💡 Recommendations",
                    value="\n".join(recommendations),
                    inline=False
                )
        
        await ctx.send(embed=embed)

    @admin_commands.command(name="restart")  # FIXED: Proper subcommand syntax
    async def restart(self, ctx, *, reason: str = "Manual restart"):  # FIXED: Use * to capture full reason
        """Enhanced restart with graceful shutdown"""
        embed = discord.Embed(
            title="🔄 Bot Restart Initiated",
            description=f"Reason: {reason}",
            color=0xffaa00,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="⏱️ Restart Process",
            value="1. Notifying active channels\n2. Saving state\n3. Disconnecting voice clients\n4. Shutting down",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
        # Notify active voice channels
        notifications_sent = 0
        for voice_client in self.bot.voice_clients:
            try:
                if hasattr(voice_client, 'channel') and voice_client.channel:
                    restart_embed = discord.Embed(
                        title="🔄 Bot Restart",
                        description="Bot is restarting. Music will resume shortly after restart.",
                        color=0xffaa00
                    )
                    await voice_client.channel.send(embed=restart_embed)
                    notifications_sent += 1
            except Exception as e:
                logger.warning(f"Failed to notify channel: {e}")
        
        logger.info(f"Restart initiated by {ctx.author} ({ctx.author.id}). Reason: {reason}")
        logger.info(f"Notified {notifications_sent} voice channels")
        
        # Graceful shutdown delay
        await asyncio.sleep(3)
        
        # Close bot
        await self.bot.close()

    @admin_commands.command(name="backup")  # FIXED: Proper subcommand syntax
    async def backup(self, ctx):
        """Create comprehensive manual backup"""
        try:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            backup_dir = Path(f"backups/manual_{timestamp}")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            await ctx.send("💾 Creating backup...")
            
            # Files to backup
            backup_items = [
                ('.env', 'Environment configuration'),
                ('data/', 'Database and data files'),
                ('logs/bot.log', 'Current log file'),
                ('version.txt', 'Version information')
            ]
            
            backed_up = []
            errors = []
            
            import shutil
            
            for item_path, description in backup_items:
                try:
                    source = Path(item_path)
                    if source.exists():
                        dest = backup_dir / item_path
                        
                        if source.is_dir():
                            shutil.copytree(source, dest)
                        else:
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(source, dest)
                        
                        backed_up.append(f"✅ {description}")
                    else:
                        backed_up.append(f"⚠️ {description} (not found)")
                except Exception as e:
                    errors.append(f"❌ {description}: {e}")
            
            # Create backup info file
            backup_info = {
                'timestamp': timestamp,
                'bot_version': self.get_current_version(),
                'environment': self.bot.config.ENVIRONMENT,
                'backed_up_items': backup_items,
                'errors': errors
            }
            
            with open(backup_dir / 'backup_info.json', 'w') as f:
                json.dump(backup_info, f, indent=2)
            
            # Calculate backup size
            total_size = sum(f.stat().st_size for f in backup_dir.rglob('*') if f.is_file())
            size_mb = total_size / 1024 / 1024
            
            embed = discord.Embed(
                title="💾 Backup Complete",
                color=0x00ff00 if not errors else 0xffaa00
            )
            
            embed.add_field(
                name="📍 Backup Location",
                value=f"`{backup_dir}`",
                inline=False
            )
            
            embed.add_field(
                name="📊 Backup Details",
                value=f"Size: {size_mb:.2f} MB\nTimestamp: {timestamp}",
                inline=True
            )
            
            embed.add_field(
                name="📋 Items Backed Up",
                value="\n".join(backed_up[:10]),  # Limit display
                inline=False
            )
            
            if errors:
                embed.add_field(
                    name="⚠️ Errors",
                    value="\n".join(errors[:5]),  # Limit display
                    inline=False
                )
            
            await ctx.send(embed=embed)
            logger.info(f"Manual backup created by {ctx.author}: {backup_dir}")
            
        except Exception as e:
            await ctx.send(f"❌ Backup failed: {e}")
            logger.error(f"Backup command error: {e}")

    @admin_commands.command(name="performance")  # FIXED: Proper subcommand syntax
    async def performance(self, ctx):
        """Show detailed performance metrics"""
        try:
            embed = discord.Embed(
                title="📊 Performance Metrics",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            
            # System metrics
            if PSUTIL_AVAILABLE and psutil is not None:
                try:
                    process = psutil.Process()
                    
                    # Memory details
                    memory_info = process.memory_info()
                    memory_mb = memory_info.rss / 1024 / 1024
                    memory_percent = process.memory_percent()
                    
                    # CPU details
                    cpu_percent = process.cpu_percent(interval=1)
                    cpu_times = process.cpu_times()
                    
                    # Disk I/O
                    io_counters = process.io_counters()
                    
                    embed.add_field(
                        name="💾 Memory Usage",
                        value=f"RSS: {memory_mb:.1f} MB\n"
                              f"Percent: {memory_percent:.1f}%\n"
                              f"VMS: {memory_info.vms / 1024 / 1024:.1f} MB",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="⚡ CPU Usage",
                        value=f"Current: {cpu_percent:.1f}%\n"
                              f"User time: {cpu_times.user:.1f}s\n"
                              f"System time: {cpu_times.system:.1f}s",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="💿 Disk I/O",
                        value=f"Read: {io_counters.read_bytes / 1024 / 1024:.1f} MB\n"
                              f"Write: {io_counters.write_bytes / 1024 / 1024:.1f} MB",
                        inline=True
                    )
                    
                except Exception as e:
                    embed.add_field(
                        name="❌ System Metrics Error",
                        value=str(e),
                        inline=False
                    )
            else:
                embed.add_field(
                    name="❌ System Metrics",
                    value="psutil not installed - install with 'pip install psutil'",
                    inline=False
                )
            
            # Bot-specific metrics
            uptime = datetime.utcnow() - self.start_time
            uptime_hours = uptime.total_seconds() / 3600
            
            commands_executed = getattr(self.bot, 'commands_executed', 0)
            commands_per_hour = commands_executed / max(uptime_hours, 1)
            
            embed.add_field(
                name="🤖 Bot Metrics",
                value=f"Uptime: {str(uptime).split('.')[0]}\n"
                      f"Commands: {commands_executed}\n"
                      f"Rate: {commands_per_hour:.1f}/hour",
                inline=True
            )
            
            # Network metrics
            embed.add_field(
                name="🌐 Network",
                value=f"Latency: {round(self.bot.latency * 1000)}ms\n"
                      f"Guilds: {len(self.bot.guilds)}\n"
                      f"Voice: {len(self.bot.voice_clients)}",
                inline=True
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error getting performance metrics: {e}")

    @tasks.loop(minutes=10)
    async def update_checker(self):
        """Periodic update checker for production environment"""
        if not hasattr(self.bot, 'config') or not getattr(self.bot.config, 'AUTO_UPDATE_ENABLED', False):
            return
        
        try:
            await self.check_for_updates()
        except Exception as e:
            logger.error(f"Update checker error: {e}")

    async def check_for_updates(self):
        """Check GitHub for updates"""
        if not hasattr(self.bot, 'config') or not getattr(self.bot.config, 'GITHUB_REPO', None):
            return
        
        try:
            url = f"https://api.github.com/repos/{self.bot.config.GITHUB_REPO}/commits/{self.bot.config.GITHUB_BRANCH}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        latest_commit = data['sha'][:7]
                        current_commit = self.get_current_version()
                        
                        self.last_update_check = datetime.utcnow()
                        
                        if latest_commit != current_commit:
                            self.update_available = True
                            self.latest_version = latest_commit
                            await self.notify_owner_update(data)
                        else:
                            self.update_available = False
                            
        except Exception as e:
            logger.warning(f"Update check failed: {e}")

    async def notify_owner_update(self, commit_data):
        """Notify bot owner about available update"""
        try:
            owner = self.bot.get_user(self.bot.owner_id) if hasattr(self.bot, 'owner_id') else None
            if not owner:
                return
            
            embed = discord.Embed(
                title="🔄 Update Available",
                color=0x00ff00
            )
            
            commit_msg = commit_data.get('commit', {}).get('message', 'No message')[:200]
            embed.add_field(
                name="📦 New Version",
                value=f"Commit: `{self.latest_version}`\nMessage: {commit_msg}",
                inline=False
            )
            
            embed.add_field(
                name="🚀 Update Command",
                value="`!admin update` to apply update",
                inline=False
            )
            
            await owner.send(embed=embed)
            logger.info(f"Notified owner about update: {self.latest_version}")
            
        except Exception as e:
            logger.error(f"Failed to notify owner about update: {e}")

    def get_current_version(self):
        """Get current version from version.txt or git"""
        try:
            version_file = Path('version.txt')
            if version_file.exists():
                with open(version_file) as f:
                    return f.read().strip().split('\n')[0]
            
            # Fallback to git
            result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], 
                                  capture_output=True, text=True)
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except:
            return "unknown"


async def setup(bot):
    """Setup function for discord.py 2.0+ cog loading"""
    await bot.add_cog(OwnerCommands(bot))

def setup_owner_commands(bot):
    """Backward compatibility setup function"""
    return asyncio.create_task(setup(bot))