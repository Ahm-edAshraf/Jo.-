"""
Modern Design System for Discord Music Bot.
Centralized styling, colors, emojis, and embed builders.
"""
from __future__ import annotations

from typing import TYPE_CHECKING
import discord

if TYPE_CHECKING:
    from mafic import Track


# ═══════════════════════════════════════════════════════════════════════════════
# COLOR PALETTE - Premium Discord-inspired colors
# ═══════════════════════════════════════════════════════════════════════════════

class Colors:
    """Modern color palette for embeds."""
    # Primary states
    PLAYING = 0x5865F2      # Discord Blurple - active playback
    PAUSED = 0xFEE75C       # Yellow - paused/warning
    SUCCESS = 0x57F287      # Green - success actions
    ERROR = 0xED4245        # Red - errors
    IDLE = 0x2B2D31         # Discord Dark - idle/empty
    INFO = 0x5865F2         # Blurple - informational
    
    # Accent colors
    QUEUE = 0x9B59B6        # Purple - queue display
    FILTER = 0xE91E63       # Pink - audio filters
    VOLUME = 0x3498DB       # Blue - volume changes
    SEARCH = 0xF39C12       # Orange - search results


# ═══════════════════════════════════════════════════════════════════════════════
# EMOJI ICONS - Consistent iconography
# ═══════════════════════════════════════════════════════════════════════════════

class Icons:
    """Unicode emoji icons for UI consistency."""
    # Playback controls
    PLAY = "▶️"
    PAUSE = "⏸️"
    RESUME = "▶️"
    SKIP = "⏭️"
    PREVIOUS = "⏮️"
    STOP = "⏹️"
    
    # Volume
    VOLUME_HIGH = "🔊"
    VOLUME_LOW = "🔉"
    VOLUME_MUTE = "🔇"
    VOLUME_UP = "🔺"
    VOLUME_DOWN = "🔻"
    
    # Queue & tracks
    MUSIC = "🎵"
    QUEUE = "📋"
    PLAYLIST = "📑"
    ADD = "➕"
    REMOVE = "➖"
    
    # States
    LOOP = "🔁"
    LOOP_ONE = "🔂"
    SHUFFLE = "🔀"
    LOADING = "⏳"
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    
    # Progress
    DURATION = "⏱️"
    LIVE = "🔴"
    
    # Sources
    YOUTUBE = "📺"
    SOUNDCLOUD = "☁️"
    SPOTIFY = "💚"
    SEARCH = "🔍"


# ═══════════════════════════════════════════════════════════════════════════════
# PROGRESS BAR STYLES
# ═══════════════════════════════════════════════════════════════════════════════

# Modern progress bar characters
_BAR_FILL = "━"
_BAR_EMPTY = "─"
_BAR_HEAD = "◉"
_BAR_LENGTH = 14


def format_progress_bar(percent: float) -> str:
    """Create a modern Spotify-style progress bar.
    
    Args:
        percent: Progress percentage (0-100)
        
    Returns:
        Unicode progress bar string like: ━━━━◉─────────
    """
    percent = max(0.0, min(100.0, percent))
    filled = int((percent / 100) * (_BAR_LENGTH - 1))
    
    bar = _BAR_FILL * filled + _BAR_HEAD + _BAR_EMPTY * (_BAR_LENGTH - 1 - filled)
    return f"`{bar}`"


def format_duration(ms: int | None) -> str:
    """Format milliseconds to human-readable duration.
    
    Args:
        ms: Duration in milliseconds
        
    Returns:
        Formatted string like "3:45" or "1:23:45"
    """
    if ms is None or ms < 0:
        return "∞"
    
    seconds = ms // 1000
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def get_source_emoji(source: str | None) -> str:
    """Get emoji for track source."""
    if source is None:
        return Icons.MUSIC
    
    source = source.lower()
    if "youtube" in source:
        return Icons.YOUTUBE
    elif "soundcloud" in source:
        return Icons.SOUNDCLOUD
    elif "spotify" in source:
        return Icons.SPOTIFY
    return Icons.MUSIC


# ═══════════════════════════════════════════════════════════════════════════════
# EMBED BUILDERS
# ═══════════════════════════════════════════════════════════════════════════════

