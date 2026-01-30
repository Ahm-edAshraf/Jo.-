"""Load configuration from environment variables."""
import os
from pathlib import Path

# Load .env if present (e.g. local dev)
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass

# Discord
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
# Optional: sync commands to this guild only (instant; leave empty for global sync, which can take up to 1 hour)
GUILD_ID = os.getenv("GUILD_ID", "")

# Lavalink
LAVALINK_HOST = os.getenv("LAVALINK_HOST", "127.0.0.1")
LAVALINK_PORT = int(os.getenv("LAVALINK_PORT", "2333"))
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD", "youshallnotpass")
LAVALINK_SSL = os.getenv("LAVALINK_SSL", "false").lower() in ("true", "1", "yes")
# Bot 0-100% maps to Lavalink 0-200 (was 0-1000). Max volume = loud but not ear-blowing.
LAVALINK_VOLUME_MAX = 200

# Optional: use yt-dlp + FFmpeg instead of Lavalink (single-service mode)
USE_YTDLP_FALLBACK = os.getenv("USE_YTDLP_FALLBACK", "false").lower() in ("true", "1", "yes")
