"""Enhanced music commands with auto-disconnect, rate limiting, and queue limits"""

import discord
from discord.ext import commands, tasks
import wavelink
import asyncio
import logging
import re
import random
from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Any

# Import formatters z utils
from utils.formatters import (
    format_duration, 
    format_progress_bar, 
    truncate_string,
    create_music_embed,
    format_track_info
)

# Import controls view
try:
    from views.controls import MusicControlsView
    _has_imported_view = True
except ImportError:
    _has_imported_view = False
    MusicControlsView = None

class FallbackMusicControlsView(discord.ui.View):
    def __init__(self, player, timeout: Optional[int] = 300):
        super().__init__(timeout=timeout)
        self.player = player
        self.message: Optional[discord.Message] = None

if _has_imported_view and MusicControlsView:
    MusicControlsViewType = MusicControlsView
else:
    MusicControlsViewType = FallbackMusicControlsView

logger = logging.getLogger('discord_bot')


class MusicPlayer(wavelink.Player):
    """Enhanced music player with auto-disconnect and advanced features"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Enhanced properties
        self.queue = wavelink.Queue()
        self.loop_mode = "off"
        self.last_activity = datetime.now(timezone.utc)
        self.current_message: Optional[discord.Message] = None
        self.auto_disconnect_task: Optional[asyncio.Task] = None
        self.inactive_timeout = 300
        
        # Persistent panel
        self.music_channel: Optional[discord.TextChannel] = None
        self.persistent_panel: Optional[discord.Message] = None
        
        # Queue limits
        self.max_queue_size = 50
        self.max_track_duration = 1800
        
        self.logger = logger
        self.start_auto_disconnect_timer()
    
    async def setup_persistent_panel(self, channel: discord.TextChannel):
        """Setup persistent music panel in specific channel"""
        try:
            self.music_channel = channel
            
            # Sprawdź czy już istnieje panel
            async for message in channel.history(limit=50):
                if (message.author == channel.guild.me and 
                    message.embeds and 
                    message.embeds[0].title and
                    "Music Control Panel" in message.embeds[0].title):
                    # Usuń stary panel
                    try:
                        await message.delete()
                    except:
                        pass
            
            embed = discord.Embed(
                title="🎵 Music Control Panel",
                description="Use buttons below to control music playback",
                color=0x00ff00
            )
            embed.add_field(name="Status", value="Ready", inline=True)
            embed.add_field(name="Queue", value="Empty", inline=True)
            embed.add_field(name="Volume", value="100%", inline=True)
            
            view = MusicControlsViewType(self, timeout=None)
            
            # Wyślij i od razu przypnij
            self.persistent_panel = await channel.send(embed=embed, view=view)
            
            # FIXED: Przypnij wiadomość żeby nie znikała
            try:
                await self.persistent_panel.pin()
            except discord.Forbidden:
                # Brak uprawnień do przypinania
                pass
            except discord.HTTPException:
                # Limit pinned messages
                pass
            
            if hasattr(view, 'message'):
                view.message = self.persistent_panel
            
            return self.persistent_panel
            
        except Exception as e:
            self.logger.error(f"Failed to setup persistent panel: {e}")
            return None
    
    async def update_persistent_panel(self):
        """Update the persistent panel with current info"""
        try:
            if not self.persistent_panel or not self.music_channel:
                return
            
            embed = discord.Embed(
                title="🎵 Music Control Panel",
                color=0x00ff00 if self.playing else 0xff9900
            )
            
            if self.current:
                embed.description = f"**Now Playing:** [{self.current.title}]({self.current.uri})"
                
                if hasattr(self.current, 'author') and self.current.author:
                    embed.add_field(name="👤 Artist", value=self.current.author, inline=True)
                
                if hasattr(self.current, 'length') and self.current.length:
                    duration = format_duration(self.current.length)
                    embed.add_field(name="⏱️ Duration", value=duration, inline=True)
                
                requester = getattr(self.current, 'requester', None)
                if requester:
                    embed.add_field(name="🎧 Requested by", value=requester.mention, inline=True)
                
                if hasattr(self.current, 'artwork') and self.current.artwork:
                    embed.set_thumbnail(url=self.current.artwork)
            else:
                embed.description = "No track currently playing"
            
            status = "🔴 Stopped"
            if self.playing:
                status = "▶️ Playing"
            elif self.paused:
                status = "⏸️ Paused"
            
            embed.add_field(name="Status", value=status, inline=True)
            embed.add_field(name="🔊 Volume", value=f"{self.volume}%", inline=True)
            embed.add_field(name="📋 Queue", value=f"{len(self.queue)} tracks", inline=True)
            embed.add_field(name="🔁 Loop", value=self.loop_mode.title(), inline=True)
            
            embed.set_footer(text=f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
            
            await self.persistent_panel.edit(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Failed to update persistent panel: {e}")

    def start_auto_disconnect_timer(self):
        """Start the auto-disconnect timer"""
        if self.auto_disconnect_task:
            self.auto_disconnect_task.cancel()
        
        self.auto_disconnect_task = asyncio.create_task(self._auto_disconnect_handler())
    
    async def _auto_disconnect_handler(self):
        """Handle auto-disconnect after inactivity"""
        try:
            while True:
                await asyncio.sleep(60)  # Check every minute
                
                time_since_activity = (datetime.now(timezone.utc) - self.last_activity).total_seconds()
                
                if self.inactive_timeout is not None and time_since_activity >= self.inactive_timeout:
                    if not self.playing and not self.paused:
                        await self.disconnect()
                        break
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Auto-disconnect handler error: {e}")
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now(timezone.utc)
    
    async def cleanup_resources(self):
        """Cleanup player resources"""
        try:
            if self.auto_disconnect_task:
                self.auto_disconnect_task.cancel()
            
            if self.current_message:
                try:
                    await self.current_message.delete()
                except:
                    pass
                
        except Exception as e:
            self.logger.error(f"Player cleanup error: {e}")
    
    async def play_next(self):
        """Play next track with loop handling"""
        try:
            if self.loop_mode == "track" and self.current:
                await self.play(self.current)
                return
            
            if self.queue.is_empty:
                if hasattr(self, 'update_persistent_panel'):
                    await self.update_persistent_panel()
                return
            else:
                next_track = await self.queue.get_wait()
                await self.play(next_track)
                
                if hasattr(self, 'update_persistent_panel'):
                    await self.update_persistent_panel()
                
        except Exception as e:
            self.logger.error(f"Play next error: {e}")
    
    async def add_track(self, track: wavelink.Playable, requester: discord.Member):
        """Add track with validation and limits"""
        queue_count = len(self.queue) if hasattr(self.queue, '__len__') else 0
        if queue_count >= self.max_queue_size:
            raise commands.CommandError(f"Kolejka jest pełna! Maksymalnie {self.max_queue_size} utworów.")
        
        track_length = getattr(track, 'length', None)
        if track_length is not None and isinstance(track_length, (int, float)) and track_length >= (self.max_track_duration * 1000):
            max_duration_str = format_duration(self.max_track_duration * 1000)
            raise commands.CommandError(f"Utwór jest za długi! Maksymalnie {max_duration_str}.")
        
        setattr(track, 'requester', requester)
        await self.queue.put_wait(track)
        
        if not hasattr(self, '_original_queue'):
            self._original_queue = []
        self._original_queue.append(track)
        
        self.update_activity()
        return True


class MusicCommands(commands.Cog):
    """Enhanced music commands with comprehensive features"""
    
    def __init__(self, bot):
        self.bot = bot
        self.url_regex = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
    
    async def cog_before_invoke(self, ctx):
        """Pre-command checks - ONLY command counter"""
        # Update command count
        if not hasattr(self.bot, 'commands_executed'):
            self.bot.commands_executed = 0
        self.bot.commands_executed += 1

    @commands.command(name='play', aliases=['p'])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def play(self, ctx, *, search: str):
        """Play a track - bot auto-joins voice channel"""
        async with ctx.typing():
            try:
                # STEP 1: Sprawdź czy user jest na voice
                if not isinstance(ctx.author, discord.Member) or not ctx.author.voice or not ctx.author.voice.channel:
                    return await ctx.send("❌ Musisz być na kanale głosowym!")
                
                # STEP 2: Połącz bota jeśli nie jest połączony
                if not ctx.guild.voice_client:
                    channel = ctx.author.voice.channel
                    player = await channel.connect(cls=MusicPlayer)
                    
                    # Utwórz persistent panel
                    await player.setup_persistent_panel(ctx.channel)
                    
                    await ctx.send(f"🔗 **Połączono z {channel.name}**")
                else:
                    player = ctx.guild.voice_client
                
                # STEP 3: Wyszukaj utwór
                tracks = await wavelink.Playable.search(search)
                if not tracks:
                    return await ctx.send("❌ Nie znaleziono utworów!")
                
                track = tracks[0]
                
                # STEP 4: Dodaj do kolejki
                await player.add_track(track, ctx.author)
                
                # STEP 5: Uruchom jeśli nic nie gra
                if not player.playing and not player.paused:
                    await player.play(track)
                    await ctx.send(f"🎵 **Teraz gra:** {track.title}")
                else:
                    await ctx.send(f"📋 **Dodano do kolejki:** {track.title}")
                
                # STEP 6: Aktualizuj panel
                if hasattr(player, 'update_persistent_panel'):
                    await player.update_persistent_panel()
                
            except Exception as e:
                await ctx.send(f"❌ Błąd: {e}")

    @commands.command(name='pause')
    @commands.cooldown(1, 2, commands.BucketType.guild)
    async def pause(self, ctx):
        """Pause the current track"""
        player = ctx.guild.voice_client
        if not player:
            return await ctx.send("❌ Not connected to voice!", )
        
        if player.playing:
            await player.pause(True)
            player.update_activity()
            await ctx.send("⏸️ Paused")
            if hasattr(player, 'update_persistent_panel'):
                await player.update_persistent_panel()
        else:
            await ctx.send("❌ Nothing is playing!", )

    @commands.command(name='resume')
    @commands.cooldown(1, 2, commands.BucketType.guild)
    async def resume(self, ctx):
        """Resume the current track"""
        player = ctx.guild.voice_client
        if not player:
            return await ctx.send("❌ Not connected to voice!", )
        
        if player.paused:
            await player.pause(False)
            player.update_activity()
            await ctx.send("▶️ Resumed", )
            if hasattr(player, 'update_persistent_panel'):
                await player.update_persistent_panel()
        else:
            await ctx.send("❌ Nothing is paused!", )

    @commands.command(name='volume', aliases=['vol'])
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def volume(self, ctx, volume: Optional[int] = None):
        """Control player volume"""
        player = ctx.guild.voice_client
        if not player:
            return await ctx.send("❌ Not connected to voice!", )
        
        if volume is None:
            return await ctx.send(f"🔊 Current volume: **{player.volume}%**", )
        
        if volume < 0 or volume > 100:
            return await ctx.send("❌ Volume must be between 0-100!", )
        
        await player.set_volume(volume)
        player.update_activity()
        
        emoji = "🔇" if volume == 0 else "🔈" if volume <= 30 else "🔉" if volume <= 70 else "🔊"
        await ctx.send(f"{emoji} Volume set to **{volume}%**", )
        
        if hasattr(player, 'update_persistent_panel'):
            await player.update_persistent_panel()

    @commands.command(name='join', aliases=['connect'])
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def join(self, ctx, *, channel: Optional[Union[discord.VoiceChannel, discord.StageChannel]] = None):
        """Join a voice channel"""
        if not channel:
            if not ctx.author.voice:
                raise commands.CommandError("Musisz być na kanale głosowym lub podać kanał!")
            channel = ctx.author.voice.channel
        
        if not channel:
            raise commands.CommandError("Nie można znaleźć kanału głosowego!")
        
        if ctx.guild.voice_client:
            await ctx.guild.voice_client.move_to(channel)
        else:
            await channel.connect(cls=MusicPlayer)
        
        embed = create_music_embed("🔗 Połączono", f"Dołączono do **{channel.name}**")
        await ctx.send(embed=embed, )

    @commands.command(name='stop')
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def stop(self, ctx):
        """Stop playback and clear queue"""
        player = ctx.guild.voice_client
        if not player:
            return await ctx.send("❌ Not connected to voice!", )
        
        player.queue.clear()
        if hasattr(player, '_original_queue'):
            player._original_queue.clear()
        
        await player.stop()
        player.update_activity()
        
        await ctx.send("⏹️ Stopped and cleared queue", )
        
        if hasattr(player, 'update_persistent_panel'):
            await player.update_persistent_panel()

    @commands.command(name='skip', aliases=['next'])
    @commands.cooldown(1, 2, commands.BucketType.guild)
    async def skip(self, ctx):
        """Skip the current track"""
        player = ctx.guild.voice_client
        if not player:
            return await ctx.send("❌ Not connected to voice!", )
        
        if not player.playing and not player.paused:
            return await ctx.send("❌ Nothing is playing!", )
        
        current_track = player.current
        await player.stop()
        player.update_activity()
        
        title = getattr(current_track, 'title', 'Unknown Track') if current_track else 'Unknown Track'
        await ctx.send(f"⏭️ Skipped: **{title}**", )

    @commands.command(name='queue', aliases=['q'])
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def queue(self, ctx):
        """Show queue"""
        player = ctx.guild.voice_client
        if not player:
            return await ctx.send("❌ Not connected to voice!", )
        
        if not player.queue:
            return await ctx.send("📋 Queue is empty", )
        
        embed = create_music_embed("📋 Queue")
        
        queue_list = []
        for i, track in enumerate(list(player.queue)[:10], 1):
            queue_list.append(f"{i}. {track.title}")
        
        embed.description = "\n".join(queue_list)
        
        if len(player.queue) > 10:
            embed.set_footer(text=f"Showing 10/{len(player.queue)} tracks")
        
        await ctx.send(embed=embed)

    @commands.command(name='nowplaying', aliases=['np', 'current'])
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def nowplaying(self, ctx):
        """Show information about the currently playing track"""
        player = ctx.guild.voice_client
        if not player:
            return await ctx.send("❌ Not connected to voice!", )
        
        if not player.current:
            return await ctx.send("❌ Nothing is playing!", )
        
        track = player.current
        embed = create_music_embed("🎵 Now Playing", f"**[{track.title}]({track.uri})**")
        
        if hasattr(track, 'author') and track.author:
            embed.add_field(name="👤 Artist", value=track.author, inline=True)
        
        if hasattr(track, 'length') and track.length:
            duration = format_duration(track.length)
            embed.add_field(name="⏱️ Duration", value=duration, inline=True)
        
        embed.add_field(name="🔊 Volume", value=f"{player.volume}%", inline=True)
        
        if hasattr(track, 'artwork') and track.artwork:
            embed.set_thumbnail(url=track.artwork)
        
        requester = getattr(track, 'requester', None)
        if requester:
            embed.set_footer(text=f"Requested by {requester.display_name}")
        
        await ctx.send(embed=embed)

    @commands.command(name='shuffle')
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def shuffle(self, ctx):
        """Shuffle the current queue"""
        player = ctx.guild.voice_client
        if not player:
            return await ctx.send("❌ Not connected to voice!", )
        
        queue_count = len(player.queue) if hasattr(player.queue, '__len__') else 0
        if queue_count < 2:
            return await ctx.send("❌ Need at least 2 tracks to shuffle!", )
        
        tracks_list = list(player.queue)
        random.shuffle(tracks_list)
        
        player.queue.clear()
        for track in tracks_list:
            await player.queue.put_wait(track)
        
        player.update_activity()
        
        embed = create_music_embed("🔀 Queue Shuffled", f"Shuffled {len(tracks_list)} tracks")
        await ctx.send(embed=embed, )

    @commands.command(name='setup_music')
    @commands.has_permissions(manage_channels=True)
    async def setup_music(self, ctx):
        """Setup dedicated music channel with persistent controls"""
        try:
            music_channel = discord.utils.get(ctx.guild.text_channels, name='🎵-music-controls')
            
            if music_channel:
                await ctx.send(f"Music channel already exists: {music_channel.mention}")
                return
            
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(
                    send_messages=False,
                    add_reactions=True
                ),
                ctx.guild.me: discord.PermissionOverwrite(
                    send_messages=True,
                    manage_messages=True,
                    embed_links=True,
                    use_external_emojis=True
                )
            }
            
            music_channel = await ctx.guild.create_text_channel(
                '🎵-music-controls',
                overwrites=overwrites,
                topic='Music control panel - Use buttons to control playback',
                position=0
            )
            
            if ctx.guild.voice_client:
                player = ctx.guild.voice_client
                if isinstance(player, MusicPlayer):
                    await player.setup_persistent_panel(music_channel)
            
            await ctx.send(f"✅ Created music channel: {music_channel.mention}")
            
        except Exception as e:
            await ctx.send(f"❌ Failed to setup music channel: {e}")

    # DODAJ NOWĄ KOMENDĘ do ręcznego tworzenia panelu:

    @commands.command(name='music_panel', aliases=['panel'])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def music_panel(self, ctx):
        """Create/refresh music control panel"""
        try:
            # Sprawdź czy bot jest połączony
            if not ctx.guild.voice_client:
                # Utwórz placeholder panel
                embed = discord.Embed(
                    title="🎵 Music Control Panel",
                    description="Use `?play <song>` to start music",
                    color=0xff9900
                )
                embed.add_field(name="Status", value="Not connected", inline=True)
                embed.add_field(name="Queue", value="Empty", inline=True)
                embed.add_field(name="Volume", value="100%", inline=True)
                
                view = MusicControlsViewType(None, timeout=None)
                # Usuń stare panele
                async for message in ctx.channel.history(limit=50):
                    if (message.author == ctx.guild.me and 
                        message.embeds and 
                        message.embeds[0].title and
                        "Music Control Panel" in message.embeds[0].title):
                        try:
                            await message.delete()
                        except:
                            pass
                            pass
                
                # Wyślij nowy panel
                panel = await ctx.send(embed=embed, view=view)
                
                try:
                    await panel.pin()
                except:
                    pass
                
                await ctx.send("✅ Created music panel! Use `?play` to connect.", )
            else:
                # Bot jest połączony - odśwież istniejący panel
                player = ctx.guild.voice_client
                if isinstance(player, MusicPlayer):
                    await player.setup_persistent_panel(ctx.channel)
                    await ctx.send("✅ Refreshed music panel!", )
                
        except Exception as e:
            await ctx.send(f"❌ Error creating panel: {e}", )

    # Wavelink events
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        """Handle track end events"""
        player = payload.player
        
        try:
            if isinstance(player, MusicPlayer):
                await player.play_next()
        except Exception as e:
            logger.error(f"Track end error: {e}")

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        """Handle track start events"""
        player = payload.player
        track = payload.track
        
        try:
            if isinstance(player, MusicPlayer):
                player.update_activity()
                if hasattr(player, 'update_persistent_panel'):
                    await player.update_persistent_panel()
        except Exception as e:
            logger.error(f"Track start error: {e}")

    @commands.Cog.listener()
    async def on_wavelink_track_exception(self, payload: wavelink.TrackExceptionEventPayload):
        """Handle track exceptions"""
        player = payload.player
        track = payload.track
        exception = payload.exception
        
        guild_name = getattr(player.guild, 'name', 'Unknown') if hasattr(player, 'guild') else 'Unknown'
        logger.error(f"Track exception in {guild_name}: {exception}")
        
        try:
            if isinstance(player, MusicPlayer):
                await player.play_next()
        except Exception as e:
            logger.error(f"Failed to play next after exception: {e}")


async def setup(bot):
    """Setup function for discord.py 2.0+ cog loading"""
    await bot.add_cog(MusicCommands(bot))