def build_now_playing_embed(
    track: Track,
    position_ms: int,
    volume: int,
    is_paused: bool = False,
    loop_mode: str = "off"
) -> discord.Embed:
    """Build a premium now-playing embed.
    
    Args:
        track: The currently playing track
        position_ms: Current playback position in milliseconds
        volume: Current volume (0-100)
        is_paused: Whether playback is paused
        loop_mode: Current loop mode (off/track/queue)
        
    Returns:
        Styled discord.Embed
    """
    length = track.length or 0
    is_stream = getattr(track, "stream", False)
    
    # Calculate progress
    if is_stream:
        progress_text = f"{Icons.LIVE} **LIVE**"
        percent = 0
    else:
        percent = (position_ms / length * 100) if length else 0
        pos_str = format_duration(position_ms)
        len_str = format_duration(length)
        bar = format_progress_bar(percent)
        progress_text = f"{bar}\n{Icons.DURATION} **{pos_str}** / {len_str}"
    
    # Determine color based on state
    color = Colors.PAUSED if is_paused else Colors.PLAYING
    
    # Get source info
    source = getattr(track, "source", None) or "Unknown"
    source_emoji = get_source_emoji(source)
    source_label = source.replace("_", " ").title()
    
    # Build status line
    status_icon = Icons.PAUSE if is_paused else Icons.PLAY
    status_text = "Paused" if is_paused else "Now Playing"
    
    # Title (truncate if needed)
    title = (track.title or "Unknown Track")[:100]
    artist = getattr(track, "author", None) or "Unknown Artist"
    
    embed = discord.Embed(
        title=f"{status_icon} {title}",
        url=getattr(track, "uri", None),
        color=color,
        timestamp=discord.utils.utcnow(),
    )
    
    embed.set_author(
        name=f"{source_emoji} {artist}",
        icon_url=None
    )
    
    # Progress field
    embed.add_field(
        name="Progress",
        value=progress_text,
        inline=False
    )
    
    # Info row
    volume_icon = Icons.VOLUME_HIGH if volume > 50 else (Icons.VOLUME_LOW if volume > 0 else Icons.VOLUME_MUTE)
    
    embed.add_field(
        name=f"{volume_icon} Volume",
        value=f"**{volume}%**",
        inline=True
    )
    
    embed.add_field(
        name=f"{source_emoji} Source",
        value=f"**{source_label}**",
        inline=True
    )
    
    # Loop indicator
    if loop_mode != "off":
        loop_icon = Icons.LOOP_ONE if loop_mode == "track" else Icons.LOOP
        embed.add_field(
            name=f"{loop_icon} Loop",
            value=f"**{loop_mode.title()}**",
            inline=True
        )
    
    # Thumbnail
    artwork = getattr(track, "artwork_url", None)
    if artwork:
        embed.set_thumbnail(url=artwork)
    
    embed.set_footer(text=f"{status_text} • Use buttons below to control playback")
    
    return embed


def build_queue_embed(
    tracks: list,
    current_track=None,
    page: int = 1,
    per_page: int = 10
) -> discord.Embed:
    """Build a styled queue embed.
    
    Args:
        tracks: List of queued tracks
        current_track: Currently playing track
        page: Current page number
        per_page: Tracks per page
        
    Returns:
        Styled discord.Embed
    """
    embed = discord.Embed(
        title=f"{Icons.QUEUE} Music Queue",
        color=Colors.QUEUE,
        timestamp=discord.utils.utcnow(),
    )
    
    # Now playing section
    if current_track:
        title = (current_track.title or "Unknown")[:50]
        duration = format_duration(current_track.length)
        embed.add_field(
            name=f"{Icons.PLAY} Now Playing",
            value=f"**{title}** `{duration}`",
            inline=False
        )
    
    # Queue section
    if not tracks:
        embed.add_field(
            name=f"{Icons.MUSIC} Up Next",
            value="*Queue is empty. Add some tracks!*",
            inline=False
        )
    else:
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_tracks = tracks[start_idx:end_idx]
        
        lines = []
        for i, track in enumerate(page_tracks, start=start_idx + 1):
            title = (track.title or "Unknown")[:40]
            duration = format_duration(track.length)
            lines.append(f"`{i}.` **{title}** `{duration}`")
        
        embed.add_field(
            name=f"{Icons.MUSIC} Up Next ({len(tracks)} tracks)",
            value="\n".join(lines) if lines else "*Empty*",
            inline=False
        )
        
        # Pagination info
        total_pages = (len(tracks) + per_page - 1) // per_page
        if total_pages > 1:
            embed.set_footer(text=f"Page {page}/{total_pages} • {len(tracks)} tracks in queue")
        else:
            embed.set_footer(text=f"{len(tracks)} tracks in queue")
    
    return embed


