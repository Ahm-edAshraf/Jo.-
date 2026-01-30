"""Discord music bot entry point. Uses Mafic + Lavalink for playback."""
from __future__ import annotations

import asyncio
import os
import signal
import sys
from typing import TYPE_CHECKING

import discord
from discord import app_commands
import mafic
from mafic.events import EndReason, TrackEndEvent

import config
from cogs.music import MusicCog
from cogs.filters import FiltersCog
from player import get_guild_player


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Idle disconnect timeout (seconds) - disconnect if no activity for this long
IDLE_TIMEOUT = 300  # 5 minutes

# Check for idle connections every N seconds
IDLE_CHECK_INTERVAL = 60


# ═══════════════════════════════════════════════════════════════════════════════
# MUSIC BOT CLIENT
# ═══════════════════════════════════════════════════════════════════════════════

class MusicBot(discord.Client):
    """Bot with Mafic NodePool for Lavalink voice."""

    def __init__(self) -> None:
        # Minimal intents for efficiency
        intents = discord.Intents.default()
        intents.guilds = True
        intents.voice_states = True
        
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.pool: mafic.NodePool[MusicBot] | None = None
        self._idle_task: asyncio.Task | None = None
        self._shutdown_event = asyncio.Event()

    async def setup_hook(self) -> None:
        """Add command groups. Lavalink connects in on_ready."""
        self.tree.add_command(MusicCog(self))
        self.tree.add_command(FiltersCog(self))

    async def on_ready(self) -> None:
        """Connect to Lavalink, sync commands if needed, start idle checker."""
        # Connect to Lavalink
        if self.pool is None:
            self.pool = mafic.NodePool(self)
            try:
                await self.pool.create_node(
                    host=config.LAVALINK_HOST,
                    port=config.LAVALINK_PORT,
                    label="main",
                    password=config.LAVALINK_PASSWORD,
                    secure=config.LAVALINK_SSL,
                )
                print("✅ Lavalink node connected.")
            except Exception as e:
                print(f"❌ Lavalink connection failed: {e}")
                print("   Bot is online but /music will not work until Lavalink is reachable.")
        
        # Sync commands only if FORCE_SYNC is set or first run
        # This saves API calls on restarts
        should_sync = os.getenv("FORCE_SYNC", "false").lower() in ("true", "1", "yes")
        
        if should_sync:
            if config.GUILD_ID:
                guild_id = int(config.GUILD_ID)
                await self.tree.sync(guild=discord.Object(id=guild_id))
                print(f"✅ Slash commands synced to guild {guild_id} (instant).")
            else:
                await self.tree.sync()
                print("✅ Slash commands synced globally (may take up to 1 hour).")
        else:
            print("ℹ️  Skipping command sync (set FORCE_SYNC=true to sync).")
        
        print(f"🎵 Logged in as {self.user} (ID: {self.user.id})")
        
        # Start idle checker
        if self._idle_task is None or self._idle_task.done():
            self._idle_task = asyncio.create_task(self._idle_disconnect_loop())
            print("✅ Idle disconnect checker started.")

    async def _idle_disconnect_loop(self) -> None:
        """Background loop to disconnect from idle voice channels."""
        await self.wait_until_ready()
        
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(IDLE_CHECK_INTERVAL)
                
                # Check all voice clients
                for vc in list(self.voice_clients):
                    if not isinstance(vc, mafic.Player):
                        continue
                    
                    guild = vc.guild
                    if not guild:
                        continue
                    
                    guild_player = get_guild_player(self, guild.id)
                    
                    # Check if voice channel is empty (only bot)
                    voice_channel = vc.channel
                    if voice_channel:
                        members = [m for m in voice_channel.members if not m.bot]
                        if not members:
                            # Channel is empty, disconnect
                            print(f"🔇 Disconnecting from empty channel in {guild.name}")
                            guild_player.clear()
                            await vc.disconnect()
                            continue
                    
                    # Check if player is idle (no music for a while)
                    if not vc.current and guild_player.is_idle(IDLE_TIMEOUT):
                        print(f"💤 Disconnecting from idle channel in {guild.name}")
                        guild_player.clear()
                        await vc.disconnect()
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️ Idle check error: {e}")

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
            vol = min(config.LAVALINK_VOLUME_MAX, max(0, guild_player.volume * config.LAVALINK_VOLUME_MAX // 100))
            await player.play(next_track, replace=True, volume=vol)
        else:
            await player.stop()

    async def close(self) -> None:
        """Graceful shutdown: stop tasks, close pool, disconnect clients."""
        print("🛑 Shutting down...")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Cancel idle task
        if self._idle_task and not self._idle_task.done():
            self._idle_task.cancel()
            try:
                await self._idle_task
            except asyncio.CancelledError:
                pass
        
        # Cancel now-playing updaters
        if hasattr(self, "_np_tasks"):
            for task in self._np_tasks.values():
                if not task.done():
                    task.cancel()
            self._np_tasks.clear()
        
        # Disconnect all voice clients
        for vc in list(self.voice_clients):
            try:
                await vc.disconnect()
            except Exception:
                pass
        
        # Close Lavalink pool
        if self.pool:
            try:
                await self.pool.close()
            except Exception:
                pass
        
        await super().close()
        print("👋 Goodbye!")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    """Start the bot."""
    if not config.DISCORD_TOKEN:
        print("❌ Missing DISCORD_TOKEN. Set it in .env or environment.")
        return
    
    bot = MusicBot()
    
    # Handle graceful shutdown signals (important for Railway/Docker)
    def handle_shutdown(sig, frame):
        print(f"\n📡 Received signal {sig}, initiating shutdown...")
        asyncio.create_task(bot.close())
    
    # Register signal handlers (Unix signals, may not work on Windows)
    try:
        signal.signal(signal.SIGTERM, handle_shutdown)
        signal.signal(signal.SIGINT, handle_shutdown)
    except (ValueError, OSError):
        # Signals may not be available in all environments
        pass
    
    # Run the bot
    bot.run(config.DISCORD_TOKEN)


if __name__ == "__main__":
    main()
