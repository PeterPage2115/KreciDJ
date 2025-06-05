"""Music control buttons view"""

import discord
from discord.ext import commands
import wavelink
import random
from typing import Optional

class MusicControlsView(discord.ui.View):
    """Interactive music control buttons"""
    
    def __init__(self, player, timeout=None):  # None = never timeout
        super().__init__(timeout=timeout)
        self.player = player
        self.message: Optional[discord.Message] = None
        
    async def on_timeout(self):
        """Called when view times out"""
        try:
            if self.message is not None:
                # FIXED: Don't remove view, just disable buttons
                for item in self.children:
                    if isinstance(item, discord.ui.Button):
                        item.disabled = True
                
                # FIXED: Separate try/except for edit to avoid "Never" type issue
                try:
                    await self.message.edit(view=self)
                except (discord.NotFound, discord.HTTPException, discord.Forbidden):
                    # Message might be deleted or we don't have permissions
                    pass
        except Exception:
            # General catch-all for any other errors
            pass
    
    @discord.ui.button(emoji="⏸️", style=discord.ButtonStyle.primary, row=0)
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Pause/Resume button"""
        try:
            if not self.player:
                await interaction.response.send_message("❌ Player not found!", ephemeral=True)
                return
                
            if self.player.paused:
                await self.player.pause(False)  # Resume
                button.emoji = "⏸️"
                await interaction.response.edit_message(view=self)
                await interaction.followup.send("▶️ Resumed!", ephemeral=True)
            else:
                await self.player.pause(True)  # Pause
                button.emoji = "▶️"
                await interaction.response.edit_message(view=self)
                await interaction.followup.send("⏸️ Paused!", ephemeral=True)
        except discord.InteractionResponded:
            # Interaction already responded
            pass
        except Exception as e:
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)
            except:
                pass
    
    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary, row=0)
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Skip current track"""
        try:
            if not self.player:
                await interaction.response.send_message("❌ Player not found!", ephemeral=True)
                return
                
            if self.player.current:
                await self.player.stop()  # Use stop() to trigger next track
                await interaction.response.send_message("⏭️ Skipped!", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Nothing to skip!", ephemeral=True)
        except Exception as e:
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)
            except:
                pass
    
    @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.danger, row=0)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Stop playback and clear queue"""
        try:
            if not self.player:
                await interaction.response.send_message("❌ Player not found!", ephemeral=True)
                return
                
            await self.player.stop()
            if hasattr(self.player, 'queue'):
                self.player.queue.clear()
            await interaction.response.send_message("⏹️ Stopped!", ephemeral=True)
        except Exception as e:
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)
            except:
                pass
    
    @discord.ui.button(emoji="🔀", style=discord.ButtonStyle.secondary, row=1)
    async def shuffle_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Shuffle the queue"""
        try:
            if not self.player:
                await interaction.response.send_message("❌ Player not found!", ephemeral=True)
                return
                
            if hasattr(self.player, 'queue') and self.player.queue:
                tracks_list = list(self.player.queue)
                if len(tracks_list) < 2:
                    await interaction.response.send_message("❌ Need at least 2 tracks to shuffle!", ephemeral=True)
                    return
                    
                random.shuffle(tracks_list)
                
                self.player.queue.clear()
                for track in tracks_list:
                    await self.player.queue.put_wait(track)
                
                await interaction.response.send_message("🔀 Queue shuffled!", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Queue is empty!", ephemeral=True)
        except Exception as e:
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)
            except:
                pass
    
    @discord.ui.button(emoji="🔁", style=discord.ButtonStyle.secondary, row=1)
    async def loop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Toggle loop mode"""
        try:
            if not self.player:
                await interaction.response.send_message("❌ Player not found!", ephemeral=True)
                return
                
            if hasattr(self.player, 'loop_mode'):
                if self.player.loop_mode == 'off':
                    self.player.loop_mode = 'track'
                    button.emoji = "🔂"
                    await interaction.response.edit_message(view=self)
                    await interaction.followup.send("🔂 Loop: Track", ephemeral=True)
                elif self.player.loop_mode == 'track':
                    self.player.loop_mode = 'queue'
                    button.emoji = "🔁"
                    await interaction.response.edit_message(view=self)
                    await interaction.followup.send("🔁 Loop: Queue", ephemeral=True)
                else:
                    self.player.loop_mode = 'off'
                    button.emoji = "🔁"
                    await interaction.response.edit_message(view=self)
                    await interaction.followup.send("❌ Loop: Off", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Loop not supported!", ephemeral=True)
        except Exception as e:
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)
            except:
                pass
    
    @discord.ui.button(emoji="📋", style=discord.ButtonStyle.secondary, row=1) 
    async def queue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show queue"""
        try:
            if not self.player:
                await interaction.response.send_message("❌ Player not found!", ephemeral=True)
                return
                
            if hasattr(self.player, 'queue') and self.player.queue:
                queue_list = []
                for i, track in enumerate(list(self.player.queue)[:10], 1):
                    title = getattr(track, 'title', 'Unknown Track')
                    queue_list.append(f"{i}. {title}")
                
                embed = discord.Embed(
                    title="📋 Queue",
                    description="\n".join(queue_list) if queue_list else "Queue is empty",
                    color=0x3498db
                )
                
                if len(self.player.queue) > 10:
                    embed.set_footer(text=f"Showing 10/{len(self.player.queue)} tracks")
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message("📋 Queue is empty!", ephemeral=True)
        except Exception as e:
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)
            except:
                pass