def build_success_embed(
    title: str,
    description: str = "",
    footer: str = ""
) -> discord.Embed:
    """Build a success embed.
    
    Args:
        title: Success message title
        description: Optional description
        footer: Optional footer text
        
    Returns:
        Styled discord.Embed
    """
    embed = discord.Embed(
        title=f"{Icons.SUCCESS} {title}",
        description=description or None,
        color=Colors.SUCCESS,
        timestamp=discord.utils.utcnow(),
    )
    if footer:
        embed.set_footer(text=footer)
    return embed


def build_error_embed(
    title: str,
    description: str = "",
    footer: str = ""
) -> discord.Embed:
    """Build an error embed.
    
    Args:
        title: Error message title
        description: Optional description
        footer: Optional footer text
        
    Returns:
        Styled discord.Embed
    """
    embed = discord.Embed(
        title=f"{Icons.ERROR} {title}",
        description=description or None,
        color=Colors.ERROR,
        timestamp=discord.utils.utcnow(),
    )
    if footer:
        embed.set_footer(text=footer)
    return embed


def build_warning_embed(
    title: str,
    description: str = "",
    footer: str = ""
) -> discord.Embed:
    """Build a warning embed.
    
    Args:
        title: Warning message title
        description: Optional description
        footer: Optional footer text
        
    Returns:
        Styled discord.Embed
    """
    embed = discord.Embed(
        title=f"{Icons.WARNING} {title}",
        description=description or None,
        color=Colors.PAUSED,
        timestamp=discord.utils.utcnow(),
    )
    if footer:
        embed.set_footer(text=footer)
    return embed


def build_info_embed(
    title: str,
    description: str = "",
    footer: str = ""
) -> discord.Embed:
    """Build an info embed.
    
    Args:
        title: Info message title
        description: Optional description
        footer: Optional footer text
        
    Returns:
        Styled discord.Embed
    """
    embed = discord.Embed(
        title=f"{Icons.INFO} {title}",
        description=description or None,
        color=Colors.INFO,
        timestamp=discord.utils.utcnow(),
    )
    if footer:
        embed.set_footer(text=footer)
    return embed


def build_loading_embed(message: str = "Loading...") -> discord.Embed:
    """Build a loading state embed.
    
    Args:
        message: Loading message
        
    Returns:
        Styled discord.Embed
    """
    return discord.Embed(
        title=f"{Icons.LOADING} {message}",
        color=Colors.INFO,
    )


def build_idle_embed() -> discord.Embed:
    """Build an idle/empty state embed.
    
    Returns:
        Styled discord.Embed
    """
    embed = discord.Embed(
        title=f"{Icons.MUSIC} Nothing Playing",
        description="The queue is empty. Use `/music play` to add tracks!",
        color=Colors.IDLE,
        timestamp=discord.utils.utcnow(),
    )
    embed.set_footer(text="Ready to play")
    return embed


def build_added_to_queue_embed(
    track,
    position: int = 0
) -> discord.Embed:
    """Build embed for track added to queue.
    
    Args:
        track: The track that was added
        position: Position in queue (0 = playing now)
        
    Returns:
        Styled discord.Embed
    """
    title = (track.title or "Unknown")[:100]
    duration = format_duration(track.length)
    source = getattr(track, "source", "Unknown")
    source_emoji = get_source_emoji(source)
    
    if position == 0:
        embed_title = f"{Icons.PLAY} Now Playing"
        color = Colors.PLAYING
    else:
        embed_title = f"{Icons.ADD} Added to Queue"
        color = Colors.SUCCESS
    
    embed = discord.Embed(
        title=embed_title,
        description=f"**{title}**",
        color=color,
        timestamp=discord.utils.utcnow(),
    )
    
    embed.add_field(name="Duration", value=f"`{duration}`", inline=True)
    embed.add_field(name="Source", value=f"{source_emoji} {source.title()}", inline=True)
    
    if position > 0:
        embed.add_field(name="Position", value=f"#{position}", inline=True)
    
    artwork = getattr(track, "artwork_url", None)
    if artwork:
        embed.set_thumbnail(url=artwork)
    
    return embed


