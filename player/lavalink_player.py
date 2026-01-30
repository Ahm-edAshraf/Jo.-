"""Queue and playback state per guild. Works with Mafic Player (guild.voice_client)."""
from __future__ import annotations

import random
import time
from typing import Any

from mafic import Track


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Maximum tracks allowed in queue (prevents memory issues on limited hosts)
MAX_QUEUE_SIZE = 200

# Default volume (0-100)
DEFAULT_VOLUME = 25


# ═══════════════════════════════════════════════════════════════════════════════
# GUILD PLAYER
# ═══════════════════════════════════════════════════════════════════════════════

class GuildPlayer:
    """Per-guild queue and loop state. Use with Mafic Player as voice_client."""

    __slots__ = ("guild_id", "queue", "loop", "volume", "last_activity")

    def __init__(self, guild_id: int) -> None:
        self.guild_id = guild_id
        self.queue: list[Track] = []
        self.loop: str = "off"  # "off" | "track" | "queue"
        self.volume: int = DEFAULT_VOLUME  # 0-100
        self.last_activity: float = time.time()  # For idle tracking

    def _touch(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = time.time()

    def add(self, track: Track) -> bool:
        """Add a track to the queue.
        
        Returns:
            True if added, False if queue is full.
        """
        self._touch()
        if len(self.queue) >= MAX_QUEUE_SIZE:
            return False
        self.queue.append(track)
        return True

    def add_many(self, tracks: list[Track]) -> int:
        """Add multiple tracks to the queue (up to limit).
        
        Returns:
            Number of tracks actually added.
        """
        self._touch()
        available = MAX_QUEUE_SIZE - len(self.queue)
        if available <= 0:
            return 0
        to_add = tracks[:available]
        self.queue.extend(to_add)
        return len(to_add)

    def clear(self) -> None:
        """Clear the queue."""
        self._touch()
        self.queue.clear()

    def remove(self, index: int) -> Track | None:
        """Remove a track by index.
        
        Args:
            index: 0-based index.
            
        Returns:
            Removed track or None if invalid index.
        """
        self._touch()
        if 0 <= index < len(self.queue):
            return self.queue.pop(index)
        return None

    def shuffle(self) -> None:
        """Shuffle the queue."""
        self._touch()
        random.shuffle(self.queue)

    def get_next(self, current_track: Track | None) -> Track | None:
        """Get the next track considering loop mode.
        
        Args:
            current_track: The currently playing track.
            
        Returns:
            Next track to play, or None if queue is empty.
        """
        self._touch()
        
        if self.loop == "track" and current_track is not None:
            return current_track
        
        if self.queue:
            next_track = self.queue.pop(0)
            # For queue loop, re-add the track we just took
            if self.loop == "queue":
                self.queue.append(next_track)
            return next_track
        
        # Queue is empty
        if self.loop == "queue" and current_track is not None:
            # If queue loop is on and we finished, loop the current track
            return current_track
        
        return None

    def is_idle(self, timeout_seconds: float = 300) -> bool:
        """Check if the player has been idle for the specified time.
        
        Args:
            timeout_seconds: Idle timeout in seconds (default 5 minutes).
            
        Returns:
            True if idle for longer than timeout.
        """
        return (time.time() - self.last_activity) > timeout_seconds

    @property
    def queue_duration_ms(self) -> int:
        """Get total duration of queued tracks in milliseconds."""
        return sum(t.length or 0 for t in self.queue)

    def __len__(self) -> int:
        return len(self.queue)

    def __repr__(self) -> str:
        return f"<GuildPlayer guild_id={self.guild_id} queue={len(self.queue)} loop={self.loop} volume={self.volume}>"


# ═══════════════════════════════════════════════════════════════════════════════
# FACTORY FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def get_guild_player(client: Any, guild_id: int) -> GuildPlayer:
    """Get or create GuildPlayer for the guild.
    
    Attaches to client._guild_players dictionary.
    
    Args:
        client: The Discord bot client.
        guild_id: Guild ID to get player for.
        
    Returns:
        GuildPlayer instance for the guild.
    """
    if not hasattr(client, "_guild_players"):
        client._guild_players = {}
    if guild_id not in client._guild_players:
        client._guild_players[guild_id] = GuildPlayer(guild_id)
    return client._guild_players[guild_id]
