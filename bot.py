"""Discord music bot entry point. Uses Mafic + Lavalink for playback."""
import discord
from discord import app_commands
import mafic
from mafic.events import EndReason, TrackEndEvent

import config
from cogs.music import MusicCog
from cogs.filters import FiltersCog
from player import get_guild_player


class MusicBot(discord.Client):
    """Bot with Mafic NodePool for Lavalink voice."""

    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.voice_states = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.pool: mafic.NodePool[MusicBot] | None = None

    async def setup_hook(self) -> None:
        """Create Lavalink node and add command groups."""
        self.pool = mafic.NodePool(self)
        await self.pool.create_node(
            host=config.LAVALINK_HOST,
            port=config.LAVALINK_PORT,
            label="main",
            password=config.LAVALINK_PASSWORD,
            secure=config.LAVALINK_SSL,
        )
        self.tree.add_command(MusicCog(self))
        self.tree.add_command(FiltersCog(self))

    async def on_ready(self) -> None:
        """Sync slash commands and log."""
        await self.tree.sync()
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("Slash commands synced.")

    async def on_track_end(self, event: TrackEndEvent) -> None:
        """Play next track from queue when current finishes."""
        if event.reason != EndReason.FINISHED:
            return
        player = event.player
        if not hasattr(player, "guild"):
            return
        guild_id = player.guild.id
        guild_player = get_guild_player(self, guild_id)
        next_track = guild_player.get_next(event.track)
        if next_track is not None:
            vol = min(1000, max(0, guild_player.volume * 10))
            await player.play(next_track, replace=True, volume=vol)
        else:
            await player.stop()

    async def close(self) -> None:
        """Close pool and client."""
        if self.pool:
            await self.pool.close()
        await super().close()


def main() -> None:
    if not config.DISCORD_TOKEN:
        print("Missing DISCORD_TOKEN. Set it in .env or environment.")
        return
    bot = MusicBot()
    bot.run(config.DISCORD_TOKEN)


if __name__ == "__main__":
    main()
