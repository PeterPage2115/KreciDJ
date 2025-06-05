"""Enhanced Discord Music Bot with comprehensive features"""

import discord
from discord.ext import commands, tasks
import wavelink
import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
import traceback
import signal
import aiohttp

# Import configurations and utilities
from config import Config

# Import health monitoring
from health.monitor import health_monitor

# FIXED: Simple logger setup instead of importing
def setup_logger(environment):
    """Simple logger setup"""
    logger = logging.getLogger('discord_bot')
    logger.setLevel(logging.DEBUG if environment == 'development' else logging.INFO)
    
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

# FIXED: Simple error handler instead of importing
class SimpleErrorHandler:
    """Simple error handler"""
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
    
    async def handle_command_error(self, ctx, error):
        """Handle command errors"""
        try:
            if isinstance(error, commands.CommandNotFound):
                return  # Ignore unknown commands
            
            elif isinstance(error, commands.MissingRequiredArgument):
                await ctx.send(f"❌ Brakuje argumentu: `{error.param.name}`")
            
            elif isinstance(error, commands.CommandOnCooldown):
                await ctx.send(f"⏳ Komenda w cooldown! Spróbuj za {error.retry_after:.1f}s")
            
            elif isinstance(error, commands.CheckFailure):
                await ctx.send("❌ Nie masz uprawnień do tej komendy!")
            
            else:
                self.logger.error(f"Command error: {error}")
                await ctx.send(f"❌ Wystąpił błąd: {str(error)}")
        
        except Exception as e:
            self.logger.error(f"Error in error handler: {e}")

