"""Slash commands for playback, queue, volume, loop, and leave."""
from __future__ import annotations

import asyncio
import re
import time
from typing import TYPE_CHECKING

import discord
from discord import app_commands
import mafic
from mafic import SearchType
import config
from player import get_guild_player
from embed_styles import (
    Colors, Icons,
    build_now_playing_embed, build_queue_embed, build_success_embed,
    build_error_embed, build_warning_embed, build_info_embed,
    build_loading_embed, build_idle_embed, build_added_to_queue_embed,
    build_playlist_added_embed, build_volume_embed, build_loop_embed,
    build_search_results_embed, format_duration
)

if TYPE_CHECKING:
    from bot import MusicBot


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Now-playing embed update interval (seconds)
_NP_UPDATE_INTERVAL = 10


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_position(position: str) -> int | None:
    """Parse '1:30' or '90' to milliseconds. Returns None if invalid."""
    position = position.strip()
    if not position:
        return None
    # M:SS or MM:SS
    m = re.match(r"^(\d+):(\d{1,2})$", position)
    if m:
        mins, secs = int(m.group(1)), int(m.group(2))
        if secs < 60:
            return (mins * 60 + secs) * 1000
    # Plain seconds
    try:
        secs = int(position)
        return secs * 1000
    except ValueError:
        return None