def build_playlist_added_embed(
    playlist_name: str,
    track_count: int
) -> discord.Embed:
    """Build embed for playlist added to queue.
    
    Args:
        playlist_name: Name of the playlist
        track_count: Number of tracks added
        
    Returns:
        Styled discord.Embed
    """
    embed = discord.Embed(
        title=f"{Icons.PLAYLIST} Playlist Added",
        description=f"**{playlist_name}**",
        color=Colors.SUCCESS,
        timestamp=discord.utils.utcnow(),
    )
    embed.add_field(
        name="Tracks Added",
        value=f"`{track_count}` tracks",
        inline=True
    )
    return embed


def build_volume_embed(volume: int, changed_by: int = 0) -> discord.Embed:
    """Build embed for volume change.
    
    Args:
        volume: Current volume (0-100)
        changed_by: Delta of volume change
        
    Returns:
        Styled discord.Embed
    """
    if volume == 0:
        icon = Icons.VOLUME_MUTE
    elif volume < 50:
        icon = Icons.VOLUME_LOW
    else:
        icon = Icons.VOLUME_HIGH
    
    # Visual volume bar
    filled = volume // 10
    bar = "█" * filled + "░" * (10 - filled)
    
    embed = discord.Embed(
        title=f"{icon} Volume",
        description=f"`{bar}` **{volume}%**",
        color=Colors.VOLUME,
    )
    
    if changed_by != 0:
        direction = Icons.VOLUME_UP if changed_by > 0 else Icons.VOLUME_DOWN
        embed.set_footer(text=f"{direction} {'+' if changed_by > 0 else ''}{changed_by}%")
    
    return embed


def build_filter_embed(
    filter_name: str,
    applied: bool = True
) -> discord.Embed:
    """Build embed for filter application.
    
    Args:
        filter_name: Name of the filter
        applied: Whether filter was applied or removed
        
    Returns:
        Styled discord.Embed
    """
    if applied:
        title = f"{Icons.SUCCESS} {filter_name} Applied"
        desc = f"Audio filter **{filter_name}** is now active."
    else:
        title = f"{Icons.INFO} {filter_name} Removed"
        desc = f"Audio filter **{filter_name}** has been removed."
    
    embed = discord.Embed(
        title=title,
        description=desc,
        color=Colors.FILTER,
        timestamp=discord.utils.utcnow(),
    )
    return embed


def build_loop_embed(mode: str) -> discord.Embed:
    """Build embed for loop mode change.
    
    Args:
        mode: Loop mode (off/track/queue)
        
    Returns:
        Styled discord.Embed
    """
    if mode == "off":
        icon = Icons.INFO
        desc = "Loop is **disabled**."
    elif mode == "track":
        icon = Icons.LOOP_ONE
        desc = "Looping **current track**."
    else:
        icon = Icons.LOOP
        desc = "Looping **entire queue**."
    
    embed = discord.Embed(
        title=f"{icon} Loop Mode: {mode.title()}",
        description=desc,
        color=Colors.INFO,
    )
    return embed


def build_search_results_embed(
    query: str,
    tracks: list,
    max_results: int = 5
) -> discord.Embed:
    """Build embed for search results selection.
    
    Args:
        query: The original search query
        tracks: List of found tracks
        max_results: Maximum results to show
        
    Returns:
        Styled discord.Embed
    """
    embed = discord.Embed(
        title=f"{Icons.SEARCH} Search Results",
        description=f"Found **{len(tracks)}** results for: `{query[:50]}`\n\n"
                    f"Select a track from the dropdown below:",
        color=Colors.SEARCH,
        timestamp=discord.utils.utcnow(),
    )
    
    # Display top results
    lines = []
    for i, track in enumerate(tracks[:max_results], start=1):
        title = (track.title or "Unknown")[:45]
        duration = format_duration(track.length)
        author = getattr(track, "author", "Unknown")[:25]
        source_emoji = get_source_emoji(getattr(track, "source", None))
        
        lines.append(f"`{i}.` {source_emoji} **{title}**\n"
                     f"     └ {author} • `{duration}`")
    
    embed.add_field(
        name="🎵 Top Results",
        value="\n".join(lines) if lines else "*No results*",
        inline=False
    )
    
    embed.set_footer(text="Select within 30 seconds or the first result will be used")
    
    return embed
