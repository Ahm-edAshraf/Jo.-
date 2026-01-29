# Discord Music Bot

A Python Discord music bot using **discord.py**, **Mafic**, and **Lavalink** for fast YouTube playback. Supports queue, pause/resume, volume, seek, loop, shuffle, and optional audio filters (bassboost, nightcore). Designed to run on **Railway** (bot + Lavalink as separate services).

## Features

- **Play** – YouTube URL or search query
- **Queue** – Add, view, remove, clear, shuffle
- **Playback** – Pause, resume, stop, skip, seek
- **Volume** – 0–100%
- **Loop** – Off, track, or queue
- **Filters** – Bassboost, nightcore, reset (Lavalink)
- **Leave** – Disconnect from voice

## Requirements

- Python 3.10+
- A running **Lavalink** server (Java 17+)
- Discord bot token

**Note:** Mafic works with only one Discord library. If you have both `discord.py` and `py-cord` installed, uninstall one (e.g. `pip uninstall py-cord`) so only `discord.py` is used.

## Local setup

1. **Clone and install**

   ```bash
   cd botmusic
   pip install -r requirements.txt
   ```

2. **Lavalink**

   - Install Java 17+
   - Download [Lavalink JAR](https://github.com/lavalink-devs/lavalink/releases) and create `application.yml` with port and password
   - Run: `java -jar Lavalink.jar`

3. **Environment**

   - Copy `.env.example` to `.env`
   - Set `DISCORD_TOKEN`, `LAVALINK_HOST` (e.g. `127.0.0.1`), `LAVALINK_PORT` (e.g. `2333`), `LAVALINK_PASSWORD`

4. **Run the bot**

   ```bash
   python bot.py
   ```

## Railway deployment

1. **New project** – Create a project with two services:
   - **Service 1:** Python app (this repo). Start command: `python bot.py`. Add env vars: `DISCORD_TOKEN`, `LAVALINK_HOST`, `LAVALINK_PORT`, `LAVALINK_PASSWORD`.
   - **Service 2:** Lavalink (use Railway’s Lavalink template). Set `LAVALINK_SERVER_PASSWORD`. Use the service’s **internal** hostname (e.g. `lavalink.railway.internal`) and port as `LAVALINK_HOST` and `LAVALINK_PORT` for the bot.

2. **Bot env vars**

   - `DISCORD_TOKEN` – From [Discord Developer Portal](https://discord.com/developers/applications) → Your App → Bot → Reset Token
   - `LAVALINK_HOST` – Lavalink service internal host (e.g. `lavalink.railway.internal`)
   - `LAVALINK_PORT` – Lavalink port (often `2333`)
   - `LAVALINK_PASSWORD` – Same as Lavalink’s `LAVALINK_SERVER_PASSWORD`
   - `LAVALINK_SSL` – Set to `true` if Lavalink uses WSS/HTTPS

3. **Deploy** – Push to the connected repo; Railway builds and runs the bot. Ensure Lavalink service is running so the bot can connect.

## Commands (slash)

| Command | Description |
|--------|-------------|
| `/music play <query>` | Play URL or search |
| `/music pause` | Pause |
| `/music resume` | Resume |
| `/music stop` | Stop and clear queue |
| `/music skip [count]` | Skip 1 or N tracks |
| `/music seek <position>` | Seek (e.g. 1:30 or 90) |
| `/music queue` | Show queue |
| `/music nowplaying` | Current track + progress |
| `/music remove <index>` | Remove queue item |
| `/music clear` | Clear queue |
| `/music shuffle` | Shuffle queue |
| `/music volume [0-100]` | Get/set volume |
| `/music loop off/track/queue` | Loop mode |
| `/music leave` | Disconnect |
| `/filter bassboost` | Bass boost |
| `/filter nightcore` | Nightcore |
| `/filter reset` | Reset filters |

## License

MIT