async def _ensure_voice(interaction: discord.Interaction) -> discord.VoiceChannel | None:
    """Ensure user is in a voice channel. Used for /play command where bot may not be connected yet."""
    channel = interaction.user.voice.channel if interaction.user.voice else None
    if channel is None:
        embed = build_error_embed(
            "Not in Voice",
            "You need to join a voice channel first."
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return None
    return channel


async def _ensure_same_voice(interaction: discord.Interaction) -> bool:
    """Ensure user is in the SAME voice channel as the bot.
    
    Used for control commands (pause, skip, stop, volume, etc.)
    Returns True if valid, False otherwise (sends error message).
    """
    # Check if user is in a voice channel
    user_channel = interaction.user.voice.channel if interaction.user.voice else None
    if user_channel is None:
        embed = build_error_embed(
            "Not in Voice",
            "You need to join a voice channel first."
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return False
    
    # Check if bot is in a voice channel
    vc = _get_player(interaction)
    if vc is None or not vc.connected:
        embed = build_error_embed(
            "Not Connected",
            "The bot is not in a voice channel."
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return False
    
    # Check if user is in the SAME voice channel as the bot
    if user_channel.id != vc.channel.id:
        embed = build_error_embed(
            "Wrong Channel",
            f"You must be in **{vc.channel.name}** to control the music."
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return False
    
    return True


def _get_player(interaction: discord.Interaction) -> mafic.Player | None:
    """Get the Mafic player for the interaction's guild."""
    vc = interaction.guild.voice_client
    if vc is None or not isinstance(vc, mafic.Player):
        return None
    return vc


def _get_vc_guild(guild: discord.Guild) -> mafic.Player | None:
    """Get the Mafic player for a guild."""
    vc = guild.voice_client
    if vc is None or not isinstance(vc, mafic.Player):
        return None
    return vc


# ═══════════════════════════════════════════════════════════════════════════════
# NOW-PLAYING UPDATER
# ═══════════════════════════════════════════════════════════════════════════════

async def _now_playing_updater_loop(
    bot: MusicBot, guild_id: int, view: MusicControlView
) -> None:
    """Background loop: update now-playing embed every N seconds."""
    try:
        while True:
            await asyncio.sleep(_NP_UPDATE_INTERVAL)
            if not view.message:
                break
            
            guild = bot.get_guild(guild_id)
            if not guild:
                break
            
            vc = _get_vc_guild(guild)
            if not vc or not vc.connected or not vc.current:
                try:
                    embed = build_idle_embed()
                    await view.message.edit(embed=embed)
                except discord.NotFound:
                    pass
                break
            
            guild_player = get_guild_player(bot, guild_id)
            embed = build_now_playing_embed(
                vc.current,
                vc.position,
                guild_player.volume,
                is_paused=vc.paused,
                loop_mode=guild_player.loop
            )
            try:
                await view.message.edit(embed=embed)
            except discord.NotFound:
                break
            except Exception:
                pass  # Rate limit; keep trying
    except asyncio.CancelledError:
        pass
    finally:
        if hasattr(bot, "_np_tasks") and guild_id in bot._np_tasks:
            bot._np_tasks.pop(guild_id, None)


def _start_now_playing_updater(
    bot: MusicBot, guild_id: int, view: MusicControlView
) -> None:
    """Cancel any existing now-playing updater and start a new one."""
    if not hasattr(bot, "_np_tasks"):
        bot._np_tasks = {}
    old = bot._np_tasks.pop(guild_id, None)
    if old and not old.done():
        old.cancel()
    task = asyncio.create_task(_now_playing_updater_loop(bot, guild_id, view))
    bot._np_tasks[guild_id] = task


def _stop_now_playing_updater(bot: MusicBot, guild_id: int) -> None:
    """Stop the now-playing updater for a guild."""
    if hasattr(bot, "_np_tasks") and guild_id in bot._np_tasks:
        task = bot._np_tasks.pop(guild_id, None)
        if task and not task.done():
            task.cancel()


# ═══════════════════════════════════════════════════════════════════════════════
# TRACK SELECT VIEW (Search Results Dropdown)
# ═══════════════════════════════════════════════════════════════════════════════

class TrackSelectView(discord.ui.View):
    """Dropdown for selecting a track from search results."""

    def __init__(
        self,
        tracks: list,
        original_user_id: int,
        timeout: float = 30.0
    ) -> None:
        super().__init__(timeout=timeout)
        self.tracks = tracks[:5]  # Max 5 results
        self.original_user_id = original_user_id
        self.selected_track = None
        self.cancelled = False
        self.message: discord.Message | None = None
        
        # Build select options
        options = []
        for i, track in enumerate(self.tracks):
            title = (track.title or "Unknown")[:95]
            author = getattr(track, "author", "Unknown")[:50]
            duration = format_duration(track.length)
            
            options.append(discord.SelectOption(
                label=f"{i + 1}. {title}",
                value=str(i),
                description=f"{author} • {duration}",
                emoji="🎵"
            ))
        
        # Add cancel option
        options.append(discord.SelectOption(
            label="Cancel",
            value="cancel",
            description="Cancel search",
            emoji="❌"
        ))
        
        # Create select menu
        self.select_menu = discord.ui.Select(
            placeholder="🔍 Choose a track to play...",
            options=options,
            custom_id="track_select"
        )
        self.select_menu.callback = self.select_callback
        self.add_item(self.select_menu)

    async def select_callback(self, interaction: discord.Interaction) -> None:
        """Handle track selection."""
        # Only allow original user to select
        if interaction.user.id != self.original_user_id:
            embed = build_error_embed(
                "Not Your Search",
                "Only the person who searched can select a track."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        value = self.select_menu.values[0]
        
        if value == "cancel":
            self.cancelled = True
            self.selected_track = None
        else:
            idx = int(value)
            self.selected_track = self.tracks[idx]
        
        self.stop()
        await interaction.response.defer()

    async def on_timeout(self) -> None:
        """Auto-select first track on timeout."""
        if self.selected_track is None and not self.cancelled:
            self.selected_track = self.tracks[0] if self.tracks else None
        
        # Disable the select menu
        self.select_menu.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass


# ═══════════════════════════════════════════════════════════════════════════════
# MUSIC CONTROL VIEW (Buttons)
# ═══════════════════════════════════════════════════════════════════════════════

class MusicControlView(discord.ui.View):
    """Modern control buttons for now-playing. Attach .message after sending."""

    def __init__(self, bot: MusicBot, paused: bool = False, timeout: float = 600) -> None:
        super().__init__(timeout=timeout)
        self.bot = bot
        self._paused = paused
        self.message: discord.Message | None = None
        self._update_pause_button()

    def _update_pause_button(self) -> None:
        """Update pause button label and style based on state."""
        for child in self.children:
            if getattr(child, "custom_id", "") == "music_pause":
                if self._paused:
                    child.label = "Resume"
                    child.emoji = Icons.RESUME
                    child.style = discord.ButtonStyle.success
                else:
                    child.label = "Pause"
                    child.emoji = Icons.PAUSE
                    child.style = discord.ButtonStyle.secondary
                break

    async def _check_same_voice_channel(self, interaction: discord.Interaction) -> bool:
        """Check if user is in the same voice channel as the bot.
        
        Returns True if valid, False if not (and sends error message).
        """
        # Check if user is in a voice channel
        if interaction.user.voice is None or interaction.user.voice.channel is None:
            embed = build_error_embed(
                "Not in Voice", 
                "You need to join a voice channel to use these controls."
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return False
        
        # Check if bot is in a voice channel
        vc = _get_vc_guild(interaction.guild)
        if vc is None or not vc.connected:
            embed = build_error_embed(
                "Not Connected", 
                "The bot is not in a voice channel."
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return False
        
        # Check if user is in the SAME voice channel as the bot
        if interaction.user.voice.channel.id != vc.channel.id:
            embed = build_error_embed(
                "Wrong Channel", 
                f"You must be in **{vc.channel.name}** to control the music."
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return False
        
        return True

    async def _refresh_embed(self, interaction: discord.Interaction) -> None:
        """Refresh the now-playing embed after a button action."""
        guild_id = interaction.guild_id
        if not guild_id:
            return
        
        vc = _get_vc_guild(interaction.guild)
        if not vc or not vc.current:
            return
        
        guild_player = get_guild_player(self.bot, guild_id)
        embed = build_now_playing_embed(
            vc.current,
            vc.position,
            guild_player.volume,
            is_paused=vc.paused,
            loop_mode=guild_player.loop
        )
        if self.message:
            await self.message.edit(embed=embed, view=self)

    @discord.ui.button(label="Pause", emoji=Icons.PAUSE, custom_id="music_pause", style=discord.ButtonStyle.secondary, row=0)
    async def pause_resume(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.defer()
        
        # Check if user is in the same voice channel as the bot
        if not await self._check_same_voice_channel(interaction):
            return
        
        guild_id = interaction.guild_id
        if guild_id is None:
            return
        
        vc = _get_vc_guild(interaction.guild)
        if vc is None or not vc.connected:
            embed = build_error_embed("Not Connected", "Bot is not in a voice channel.")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        if vc.paused:
            await vc.resume()
            self._paused = False
            embed = build_success_embed("Resumed", f"{Icons.PLAY} Playback resumed.")
        else:
            await vc.pause()
            self._paused = True
            embed = build_warning_embed("Paused", f"{Icons.PAUSE} Playback paused.")
        
        self._update_pause_button()
        await self._refresh_embed(interaction)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="Skip", emoji=Icons.SKIP, custom_id="music_skip", style=discord.ButtonStyle.primary, row=0)
    async def skip_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.defer()
        
        # Check if user is in the same voice channel as the bot
        if not await self._check_same_voice_channel(interaction):
            return
        
        guild_id = interaction.guild_id
        if guild_id is None:
            return
        
        vc = _get_vc_guild(interaction.guild)
        
        guild_player = get_guild_player(self.bot, guild_id)
        next_track = guild_player.get_next(vc.current)
        
        if next_track is not None:
            vol = min(config.LAVALINK_VOLUME_MAX, max(0, guild_player.volume * config.LAVALINK_VOLUME_MAX // 100))
            await vc.play(next_track, replace=True, volume=vol)
            
            self._paused = False
            self._update_pause_button()
            
            # Update embed
            embed = build_now_playing_embed(
                next_track, 0, guild_player.volume,
                is_paused=False, loop_mode=guild_player.loop
            )
            if self.message:
                await self.message.edit(embed=embed, view=self)
            
            skip_embed = build_success_embed("Skipped", f"{Icons.SKIP} Now playing **{next_track.title}**")
            await interaction.followup.send(embed=skip_embed, ephemeral=True)
        else:
            await vc.stop()
            if self.message:
                embed = build_idle_embed()
                for c in self.children:
                    c.disabled = True
                await self.message.edit(embed=embed, view=self)
            _stop_now_playing_updater(self.bot, guild_id)
            
            embed = build_info_embed("Queue Empty", "Skipped. No more tracks in queue.")
            await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="Stop", emoji=Icons.STOP, custom_id="music_stop", style=discord.ButtonStyle.danger, row=0)
    async def stop_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.defer()
        
        # Check if user is in the same voice channel as the bot
        if not await self._check_same_voice_channel(interaction):
            return
        
        guild_id = interaction.guild_id
        if guild_id is None:
            return
        
        vc = _get_vc_guild(interaction.guild)
        guild_player = get_guild_player(self.bot, guild_id)
        guild_player.clear()
        
        if vc is not None and vc.connected:
            await vc.stop()
        
        if self.message:
            embed = build_idle_embed()
            for c in self.children:
                c.disabled = True
            await self.message.edit(embed=embed, view=self)
        
        _stop_now_playing_updater(self.bot, guild_id)
        
        embed = build_success_embed("Stopped", f"{Icons.STOP} Playback stopped and queue cleared.")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="−10%", emoji=Icons.VOLUME_DOWN, custom_id="music_vol_down", style=discord.ButtonStyle.secondary, row=1)
    async def vol_down(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.defer()
        
        # Check if user is in the same voice channel as the bot
        if not await self._check_same_voice_channel(interaction):
            return
        
        guild_id = interaction.guild_id
        if guild_id is None:
            return
        
        guild_player = get_guild_player(self.bot, guild_id)
        old_vol = guild_player.volume
        guild_player.volume = max(0, guild_player.volume - 10)
        
        vc = _get_vc_guild(interaction.guild)
        if vc is not None and vc.connected:
            await vc.set_volume(min(config.LAVALINK_VOLUME_MAX, guild_player.volume * config.LAVALINK_VOLUME_MAX // 100))
        
        await self._refresh_embed(interaction)
        
        embed = build_volume_embed(guild_player.volume, changed_by=-10)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="+10%", emoji=Icons.VOLUME_UP, custom_id="music_vol_up", style=discord.ButtonStyle.secondary, row=1)
    async def vol_up(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.defer()
        
        # Check if user is in the same voice channel as the bot
        if not await self._check_same_voice_channel(interaction):
            return
        
        guild_id = interaction.guild_id
        if guild_id is None:
            return
        
        guild_player = get_guild_player(self.bot, guild_id)
        guild_player.volume = min(100, guild_player.volume + 10)
        
        vc = _get_vc_guild(interaction.guild)
        if vc is not None and vc.connected:
            await vc.set_volume(min(config.LAVALINK_VOLUME_MAX, guild_player.volume * config.LAVALINK_VOLUME_MAX // 100))
        
        await self._refresh_embed(interaction)
        
        embed = build_volume_embed(guild_player.volume, changed_by=10)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="Queue", emoji=Icons.QUEUE, custom_id="music_queue", style=discord.ButtonStyle.primary, row=1)
    async def queue_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.defer(ephemeral=True)
        
        guild_id = interaction.guild_id
        if guild_id is None:
            return
        
        guild_player = get_guild_player(self.bot, guild_id)
        vc = _get_vc_guild(interaction.guild)
        
        embed = build_queue_embed(
            guild_player.queue,
            current_track=vc.current if vc else None
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    async def on_timeout(self) -> None:
        """Disable buttons on timeout."""
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass


# ═══════════════════════════════════════════════════════════════════════════════
# MUSIC COG (Slash Commands)
# ═══════════════════════════════════════════════════════════════════════════════

class MusicCog(discord.app_commands.Group):
    """Music playback commands."""

    def __init__(self, bot: MusicBot) -> None:
        super().__init__(name="music", description="Music playback and queue management")
        self.bot = bot

    @app_commands.command(name="play", description="Play a YouTube URL or search query")
    @app_commands.describe(query="YouTube URL or search query")
    async def play(self, interaction: discord.Interaction, query: str) -> None:
        channel = await _ensure_voice(interaction)
        if channel is None:
            return
        
        # Check if bot is already in a DIFFERENT voice channel
        existing_vc = _get_player(interaction)
        if existing_vc is not None and existing_vc.connected:
            if existing_vc.channel.id != channel.id:
                embed = build_error_embed(
                    "Already in Use",
                    f"The bot is currently in **{existing_vc.channel.name}**.\n"
                    f"Join that channel or wait for it to become available."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        query = query.strip()
        if not query:
            embed = build_error_embed("Missing Query", "Please provide a URL or search query.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Send loading state
        loading_embed = build_loading_embed("Searching for tracks...")
        await interaction.response.send_message(embed=loading_embed)

        bot = self.bot
        guild_id = interaction.guild_id
        assert guild_id is not None
        guild_player = get_guild_player(bot, guild_id)

        # Connect if needed
        vc = _get_player(interaction)
        if vc is None:
            try:
                vc = await channel.connect(cls=mafic.Player, self_deaf=True)
            except Exception as e:
                embed = build_error_embed("Connection Failed", f"Could not join voice: {e}")
                await interaction.edit_original_response(embed=embed)
                return

        # Resolve query - check if it's a URL or search
        is_url = query.startswith("http://") or query.startswith("https://")
        
        try:
            if is_url:
                # Direct URL - no search type needed
                result = await vc.fetch_tracks(query)
            else:
                # Search query - let mafic add the ytsearch: prefix via search_type
                result = await vc.fetch_tracks(query, search_type=SearchType.YOUTUBE)
        except Exception as e:
            embed = build_error_embed("Search Failed", f"Could not search for tracks: {e}")
            await interaction.edit_original_response(embed=embed)
            return

        if result is None:
            embed = build_warning_embed("No Results", "No tracks found for your query.")
            await interaction.edit_original_response(embed=embed)
            return

        # Handle playlist (direct add, no selection needed)
        if isinstance(result, mafic.Playlist):
            tracks = result.tracks
            guild_player.add_many(tracks)
            name = result.name or "Playlist"
            embed = build_playlist_added_embed(name, len(tracks))
            await interaction.edit_original_response(embed=embed)
        else:
            tracks = list(result)
            if not tracks:
                embed = build_warning_embed("No Results", "No tracks found for your query.")
                await interaction.edit_original_response(embed=embed)
                return
            
            # For search queries with multiple results, show selection dropdown
            if not is_url and len(tracks) > 1:
                # Show search results with dropdown
                embed = build_search_results_embed(query, tracks)
                select_view = TrackSelectView(tracks, interaction.user.id)
                msg = await interaction.edit_original_response(embed=embed, view=select_view)
                select_view.message = msg
                
                # Wait for user selection
                await select_view.wait()
                
                if select_view.cancelled:
                    embed = build_info_embed("Search Cancelled", "No track was added.")
                    await interaction.edit_original_response(embed=embed, view=None)
                    return
                
                selected_track = select_view.selected_track
                if selected_track is None:
                    embed = build_warning_embed("No Selection", "No track was selected.")
                    await interaction.edit_original_response(embed=embed, view=None)
                    return
                
                guild_player.add(selected_track)
                # Clear the dropdown
                await interaction.edit_original_response(view=None)
            else:
                # URL or single result - just add first track
                selected_track = tracks[0]
                guild_player.add(selected_track)

        # Re-check voice connection after selection (may have disconnected during 30s wait)
        vc = _get_player(interaction)
        if vc is None or not vc.connected:
            # Try to reconnect
            try:
                vc = await channel.connect(cls=mafic.Player, self_deaf=True)
            except Exception as e:
                embed = build_error_embed("Connection Failed", f"Could not rejoin voice: {e}")
                await interaction.edit_original_response(embed=embed)
                return

        # Start playing if nothing is playing
        if vc.current is None:
            next_track = guild_player.get_next(None)
            if next_track is not None:
                vol = min(config.LAVALINK_VOLUME_MAX, max(0, guild_player.volume * config.LAVALINK_VOLUME_MAX // 100))
                await vc.play(next_track, replace=True, volume=vol)
                
                embed = build_now_playing_embed(
                    next_track, 0, guild_player.volume,
                    is_paused=False, loop_mode=guild_player.loop
                )
                view = MusicControlView(bot, paused=False)
                msg = await interaction.edit_original_response(embed=embed, view=view)
                view.message = msg
                _start_now_playing_updater(bot, guild_id, view)
                return

        # Only added to queue (single track from non-playlist)
        if not isinstance(result, mafic.Playlist):
            embed = build_added_to_queue_embed(selected_track, position=len(guild_player.queue))
            await interaction.edit_original_response(embed=embed)

    @app_commands.command(name="pause", description="Pause playback")
    async def pause(self, interaction: discord.Interaction) -> None:
        if not await _ensure_same_voice(interaction):
            return
        
        vc = _get_player(interaction)
        if vc.paused:
            embed = build_warning_embed("Already Paused", "Playback is already paused.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await vc.pause()
        embed = build_success_embed("Paused", f"{Icons.PAUSE} Playback has been paused.")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="resume", description="Resume playback")
    async def resume(self, interaction: discord.Interaction) -> None:
        if not await _ensure_same_voice(interaction):
            return
        
        vc = _get_player(interaction)
        if not vc.paused:
            embed = build_warning_embed("Not Paused", "Playback is not paused.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await vc.resume()
        embed = build_success_embed("Resumed", f"{Icons.PLAY} Playback has been resumed.")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="stop", description="Stop playback and clear queue")
    async def stop(self, interaction: discord.Interaction) -> None:
        if not await _ensure_same_voice(interaction):
            return
        
        vc = _get_player(interaction)
        guild_id = interaction.guild_id
        assert guild_id is not None
        guild_player = get_guild_player(self.bot, guild_id)
        guild_player.clear()
        
        await vc.stop()
        _stop_now_playing_updater(self.bot, guild_id)
        
        embed = build_success_embed("Stopped", f"{Icons.STOP} Playback stopped and queue cleared.")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="skip", description="Skip current track or N tracks")
    @app_commands.describe(count="Number of tracks to skip (default 1)")
    async def skip(self, interaction: discord.Interaction, count: int = 1) -> None:
        if not await _ensure_same_voice(interaction):
            return
        
        vc = _get_player(interaction)
        guild_id = interaction.guild_id
        assert guild_id is not None
        guild_player = get_guild_player(self.bot, guild_id)
        count = max(1, min(count, len(guild_player) + 1))
        
        # Remove (count - 1) from queue
        for _ in range(count - 1):
            if guild_player.queue:
                guild_player.queue.pop(0)
        
        next_track = guild_player.get_next(vc.current)
        if next_track is not None:
            vol = min(config.LAVALINK_VOLUME_MAX, max(0, guild_player.volume * config.LAVALINK_VOLUME_MAX // 100))
            await vc.play(next_track, replace=True, volume=vol)
            
            embed = build_now_playing_embed(
                next_track, 0, guild_player.volume,
                is_paused=False, loop_mode=guild_player.loop
            )
            view = MusicControlView(self.bot, paused=False)
            result = await interaction.response.send_message(embed=embed, view=view)
            view.message = getattr(result, "resource", result)
            _start_now_playing_updater(self.bot, guild_id, view)
        else:
            await vc.stop()
            embed = build_info_embed("Queue Empty", f"{Icons.SKIP} Skipped. No more tracks in queue.")
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="seek", description="Seek to position (e.g. 1:30 or 90)")
    @app_commands.describe(position="Position as M:SS or seconds")
    async def seek(self, interaction: discord.Interaction, position: str) -> None:
        if not await _ensure_same_voice(interaction):
            return
        
        vc = _get_player(interaction)
        if vc.current is None:
            embed = build_error_embed("Nothing Playing", "No track is currently playing.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        ms = _parse_position(position)
        if ms is None:
            embed = build_error_embed("Invalid Position", "Use format like `1:30` or `90` (seconds).")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await vc.seek(ms)
        embed = build_success_embed("Seeked", f"{Icons.DURATION} Jumped to **{format_duration(ms)}**")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="queue", description="Show the queue")
    async def queue_cmd(self, interaction: discord.Interaction) -> None:
        guild_id = interaction.guild_id
        assert guild_id is not None
        guild_player = get_guild_player(self.bot, guild_id)
        vc = _get_player(interaction)
        
        embed = build_queue_embed(
            guild_player.queue,
            current_track=vc.current if vc else None
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="nowplaying", description="Show current track and progress")
    async def nowplaying(self, interaction: discord.Interaction) -> None:
        vc = _get_player(interaction)
        if vc is None or not vc.connected or vc.current is None:
            embed = build_idle_embed()
            await interaction.response.send_message(embed=embed)
            return
        
        guild_id = interaction.guild_id
        assert guild_id is not None
        guild_player = get_guild_player(self.bot, guild_id)
        
        embed = build_now_playing_embed(
            vc.current, vc.position, guild_player.volume,
            is_paused=vc.paused, loop_mode=guild_player.loop
        )
        view = MusicControlView(self.bot, paused=vc.paused)
        result = await interaction.response.send_message(embed=embed, view=view)
        view.message = getattr(result, "resource", result)
        _start_now_playing_updater(self.bot, guild_id, view)

    @app_commands.command(name="remove", description="Remove a track from the queue by index")
    @app_commands.describe(index="Queue position (1-based)")
    async def remove(self, interaction: discord.Interaction, index: int) -> None:
        if not await _ensure_same_voice(interaction):
            return
        
        guild_id = interaction.guild_id
        assert guild_id is not None
        guild_player = get_guild_player(self.bot, guild_id)
        
        removed = guild_player.remove(index - 1)
        if removed is None:
            embed = build_error_embed("Invalid Index", f"Position **{index}** is not valid.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = build_success_embed("Removed", f"{Icons.REMOVE} Removed **{removed.title}** from the queue.")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="clear", description="Clear the queue")
    async def clear(self, interaction: discord.Interaction) -> None:
        if not await _ensure_same_voice(interaction):
            return
        
        guild_id = interaction.guild_id
        assert guild_id is not None
        guild_player = get_guild_player(self.bot, guild_id)
        
        count = len(guild_player.queue)
        guild_player.clear()
        
        embed = build_success_embed("Queue Cleared", f"{Icons.REMOVE} Removed **{count}** tracks from the queue.")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="shuffle", description="Shuffle the queue")
    async def shuffle_cmd(self, interaction: discord.Interaction) -> None:
        if not await _ensure_same_voice(interaction):
            return
        
        guild_id = interaction.guild_id
        assert guild_id is not None
        guild_player = get_guild_player(self.bot, guild_id)
        
        if not guild_player.queue:
            embed = build_warning_embed("Queue Empty", "Nothing to shuffle.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        guild_player.shuffle()
        embed = build_success_embed("Shuffled", f"{Icons.SHUFFLE} Queue has been shuffled!")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="volume", description="Get or set volume (0-100)")
    @app_commands.describe(level="Volume level 0-100 (omit to show current)")
    async def volume(self, interaction: discord.Interaction, level: int | None = None) -> None:
        # Volume viewing doesn't require same channel, but changing does
        guild_id = interaction.guild_id
        assert guild_id is not None
        guild_player = get_guild_player(self.bot, guild_id)
        
        if level is None:
            # Just viewing - anyone can do this
            embed = build_volume_embed(guild_player.volume)
            await interaction.response.send_message(embed=embed)
            return
        
        # Changing volume - require same voice channel
        if not await _ensure_same_voice(interaction):
            return
        
        old_level = guild_player.volume
        level = max(0, min(100, level))
        guild_player.volume = level
        
        vc = _get_player(interaction)
        await vc.set_volume(min(config.LAVALINK_VOLUME_MAX, level * config.LAVALINK_VOLUME_MAX // 100))
        
        embed = build_volume_embed(level, changed_by=level - old_level)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="loop", description="Set loop mode: off, track, or queue")
    @app_commands.describe(mode="off / track / queue")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Off", value="off"),
        app_commands.Choice(name="Track", value="track"),
        app_commands.Choice(name="Queue", value="queue"),
    ])
    async def loop_cmd(self, interaction: discord.Interaction, mode: str) -> None:
        if not await _ensure_same_voice(interaction):
            return
        
        guild_id = interaction.guild_id
        assert guild_id is not None
        guild_player = get_guild_player(self.bot, guild_id)
        guild_player.loop = mode
        
        embed = build_loop_embed(mode)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leave", description="Disconnect from voice")
    async def leave(self, interaction: discord.Interaction) -> None:
        if not await _ensure_same_voice(interaction):
            return
        
        vc = _get_player(interaction)
        guild_id = interaction.guild_id
        assert guild_id is not None
        guild_player = get_guild_player(self.bot, guild_id)
        guild_player.clear()
        
        _stop_now_playing_updater(self.bot, guild_id)
        await vc.disconnect()
        
        embed = build_success_embed("Disconnected", f"{Icons.SUCCESS} Left the voice channel.")
        await interaction.response.send_message(embed=embed)
