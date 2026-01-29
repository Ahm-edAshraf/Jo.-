"""Queue and playback state per guild. Works with Mafic Player (guild.voice_client)."""
from __future__ import annotations

import random
from typing import Any

from mafic import Track


class GuildPlayer:
    """Per-guild queue and loop state. Use with Mafic Player as voice_client."""

    __slots__ = ("guild_id", "queue", "loop", "volume")

    def __init__(self, guild_id: int) -> None:
        self.guild_id = guild_id
        self.queue: list[Track] = []
        self.loop: str = "off"  # "off" | "track" | "queue"
        self.volume: int = 100  # 0-100, mapped to Lavalink 0-1000 when playing

    def add(self, track: Track) -> None:
        self.queue.append(track)

    def add_many(self, tracks: list[Track]) -> None:
        self.queue.extend(tracks)

    def clear(self) -> None:
        self.queue.clear()

    def remove(self, index: int) -> Track | None:
        if 0 <= index < len(self.queue):
            return self.queue.pop(index)
        return None

    def shuffle(self) -> None:
        random.shuffle(self.queue)

    def get_next(self, current_track: Track | None) -> Track | None:
        """Return the next track to play considering loop mode. Does not mutate queue for loop queue."""
        if self.loop == "track" and current_track is not None:
            return current_track
        if self.queue:
            return self.queue.pop(0)
        if self.loop == "queue" and current_track is not None:
            self.queue.append(current_track)
            return self.queue.pop(0)
        return None

    def __len__(self) -> int:
        return len(self.queue)


def get_guild_player(client: Any, guild_id: int) -> GuildPlayer:
    """Get or create GuildPlayer for the guild. Attaches to client._guild_players."""
    if not hasattr(client, "_guild_players"):
        client._guild_players = {}
    if guild_id not in client._guild_players:
        client._guild_players[guild_id] = GuildPlayer(guild_id)
    return client._guild_players[guild_id]
