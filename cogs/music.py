"""Slash commands for playback, queue, volume, loop, and leave."""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

import discord
from discord import app_commands
import mafic
from mafic import SearchType
from player import get_guild_player

if TYPE_CHECKING:
    from bot import MusicBot


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


def _format_duration(ms: int) -> str:
    if ms is None or ms < 0:
        return "?"
    s = ms // 1000
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


async def _ensure_voice(interaction: discord.Interaction) -> discord.VoiceChannel | None:
    channel = interaction.user.voice.channel if interaction.user.voice else None
    if channel is None:
        await interaction.response.send_message(
            "Join a voice channel first.", ephemeral=True
        )
        return None
    return channel


def _get_player(interaction: discord.Interaction) -> mafic.Player | None:
    vc = interaction.guild.voice_client
    if vc is None or not isinstance(vc, mafic.Player):
        return None
    return vc


class MusicCog(discord.app_commands.Group):
    """Music commands."""

    def __init__(self, bot: MusicBot) -> None:
        super().__init__(name="music", description="Music playback and queue")
        self.bot = bot

    @app_commands.command(name="play", description="Play a YouTube URL or search query")
    @app_commands.describe(query="YouTube URL or search query")
    async def play(self, interaction: discord.Interaction, query: str) -> None:
        channel = await _ensure_voice(interaction)
        if channel is None:
            return
        query = query.strip()
        if not query:
            await interaction.response.send_message(
                "Provide a URL or search query.", ephemeral=True
            )
            return

        await interaction.response.defer()

        bot = self.bot
        guild_id = interaction.guild_id
        assert guild_id is not None
        guild_player = get_guild_player(bot, guild_id)

        # Connect if needed (use Mafic Player)
        vc = _get_player(interaction)
        if vc is None:
            try:
                vc = await channel.connect(cls=mafic.Player, self_deaf=True)
            except Exception as e:
                await interaction.followup.send(
                    f"Could not join voice: {e}", ephemeral=True
                )
                return

        # Resolve query: URL or ytsearch
        if query.startswith("http://") or query.startswith("https://"):
            search_query = query
        else:
            search_query = f"ytsearch:{query}"

        try:
            result = await vc.fetch_tracks(search_query, search_type=SearchType.YOUTUBE)
        except Exception as e:
            await interaction.followup.send(
                f"Search failed: {e}", ephemeral=True
            )
            return

        if result is None:
            await interaction.followup.send("No results found.", ephemeral=True)
            return

        # Playlist vs single/list
        if isinstance(result, mafic.Playlist):
            tracks = result.tracks
            guild_player.add_many(tracks)
            name = result.name or "Playlist"
            await interaction.followup.send(
                f"Added **{len(tracks)}** tracks from **{name}** to the queue."
            )
        else:
            tracks = list(result)
            if not tracks:
                await interaction.followup.send("No results found.", ephemeral=True)
                return
            guild_player.add(tracks[0])
            if len(tracks) > 1:
                for t in tracks[1:]:
                    guild_player.add(t)

        # Start playing if nothing is playing
        if vc.current is None:
            next_track = guild_player.get_next(None)
            if next_track is not None:
                vol = min(1000, max(0, guild_player.volume * 10))
                await vc.play(next_track, replace=True, volume=vol)
                await interaction.followup.send(
                    f"Now playing **{next_track.title}**"
                )
                return

        # Reply when we only added to queue (not playlist)
        if not isinstance(result, mafic.Playlist):
            if len(tracks) == 1:
                await interaction.followup.send(
                    f"Added **{tracks[0].title}** to the queue."
                )
            else:
                await interaction.followup.send(
                    f"Added **{len(tracks)}** tracks to the queue."
                )

    @app_commands.command(name="pause", description="Pause playback")
    async def pause(self, interaction: discord.Interaction) -> None:
        if await _ensure_voice(interaction) is None:
            return
        vc = _get_player(interaction)
        if vc is None or not vc.connected:
            await interaction.response.send_message(
                "Not connected to voice.", ephemeral=True
            )
            return
        if vc.paused:
            await interaction.response.send_message(
                "Already paused.", ephemeral=True
            )
            return
        await vc.pause()
        await interaction.response.send_message("Paused.")

    @app_commands.command(name="resume", description="Resume playback")
    async def resume(self, interaction: discord.Interaction) -> None:
        if await _ensure_voice(interaction) is None:
            return
        vc = _get_player(interaction)
        if vc is None or not vc.connected:
            await interaction.response.send_message(
                "Not connected to voice.", ephemeral=True
            )
            return
        if not vc.paused:
            await interaction.response.send_message(
                "Not paused.", ephemeral=True
            )
            return
        await vc.resume()
        await interaction.response.send_message("Resumed.")

    @app_commands.command(name="stop", description="Stop playback and clear queue")
    async def stop(self, interaction: discord.Interaction) -> None:
        if await _ensure_voice(interaction) is None:
            return
        vc = _get_player(interaction)
        guild_id = interaction.guild_id
        assert guild_id is not None
        guild_player = get_guild_player(self.bot, guild_id)
        guild_player.clear()
        if vc is not None and vc.connected:
            await vc.stop()
        await interaction.response.send_message("Stopped and queue cleared.")

    @app_commands.command(name="skip", description="Skip current track or N tracks")
    @app_commands.describe(count="Number of tracks to skip (default 1)")
    async def skip(self, interaction: discord.Interaction, count: int = 1) -> None:
        if await _ensure_voice(interaction) is None:
            return
        vc = _get_player(interaction)
        if vc is None or not vc.connected:
            await interaction.response.send_message(
                "Not connected to voice.", ephemeral=True
            )
            return
        guild_id = interaction.guild_id
        assert guild_id is not None
        guild_player = get_guild_player(self.bot, guild_id)
        count = max(1, min(count, len(guild_player) + 1))
        # Remove (count - 1) from queue, then play next
        for _ in range(count - 1):
            if guild_player.queue:
                guild_player.queue.pop(0)
        next_track = guild_player.get_next(vc.current)
        if next_track is not None:
            vol = min(1000, max(0, guild_player.volume * 10))
            await vc.play(next_track, replace=True, volume=vol)
            await interaction.response.send_message(
                f"Skipped. Now playing **{next_track.title}**"
            )
        else:
            await vc.stop()
            await interaction.response.send_message("Skipped. Queue empty.")

    @app_commands.command(name="seek", description="Seek to position (e.g. 1:30 or 90)")
    @app_commands.describe(position="Position as M:SS or seconds")
    async def seek(self, interaction: discord.Interaction, position: str) -> None:
        if await _ensure_voice(interaction) is None:
            return
        vc = _get_player(interaction)
        if vc is None or not vc.connected or vc.current is None:
            await interaction.response.send_message(
                "Nothing playing.", ephemeral=True
            )
            return
        ms = _parse_position(position)
        if ms is None:
            await interaction.response.send_message(
                "Invalid position. Use M:SS or seconds.", ephemeral=True
            )
            return
        await vc.seek(ms)
        await interaction.response.send_message(
            f"Seeked to {_format_duration(ms)}."
        )

    @app_commands.command(name="queue", description="Show the queue")
    async def queue_cmd(self, interaction: discord.Interaction) -> None:
        guild_id = interaction.guild_id
        assert guild_id is not None
        guild_player = get_guild_player(self.bot, guild_id)
        vc = _get_player(interaction)
        lines = []
        if vc and vc.current:
            lines.append(f"**Now playing:** {vc.current.title}")
        if not guild_player.queue and not (vc and vc.current):
            await interaction.response.send_message("Queue is empty.")
            return
        for i, t in enumerate(guild_player.queue[:15], 1):
            lines.append(f"`{i}.` {t.title} ({_format_duration(t.length)})")
        if len(guild_player.queue) > 15:
            lines.append(f"... and {len(guild_player.queue) - 15} more.")
        await interaction.response.send_message("\n".join(lines))

    @app_commands.command(name="nowplaying", description="Show current track and progress")
    async def nowplaying(self, interaction: discord.Interaction) -> None:
        vc = _get_player(interaction)
        if vc is None or not vc.connected or vc.current is None:
            await interaction.response.send_message("Nothing playing.")
            return
        t = vc.current
        guild_id = interaction.guild_id
        assert guild_id is not None
        guild_player = get_guild_player(self.bot, guild_id)
        pos = vc.position
        length = t.length
        pct = (pos / length * 100) if length else 0
        bar_len = 12
        filled = int(bar_len * pct / 100)
        bar = "█" * filled + "░" * (bar_len - filled)
        await interaction.response.send_message(
            f"**{t.title}**\n"
            f"`[{bar}]` {_format_duration(pos)} / {_format_duration(length)}\n"
            f"Volume: {guild_player.volume}%"
        )

    @app_commands.command(name="remove", description="Remove a track from the queue by index")
    @app_commands.describe(index="Queue position (1-based)")
    async def remove(self, interaction: discord.Interaction, index: int) -> None:
        guild_id = interaction.guild_id
        assert guild_id is not None
        guild_player = get_guild_player(self.bot, guild_id)
        # 1-based for user
        removed = guild_player.remove(index - 1)
        if removed is None:
            await interaction.response.send_message(
                "Invalid queue index.", ephemeral=True
            )
            return
        await interaction.response.send_message(
            f"Removed **{removed.title}** from the queue."
        )

    @app_commands.command(name="clear", description="Clear the queue")
    async def clear(self, interaction: discord.Interaction) -> None:
        guild_id = interaction.guild_id
        assert guild_id is not None
        guild_player = get_guild_player(self.bot, guild_id)
        guild_player.clear()
        await interaction.response.send_message("Queue cleared.")

    @app_commands.command(name="shuffle", description="Shuffle the queue")
    async def shuffle_cmd(self, interaction: discord.Interaction) -> None:
        guild_id = interaction.guild_id
        assert guild_id is not None
        guild_player = get_guild_player(self.bot, guild_id)
        if not guild_player.queue:
            await interaction.response.send_message("Queue is empty.", ephemeral=True)
            return
        guild_player.shuffle()
        await interaction.response.send_message("Queue shuffled.")

    @app_commands.command(name="volume", description="Get or set volume (0-100)")
    @app_commands.describe(level="Volume level 0-100 (omit to show current)")
    async def volume(self, interaction: discord.Interaction, level: int | None = None) -> None:
        guild_id = interaction.guild_id
        assert guild_id is not None
        guild_player = get_guild_player(self.bot, guild_id)
        if level is None:
            await interaction.response.send_message(
                f"Volume is **{guild_player.volume}%**."
            )
            return
        level = max(0, min(100, level))
        guild_player.volume = level
        vc = _get_player(interaction)
        if vc is not None and vc.connected:
            await vc.set_volume(level * 10)
        await interaction.response.send_message(f"Volume set to **{level}%**.")

    @app_commands.command(name="loop", description="Set loop mode: off, track, or queue")
    @app_commands.describe(mode="off / track / queue")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Off", value="off"),
        app_commands.Choice(name="Track", value="track"),
        app_commands.Choice(name="Queue", value="queue"),
    ])
    async def loop_cmd(self, interaction: discord.Interaction, mode: str) -> None:
        guild_id = interaction.guild_id
        assert guild_id is not None
        guild_player = get_guild_player(self.bot, guild_id)
        guild_player.loop = mode
        await interaction.response.send_message(f"Loop set to **{mode}**.")

    @app_commands.command(name="leave", description="Disconnect from voice")
    async def leave(self, interaction: discord.Interaction) -> None:
        vc = _get_player(interaction)
        if vc is None or not vc.connected:
            await interaction.response.send_message(
                "Not in a voice channel.", ephemeral=True
            )
            return
        guild_id = interaction.guild_id
        assert guild_id is not None
        guild_player = get_guild_player(self.bot, guild_id)
        guild_player.clear()
        await vc.disconnect()
        await interaction.response.send_message("Left voice channel.")