class MuzycznyBot(commands.Bot):
    """Enhanced Discord Music Bot"""
    
    def __init__(self):
        # Configuration
        config = Config()
        
        # Setup intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        intents.guilds = True
        
        # Initialize bot
        super().__init__(
            command_prefix=config.COMMAND_PREFIX,
            intents=intents,
            help_command=None,
            case_insensitive=True,
            strip_after_prefix=True
        )
        
        # Bot properties
        self.config = config
        self.start_time = datetime.now(timezone.utc)
        self.commands_executed = 0
        self.last_error = None
        
        # Setup logging
        self.logger = setup_logger(config.ENVIRONMENT)
        
        # Setup error handler
        self.error_handler = SimpleErrorHandler(self)
        
        # Lavalink setup flag
        self._lavalink_setup = False
        
    async def setup_hook(self):
        """Setup hook called when bot is starting"""
        try:
            self.logger.info("🚀 Setting up bot...")
            
            # Setup Lavalink
            await self.setup_lavalink()
            
            # Load cogs
            await self.load_extensions()
            
            # Start background tasks
            self.start_background_tasks()
            
            self.logger.info("✅ Bot setup completed successfully!")
            
        except Exception as e:
            self.logger.error(f"❌ Setup failed: {e}")
            self.logger.error(traceback.format_exc())
            await self.close()
    
    async def setup_lavalink(self):
        """Setup Lavalink connection"""
        try:
            if self._lavalink_setup:
                return
                
            self.logger.info("🎵 Setting up Lavalink connection...")
            
            # Build node configuration
            node_config = {
                'identifier': 'MAIN',
                'host': self.config.LAVALINK_HOST,
                'port': self.config.LAVALINK_PORT,
                'password': self.config.LAVALINK_PASSWORD,
                'https': getattr(self.config, 'LAVALINK_HTTPS', False),
                'heartbeat': 30,
                'retries': 3
            }
            
            # Create and connect node
            node = wavelink.Node(
                uri=f"{'https' if node_config['https'] else 'http'}://{node_config['host']}:{node_config['port']}",
                password=node_config['password']
            )
            
            await wavelink.Pool.connect(nodes=[node], client=self)
            
            self.logger.info(f"✅ Connected to Lavalink: {node_config['host']}:{node_config['port']}")
            self._lavalink_setup = True
            
        except Exception as e:
            self.logger.error(f"❌ Lavalink setup failed: {e}")
            raise
    
    async def load_extensions(self):
        """Load all bot extensions/cogs"""
        try:
            self.logger.info("📦 Loading extensions...")
            
            # Load music commands cog
            from commands.music import MusicCommands
            await self.add_cog(MusicCommands(self))
            self.logger.info("✅ Loaded: MusicCommands")
            
            # Load utility commands
            try:
                from commands.utils import UtilityCommands
                await self.add_cog(UtilityCommands(self))
                self.logger.info("✅ Loaded: UtilityCommands")
            except ImportError as e:
                self.logger.info(f"ℹ️ UtilityCommands not available: {e}")
            except Exception as e:
                self.logger.warning(f"⚠️ Could not load UtilityCommands: {e}")
            
            # Load owner commands
            try:
                from commands.owner_commands import OwnerCommands
                await self.add_cog(OwnerCommands(self))
                self.logger.info("✅ Loaded: OwnerCommands")
            except ImportError as e:
                self.logger.info(f"ℹ️ OwnerCommands not available: {e}")
            except Exception as e:
                self.logger.warning(f"⚠️ Could not load OwnerCommands: {e}")
        
        except Exception as e:
            self.logger.error(f"❌ Failed to load extensions: {e}")
            self.logger.error(traceback.format_exc())
            raise
    
    def start_background_tasks(self):
        """Start background tasks"""
        try:
            # Start command statistics task
            if not hasattr(self, '_stats_task_started'):
                self.update_stats_task.start()
                self._stats_task_started = True
                self.logger.info("✅ Started background tasks")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to start background tasks: {e}")
    
    @tasks.loop(minutes=5)
    async def update_stats_task(self):
        """Update bot statistics periodically"""
        try:
            # Log basic stats
            stats = {
                'guilds': len(self.guilds),
                'users': len(self.users),
                'voice_clients': len(self.voice_clients),
                'commands_executed': self.commands_executed,
                'uptime': str(datetime.now(timezone.utc) - self.start_time).split('.')[0]
            }
            
            self.logger.info(f"📊 Bot stats: {stats}")
            
        except Exception as e:
            self.logger.error(f"Stats update error: {e}")
    
    @update_stats_task.before_loop
    async def before_stats_task(self):
        """Wait for bot to be ready before starting stats task"""
        await self.wait_until_ready()
    
    async def on_ready(self):
        """Called when bot is ready"""
        try:
            self.logger.info("=" * 50)
            self.logger.info("🎵 MUZYCZNY BOT DISCORD - READY!")
            self.logger.info("=" * 50)
            self.logger.info(f"Bot: {self.user} (ID: {self.user.id if self.user else 'Unknown'})")
            self.logger.info(f"Servers: {len(self.guilds)}")
            self.logger.info(f"Users: {len(self.users)}")
            self.logger.info(f"Command Prefix: {self.command_prefix}")
            self.logger.info(f"Environment: {self.config.ENVIRONMENT}")
            
            # Update presence
            activity = discord.Activity(
                type=discord.ActivityType.listening,
                name=f"{self.command_prefix}help | {len(self.guilds)} servers"
            )
            await self.change_presence(activity=activity, status=discord.Status.online)
            
            self.logger.info("✅ Bot is ready and online!")
            
            # Setup monitoring
            await self.setup_monitoring()
            
        except Exception as e:
            self.logger.error(f"Error in on_ready: {e}")
    
    async def setup_monitoring(self):
        """Setup monitoring systems"""
        # Set bot instance for health monitoring
        health_monitor.set_bot_instance(self)
        
        # Start health server
        success = health_monitor.start()
        if success:
            self.logger.info("✅ Health monitoring started")
        else:
            self.logger.warning("⚠️ Health monitoring failed to start")
    
    async def on_guild_join(self, guild):
        """Called when bot joins a guild"""
        self.logger.info(f"🔗 Joined guild: {guild.name} (ID: {guild.id})")
        
        # Update presence
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name=f"{self.command_prefix}help | {len(self.guilds)} servers"
        )
        await self.change_presence(activity=activity)
    
    async def on_guild_remove(self, guild):
        """Called when bot leaves a guild"""
        self.logger.info(f"📤 Left guild: {guild.name} (ID: {guild.id})")
        
        # Update presence
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name=f"{self.command_prefix}help | {len(self.guilds)} servers"
        )
        await self.change_presence(activity=activity)
    
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload):
        """Called when Lavalink node is ready"""
        self.logger.info(f"🎵 Lavalink node ready: {payload.node.identifier}")
    
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        """Called when track starts playing"""
        # FIXED: Remove all problematic player method calls
        # These methods don't exist in standard wavelink Player
        # They will be implemented in our custom Player class in music.py
        try:
            self.logger.info(f"🎵 Started playing: {payload.track.title}")
        except Exception as e:
            self.logger.error(f"Track start event error: {e}")
    
    async def on_command_error(self, ctx, error):
        """Global command error handler"""
        await self.error_handler.handle_command_error(ctx, error)
    
    async def on_error(self, event, *args, **kwargs):
        """Global error handler"""
        try:
            self.logger.error(f"Event error: {event}")
            if args:
                self.logger.error(f"Args: {args}")
            if kwargs:
                self.logger.error(f"Kwargs: {kwargs}")
        except Exception as e:
            print(f"Error in error handler: {e}")
    
    async def on_command(self, ctx):
        """Called before every command"""
        self.commands_executed += 1
        
        # FIXED: Safe guild name access
        guild_name = ctx.guild.name if ctx.guild else 'DM'
        self.logger.info(f"Command: {ctx.command.name} by {ctx.author} in {guild_name}")
    
    async def close(self):
        """Enhanced close with cleanup"""
        try:
            self.logger.info("🔄 Shutting down bot...")
            
            # Cancel background tasks
            if hasattr(self, 'update_stats_task'):
                self.update_stats_task.cancel()
            
            # FIXED: Simple voice client disconnect without problematic method calls
            for voice_client in list(self.voice_clients):
                try:
                    # Simple disconnect - no custom cleanup methods
                    await voice_client.disconnect(force=True)
                except Exception as e:
                    self.logger.error(f"Error disconnecting voice client: {e}")
            
            # FIXED: Simple Lavalink cleanup - no problematic method calls
            try:
                # Just clear the nodes - let the library handle cleanup
                if hasattr(wavelink, 'Pool') and hasattr(wavelink.Pool, 'nodes'):
                    # Clear nodes without calling disconnect/close
                    # The library will handle cleanup during bot shutdown
                    pass
            except Exception as e:
                self.logger.debug(f"Lavalink cleanup: {e}")
            
            await super().close()
            self.logger.info("✅ Bot shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

# FIXED: Proper async setup
async def main():
    """Main bot runner with proper async handling"""
    # Validate configuration first
    config = Config()
    config.validate_config()
    
    # Create bot instance
    bot = MuzycznyBot()
    
    # Setup graceful shutdown
    def signal_handler(sig, frame):
        print("\n🔄 Shutting down gracefully...")
        if hasattr(bot, 'loop') and bot.loop:
            bot.loop.create_task(bot.close())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start bot
        async with bot:
            await bot.start(config.get_discord_token())
            
    except KeyboardInterrupt:
        print("\n🔄 KeyboardInterrupt received, shutting down...")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        traceback.print_exc()
    finally:
        if not bot.is_closed():
            await bot.close()

if __name__ == "__main__":
    print("🔍 Validating bot configuration...")
    try:
        # This will validate and show config
        config = Config()
        config.validate_config()
        
        print("🚀 Starting Discord Music Bot...")
        
        # Run the bot properly
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
        traceback.print_exc()
        sys.exit(1)