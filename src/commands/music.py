"""Enhanced Music Commands with Beautiful UI"""

import discord
from discord.ext import commands
import wavelink
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Union, Any
import json
import logging

class EnhancedMusicUI:
    """Enhanced Music UI with persistent controls"""
    
    def __init__(self, bot):
        self.bot = bot
        self.persistent_panels: Dict[int, dict] = {}  # guild_id -> panel_data
        self.update_tasks: Dict[int, asyncio.Task] = {}
        self.logger = logging.getLogger('music_ui')
    
    async def create_now_playing_embed(self, player: wavelink.Player, track: Any) -> discord.Embed:
        """Create beautiful now playing embed - Clean 3x2 Layout"""
        
        # Calculate progress
        position = player.position or 0
        duration = getattr(track, 'length', 0) or 0
        progress_bar = self.create_progress_bar(position, duration)
        
        # Create main embed
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"**[{track.title}]({getattr(track, 'uri', 'https://discord.com')})**",
            color=0x1db954,  # Spotify green
            timestamp=datetime.utcnow()
        )
        
        # First Row - Track Info
        embed.add_field(
            name="🎤 Artist",
            value=f"`{getattr(track, 'author', 'Unknown')}`",
            inline=True
        )
        
        embed.add_field(
            name="⏱️ Duration", 
            value=f"`{self.format_time(duration)}`",
            inline=True
        )
        
        embed.add_field(
            name="🔊 Volume",
            value=f"`{player.volume}%`",
            inline=True
        )
        
        # Progress bar - Full Width
        embed.add_field(
            name="📈 Progress",
            value=f"```{progress_bar}```",
            inline=False
        )
        
        # Second Row - Player Status
        loop_mode = self.get_loop_mode_display(player)
        
        embed.add_field(
            name="🔁 Loop",
            value=f"`{loop_mode}`",
            inline=True
        )
        
        embed.add_field(
            name="👥 Queue",
            value=f"`{len(player.queue)} tracks`",
            inline=True
        )
        
        embed.add_field(
            name="🎧 Status",
            value=f"`{'Paused' if player.paused else 'Playing'}`",
            inline=True
        )
        
        # Add thumbnail if available
        if hasattr(track, 'artwork_url') and track.artwork_url:
            embed.set_thumbnail(url=track.artwork_url)
        elif hasattr(track, 'thumbnail') and track.thumbnail:
            embed.set_thumbnail(url=track.thumbnail)
        
        # Footer with controls hint
        embed.set_footer(
            text="Use buttons below to control playback • Auto-updates every 10s",
            icon_url=self.bot.user.avatar.url if self.bot.user and self.bot.user.avatar else None
        )
        
        return embed
    
    def get_loop_mode_display(self, player: wavelink.Player) -> str:
        """Get human-readable loop mode"""
        
        loop_mode = "Off"
        
        if hasattr(player, 'queue') and hasattr(player.queue, 'mode'):
            try:
                mode = str(player.queue.mode).lower()
                
                # Convert technical names to user-friendly names
                if 'normal' in mode or 'none' in mode:
                    loop_mode = "Off"
                elif 'loop' in mode and 'queue' in mode:
                    loop_mode = "Queue Loop"
                elif 'loop' in mode:
                    loop_mode = "Track Loop"
                elif 'repeat' in mode:
                    loop_mode = "Repeat"
                else:
                    loop_mode = "Off"
                    
            except:
                loop_mode = "Off"
        
        return loop_mode

    def create_progress_bar(self, position: int, duration: int, length: int = 20) -> str:
        """Create visual progress bar with time info"""
        if duration == 0 or position is None or duration is None:
            return "▱" * length + " --:-- / --:--"
            
        progress = min(position / duration, 1.0)
        filled = int(progress * length)
        
        # Create the bar
        bar = "▰" * filled + "▱" * (length - filled)
        
        # Format times
        current_time = self.format_time(position)
        total_time = self.format_time(duration)
        
        # Calculate percentage
        percentage = int(progress * 100)
        
        return f"{current_time} {bar} {total_time} ({percentage}%)"
    
    def format_time(self, milliseconds: Optional[int]) -> str:
        """Format time from milliseconds to MM:SS"""
        if milliseconds is None or milliseconds < 0:
            return "00:00"
            
        seconds = milliseconds // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        
        if minutes >= 60:
            hours = minutes // 60
            minutes = minutes % 60
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        
        return f"{minutes:02d}:{seconds:02d}"
    
    async def create_music_controls_view(self, player: wavelink.Player) -> discord.ui.View:
        """Create interactive music controls"""
        
        class MusicControlsView(discord.ui.View):
            def __init__(self, ui_handler, player):
                super().__init__(timeout=None)  # Persistent view
                self.ui_handler = ui_handler
                self.player = player
            
            @discord.ui.button(emoji="⏯️", style=discord.ButtonStyle.primary, custom_id="play_pause")
            async def play_pause(self, interaction: discord.Interaction, button: discord.ui.Button):
                try:
                    if self.player.paused:
                        await self.player.pause(False)  # Resume
                        await interaction.response.send_message("▶️ Resumed playback", ephemeral=True)
                    else:
                        await self.player.pause(True)  # Pause
                        await interaction.response.send_message("⏸️ Paused playback", ephemeral=True)
                except Exception as e:
                    await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
            
            @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary, custom_id="skip")
            async def skip_track(self, interaction: discord.Interaction, button: discord.ui.Button):
                try:
                    if not self.player.queue:
                        await interaction.response.send_message("❌ No tracks in queue to skip to", ephemeral=True)
                        return
                    
                    await self.player.skip()
                    await interaction.response.send_message("⏭️ Skipped to next track", ephemeral=True)
                except Exception as e:
                    await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
            
            @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.danger, custom_id="stop")
            async def stop_playback(self, interaction: discord.Interaction, button: discord.ui.Button):
                try:
                    await self.player.stop()
                    await self.player.disconnect()
                    await interaction.response.send_message("⏹️ Stopped playback and disconnected", ephemeral=True)
                except Exception as e:
                    await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
            
            @discord.ui.button(emoji="🔀", style=discord.ButtonStyle.secondary, custom_id="shuffle")
            async def shuffle_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
                try:
                    if len(self.player.queue) < 2:
                        await interaction.response.send_message("❌ Need at least 2 tracks to shuffle", ephemeral=True)
                        return
                    
                    # Manual shuffle since shuffle() might not exist
                    import random
                    queue_list = list(self.player.queue)
                    random.shuffle(queue_list)
                    
                    # Clear and refill queue
                    self.player.queue.clear()
                    for track in queue_list:
                        await self.player.queue.put_wait(track)
                    
                    await interaction.response.send_message("🔀 Queue shuffled", ephemeral=True)
                except Exception as e:
                    await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
            
            @discord.ui.button(emoji="📋", style=discord.ButtonStyle.secondary, custom_id="queue")
            async def show_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
                await self.ui_handler.show_queue_embed(interaction, self.player)
        
        return MusicControlsView(self, player)
    
    async def show_queue_embed(self, interaction: discord.Interaction, player: wavelink.Player):
        """Show queue in a beautiful embed"""
        
        if not player.queue:
            embed = discord.Embed(
                title="📋 Queue is Empty",
                description="No tracks in queue. Add some music with `!play`!",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Create queue embed
        embed = discord.Embed(
            title="📋 Music Queue",
            color=0x3498db,
            timestamp=datetime.utcnow()
        )
        
        # Show next 10 tracks
        queue_list = list(player.queue)[:10]
        queue_text = ""
        
        for i, track in enumerate(queue_list, 1):
            duration = self.format_time(getattr(track, 'length', 0))
            queue_text += f"`{i}.` **{track.title}** by `{getattr(track, 'author', 'Unknown')}`  •  `{duration}`\n"
        
        if len(player.queue) > 10:
            queue_text += f"\n*...and {len(player.queue) - 10} more tracks*"
        
        embed.description = queue_text
        embed.set_footer(text=f"Total: {len(player.queue)} tracks")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def create_persistent_panel(self, ctx, player: wavelink.Player, track: Any, force_new: bool = False):
        """Create or update persistent music control panel"""
        
        try:
            embed = await self.create_now_playing_embed(player, track)
            view = await self.create_music_controls_view(player)
            
            # Check if panel already exists
            guild_id = ctx.guild.id
            existing_panel = self.persistent_panels.get(guild_id)
            
            if existing_panel and not force_new:
                # Update existing panel
                try:
                    message = existing_panel['message']
                    await message.edit(embed=embed, view=view)
                    existing_panel['last_update'] = datetime.utcnow()
                    self.logger.info(f"Updated existing panel for guild {guild_id}")
                    return
                except discord.NotFound:
                    # Message was deleted, create new one
                    pass
                except Exception as e:
                    self.logger.warning(f"Failed to update existing panel: {e}")
            
            # Create new panel
            message = await ctx.send(embed=embed, view=view)
            
            # Store panel data
            self.persistent_panels[guild_id] = {
                'message': message,
                'channel': ctx.channel,
                'player': player,
                'last_update': datetime.utcnow()
            }
            
            # Start update task
            if guild_id in self.update_tasks:
                self.update_tasks[guild_id].cancel()
            
            self.update_tasks[guild_id] = asyncio.create_task(
                self.update_panel_loop(guild_id)
            )
            
            self.logger.info(f"Created new persistent panel for guild {guild_id}")
            
        except Exception as e:
            self.logger.error(f"Error creating persistent panel: {e}")
            # Fallback to simple embed
            embed = discord.Embed(
                title="🎵 Now Playing",
                description=f"**{track.title}** by {getattr(track, 'author', 'Unknown')}",
                color=0x1db954
            )
            await ctx.send(embed=embed)
    
    async def update_panel_loop(self, guild_id: int):
        """Update panel periodically"""
        
        while guild_id in self.persistent_panels:
            try:
                await asyncio.sleep(10)  # Update every 10 seconds
                
                panel_data = self.persistent_panels.get(guild_id)
                if not panel_data:
                    break
                
                player = panel_data['player']
                message = panel_data['message']
                
                # Check if player is still active
                if not player.connected or not player.current:
                    break
                
                # Update embed
                embed = await self.create_now_playing_embed(player, player.current)
                await message.edit(embed=embed)
                
                panel_data['last_update'] = datetime.utcnow()
                
            except discord.NotFound:
                # Message was deleted
                break
            except Exception as e:
                self.logger.error(f"Panel update error: {e}")
                break
        
        # Cleanup
        if guild_id in self.persistent_panels:
            del self.persistent_panels[guild_id]
        if guild_id in self.update_tasks:
            del self.update_tasks[guild_id]
    
    async def refresh_panel_position(self, ctx, player: wavelink.Player):
        """Refresh panel position by creating new one at bottom"""
        
        if not player or not player.current:
            return
            
        guild_id = ctx.guild.id
        
        # Cancel old panel update task
        if guild_id in self.update_tasks:
            self.update_tasks[guild_id].cancel()
        
        # Delete old panel reference (don't delete message to avoid spam)
        if guild_id in self.persistent_panels:
            old_panel = self.persistent_panels[guild_id]
            # Optionally delete old message after delay
            try:
                await asyncio.sleep(2)
                await old_panel['message'].delete()
            except:
                pass
        
        # Create fresh panel at current position
        await self.create_persistent_panel(ctx, player, player.current, force_new=True)

class MusicCommands(commands.Cog):
    """Enhanced Music Commands with Beautiful UI"""
    
    def __init__(self, bot):
        self.bot = bot
        self.ui_handler = EnhancedMusicUI(bot)
        self.logger = logging.getLogger('music_commands')
    
    def get_player(self, ctx) -> Optional[wavelink.Player]:
        """Get player for guild"""
        try:
            return wavelink.Pool.get_node().get_player(ctx.guild.id)
        except:
            return None
    
    @commands.hybrid_command(name="play", description="Play music with enhanced UI")
    async def enhanced_play(self, ctx, *, query: str):
        """Enhanced play command with beautiful UI"""
        
        try:
            # Check if user is in voice channel
            if not ctx.author.voice:
                embed = discord.Embed(
                    title="❌ Voice Channel Required",
                    description="You need to be in a voice channel to use this command!",
                    color=0xff6b6b
                )
                return await ctx.send(embed=embed)
            
            # Get or create player
            player = self.get_player(ctx)
            if not player:
                player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
            
            # Set up autoplay
            player.autoplay = wavelink.AutoPlayMode.enabled

            # Search for tracks
            if query.startswith(("http://", "https://")):
                tracks = await wavelink.Pool.fetch_tracks(query)
            else:
                tracks = await wavelink.Pool.fetch_tracks(f"ytsearch:{query}")
            
            if not tracks:
                embed = discord.Embed(
                    title="❌ No Results",
                    description=f"No tracks found for: `{query}`",
                    color=0xff6b6b
                )
                return await ctx.send(embed=embed)
            
            track = tracks[0]
            
            # Add to queue or play
            if player.current:
                await player.queue.put_wait(track)
                embed = discord.Embed(
                    title="📋 Added to Queue",
                    description=f"**[{track.title}]({getattr(track, 'uri', 'https://discord.com')})**\nby `{getattr(track, 'author', 'Unknown')}`",
                    color=0x00ff00
                )
                embed.add_field(name="Position", value=f"`#{len(player.queue)}`", inline=True)
                embed.add_field(name="Duration", value=f"`{self.ui_handler.format_time(getattr(track, 'length', 0))}`", inline=True)
                await ctx.send(embed=embed)
            else:
                await player.play(track)
                # Create persistent panel
                await self.ui_handler.create_persistent_panel(ctx, player, track)
        
        except Exception as e:
            self.logger.error(f"Play command error: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {str(e)}",
                color=0xff6b6b
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="volume", description="Set volume with visual feedback")
    async def volume_enhanced(self, ctx, volume: Optional[int] = None):
        """Enhanced volume control"""
        
        player = self.get_player(ctx)
        if not player:
            embed = discord.Embed(
                title="❌ No Player",
                description="No active music player",
                color=0xff6b6b
            )
            return await ctx.send(embed=embed)
        
        if volume is None:
            # Show current volume
            embed = discord.Embed(
                title="🔊 Current Volume",
                description=f"Volume is set to **{player.volume}%**",
                color=0x3498db
            )
            
            # Add volume bar
            vol_bar = "▰" * (player.volume // 10) + "▱" * (10 - player.volume // 10)
            embed.add_field(
                name="Volume Bar",
                value=f"```{vol_bar} {player.volume}%```",
                inline=False
            )
            
            # Send and refresh panel
            await self.send_with_panel_refresh(ctx, embed)
            return
        
        # Set volume
        if not 0 <= volume <= 100:
            embed = discord.Embed(
                title="❌ Invalid Volume",
                description="Volume must be between 0 and 100",
                color=0xff6b6b
            )
            return await ctx.send(embed=embed)
        
        await player.set_volume(volume)
        
        # Visual feedback
        embed = discord.Embed(
            title="🔊 Volume Changed",
            description=f"Volume set to **{volume}%**",
            color=0x00ff00
        )
        
        vol_bar = "▰" * (volume // 10) + "▱" * (10 - volume // 10)
        embed.add_field(
            name="Volume Bar",
            value=f"```{vol_bar} {volume}%```",
            inline=False
        )
        
        # Send and refresh panel
        await self.send_with_panel_refresh(ctx, embed)
    
    @commands.hybrid_command(name="queue", aliases=["q"], description="Show queue")
    async def queue_enhanced(self, ctx):
        """Enhanced queue display"""
        
        player = self.get_player(ctx)
        if not player:
            embed = discord.Embed(
                title="❌ No Player",
                description="No active music player",
                color=0xff6b6b
            )
            return await ctx.send(embed=embed)
        
        # Direct call instead of interaction
        if not player.queue:
            embed = discord.Embed(
                title="📋 Queue is Empty",
                description="No tracks in queue. Add some music with `!play`!",
                color=0xff6b6b
            )
            # Send and refresh panel
            await self.send_with_panel_refresh(ctx, embed)
            return
        
        # Create queue embed
        embed = discord.Embed(
            title="📋 Music Queue",
            color=0x3498db,
            timestamp=datetime.utcnow()
        )
        
        # Show next 10 tracks
        queue_list = list(player.queue)[:10]
        queue_text = ""
        
        for i, track in enumerate(queue_list, 1):
            duration = self.ui_handler.format_time(getattr(track, 'length', 0))
            queue_text += f"`{i}.` **{track.title}** by `{getattr(track, 'author', 'Unknown')}`  •  `{duration}`\n"
        
        if len(player.queue) > 10:
            queue_text += f"\n*...and {len(player.queue) - 10} more tracks*"
        
        embed.description = queue_text
        embed.set_footer(text=f"Total: {len(player.queue)} tracks")
        
        # Send and refresh panel
        await self.send_with_panel_refresh(ctx, embed)
    
    @commands.hybrid_command(name="nowplaying", aliases=["np"], description="Show enhanced now playing")
    async def now_playing_enhanced(self, ctx):
        """Enhanced now playing display"""
        
        player = self.get_player(ctx)
        if not player or not player.current:
            embed = discord.Embed(
                title="❌ Nothing Playing",
                description="No music is currently playing",
                color=0xff6b6b
            )
            return await ctx.send(embed=embed)
        
        # Create enhanced display at current position
        await self.ui_handler.create_persistent_panel(ctx, player, player.current, force_new=True)
    
    @commands.hybrid_command(name="pause", description="Pause playback")
    async def pause_enhanced(self, ctx):
        """Pause playback with visual feedback"""
        
        player = self.get_player(ctx)
        if not player or not player.current:
            embed = discord.Embed(
                title="❌ Nothing Playing",
                description="No music is currently playing",
                color=0xff6b6b
            )
            return await ctx.send(embed=embed)
        
        if player.paused:
            embed = discord.Embed(
                title="⏸️ Already Paused",
                description="Playback is already paused",
                color=0xffaa00
            )
            return await ctx.send(embed=embed)
        
        await player.pause(True)
        embed = discord.Embed(
            title="⏸️ Paused",
            description=f"Paused: **{player.current.title}**",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="resume", description="Resume playback")
    async def resume_enhanced(self, ctx):
        """Resume playback with visual feedback"""
        
        player = self.get_player(ctx)
        if not player or not player.current:
            embed = discord.Embed(
                title="❌ Nothing Playing",
                description="No music is currently playing",
                color=0xff6b6b
            )
            return await ctx.send(embed=embed)
        
        if not player.paused:
            embed = discord.Embed(
                title="▶️ Already Playing",
                description="Playback is already active",
                color=0xffaa00
            )
            return await ctx.send(embed=embed)
        
        await player.pause(False)  # Resume
        embed = discord.Embed(
            title="▶️ Resumed",
            description=f"Resumed: **{player.current.title}**",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="skip", description="Skip current track")
    async def skip_enhanced(self, ctx):
        """Skip current track with visual feedback"""
        
        player = self.get_player(ctx)
        if not player or not player.current:
            embed = discord.Embed(
                title="❌ Nothing Playing",
                description="No music is currently playing",
                color=0xff6b6b
            )
            return await ctx.send(embed=embed)
        
        old_track = player.current.title
        await player.skip()
        
        embed = discord.Embed(
            title="⏭️ Skipped",
            description=f"Skipped: **{old_track}**",
            color=0x00ff00
        )
        
        if player.current:
            embed.add_field(
                name="Now Playing",
                value=f"**{player.current.title}** by `{getattr(player.current, 'author', 'Unknown')}`",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="stop", description="Stop playback and disconnect")
    async def stop_enhanced(self, ctx):
        """Stop playback and disconnect"""
        
        player = self.get_player(ctx)
        if not player:
            embed = discord.Embed(
                title="❌ No Player",
                description="No active music player",
                color=0xff6b6b
            )
            return await ctx.send(embed=embed)
        
        await player.stop()
        await player.disconnect()
        
        # Cleanup UI
        if ctx.guild.id in self.ui_handler.persistent_panels:
            del self.ui_handler.persistent_panels[ctx.guild.id]
        if ctx.guild.id in self.ui_handler.update_tasks:
            self.ui_handler.update_tasks[ctx.guild.id].cancel()
            del self.ui_handler.update_tasks[ctx.guild.id]
        
        embed = discord.Embed(
            title="⏹️ Stopped",
            description="Playback stopped and disconnected from voice channel",
            color=0x00ff00
        )
        await ctx.send(embed=embed)

    async def send_with_panel_refresh(self, ctx, embed: discord.Embed):
        """Send embed and refresh panel position"""
        
        await ctx.send(embed=embed)
        
        # Refresh panel position if music is playing
        player = self.get_player(ctx)
        if player and player.current:
            await self.ui_handler.refresh_panel_position(ctx, player)
    
    @commands.hybrid_command(name="panel", aliases=["controls"], description="Show music control panel")
    async def refresh_panel(self, ctx):
        """Refresh music control panel at current position"""
        
        player = self.get_player(ctx)
        if not player or not player.current:
            embed = discord.Embed(
                title="❌ Nothing Playing",
                description="No music is currently playing",
                color=0xff6b6b
            )
            return await ctx.send(embed=embed)
        
        # Force create new panel at current position
        await self.ui_handler.create_persistent_panel(ctx, player, player.current, force_new=True)
        
        # Send confirmation
        embed = discord.Embed(
            title="🎮 Panel Refreshed",
            description="Music control panel moved to current position",
            color=0x00ff00
        )
        await ctx.send(embed=embed, delete_after=3)  # Auto-delete after 3s

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        """Handle track end event - Auto-play next track"""
        
        player = payload.player
        
        if not player:
            return
            
        # Log the track end
        guild_id = player.guild.id if player.guild else "Unknown"
        self.logger.info(f"Track ended in guild {guild_id}: {payload.track.title if payload.track else 'Unknown'}")
        
        # Check if there are tracks in queue
        if not player.queue.is_empty:
            try:
                # Get next track
                next_track = await player.queue.get_wait()
                
                # Play next track
                await player.play(next_track)
                
                self.logger.info(f"Auto-playing next track: {next_track.title}")
                
                # Update any existing panels
                await self.update_panels_for_new_track(player, next_track)
                
            except Exception as e:
                self.logger.error(f"Error auto-playing next track: {e}")
        else:
            # Queue is empty, clean up panels
            guild_id = player.guild.id if player.guild else "Unknown"
            self.logger.info(f"Queue empty in guild {guild_id}, playback finished")
            if player.guild:
                await self.cleanup_panels_for_guild(player.guild.id)
    
    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        """Handle track start event"""
        
        player = payload.player
        track = payload.track
        
        if not player or not track:
            return
            
        guild_id = player.guild.id if player.guild else "Unknown"
        self.logger.info(f"Track started in guild {guild_id}: {track.title}")
        
        # Update panels for new track
        await self.update_panels_for_new_track(player, track)
    
    async def update_panels_for_new_track(self, player: wavelink.Player, track: Any):
        """Update existing panels when new track starts"""
        
        if not player.guild:
            return
            
        guild_id = player.guild.id
        panel_data = self.ui_handler.persistent_panels.get(guild_id)
        
        if panel_data:
            try:
                # Update the embed with new track info
                embed = await self.ui_handler.create_now_playing_embed(player, track)
                view = await self.ui_handler.create_music_controls_view(player)
                
                message = panel_data['message']
                await message.edit(embed=embed, view=view)
                
                panel_data['last_update'] = datetime.utcnow()
                
                self.logger.info(f"Updated panel for new track in guild {guild_id}")
                
            except discord.NotFound:
                # Panel message was deleted
                del self.ui_handler.persistent_panels[guild_id]
            except Exception as e:
                self.logger.error(f"Error updating panel for new track: {e}")
    
    async def cleanup_panels_for_guild(self, guild_id: int):
        """Clean up panels when playback ends"""
        
        # Cancel update tasks
        if guild_id in self.ui_handler.update_tasks:
            self.ui_handler.update_tasks[guild_id].cancel()
            del self.ui_handler.update_tasks[guild_id]
        
        # Remove panel reference
        if guild_id in self.ui_handler.persistent_panels:
            panel_data = self.ui_handler.persistent_panels[guild_id]
            
            try:
                # Update panel to show "Playback Finished"
                embed = discord.Embed(
                    title="🏁 Playback Finished",
                    description="All tracks have been played. Add more music with `!play`!",
                    color=0x95a5a6
                )
                embed.set_footer(text="Use !play to add more tracks")
                
                # Remove buttons (set view to None)
                await panel_data['message'].edit(embed=embed, view=None)
                
            except discord.NotFound:
                pass
            except Exception as e:
                self.logger.error(f"Error updating finished panel: {e}")
            
            # Clean up reference
            del self.ui_handler.persistent_panels[guild_id]

async def setup(bot):
    await bot.add_cog(MusicCommands(bot))