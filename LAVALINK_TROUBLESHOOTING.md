# Lavalink Music Bot Troubleshooting Guide

## Current Status (January 31, 2026)

### ✅ What's Working
- Bot connects to Lavalink successfully
- OAuth authentication is working (refresh token persisted via env variable)
- Search queries are processed correctly (no more double `ytsearch:` prefix)
- Search results are returned from YouTube

### ❌ Current Problem
**Playback fails with "This video is unavailable"**

The error in Lavalink logs:
```
ERROR d.l.y.c.LocalSignatureCipherManager: Problematic YouTube player script detected 
(issue detected with script: must find sig function)
Source version: 1.16.0
```

### Root Cause
**Lavalink has a bug that forces youtube-plugin version 1.16.0**, even when 1.17.0 is configured or pre-downloaded.

Every time Lavalink starts:
1. It finds youtube-plugin-1.17.0.jar (which we download)
2. It DELETES it saying "new version: 1.16.0" (incorrect version comparison)
3. It downloads 1.16.0 from maven

The 1.16.0 version has broken YouTube signature parsing that 1.17.0 fixes.

---

## Configuration Files

### `lavalink/Dockerfile`
```dockerfile
FROM ghcr.io/lavalink-devs/lavalink:dev

RUN mkdir -p /opt/Lavalink/plugins && \
    wget -O /opt/Lavalink/plugins/youtube-plugin-1.17.0.jar \
    https://github.com/lavalink-devs/youtube-source/releases/download/1.17.0/youtube-plugin-1.17.0.jar

COPY application.yml /opt/Lavalink/application.yml
```

### `lavalink/application.yml`
```yaml
server:
  port: 2333
  address: 0.0.0.0

lavalink:
  server:
    password: "ahmed"
    sources:
      youtube: false  # Using youtube-plugin instead
      soundcloud: true
      bandcamp: true
      twitch: true
      vimeo: true
      http: true
      local: false

plugins:
  youtube:
    enabled: true
    allowSearch: true
    allowDirectVideoIds: true
    allowDirectPlaylistIds: true
    clients:
      # Search-capable clients
      - MUSIC        # For ytmsearch
      - WEB          # For ytsearch
      # OAuth-compatible clients for playback
      - ANDROID_MUSIC
      - IOS
    oauth:
      enabled: true
      refreshToken: ${YOUTUBE_REFRESH_TOKEN:}  # Set in Railway env vars

logging:
  level:
    root: INFO
    lavalink: INFO
```

---

## Railway Environment Variables

### Lavalink Service
| Variable | Value |
|----------|-------|
| `YOUTUBE_REFRESH_TOKEN` | The OAuth refresh token from the logs |

### Bot Service
| Variable | Value |
|----------|-------|
| `DISCORD_TOKEN` | Your bot token |
| `LAVALINK_HOST` | `lavalink-2026.railway.internal` |
| `LAVALINK_PORT` | `2333` |
| `LAVALINK_PASSWORD` | `ahmed` |
| `LAVALINK_SSL` | `false` |

---

## Bot Code Fixes Applied

### `cogs/music.py` - Fixed double search prefix
The play command was adding `ytsearch:` manually AND passing `search_type=SearchType.YOUTUBE`, causing double prefixing.

**Fixed code:**
```python
if is_url:
    result = await vc.fetch_tracks(query)
else:
    # Let mafic add the ytsearch: prefix via search_type
    result = await vc.fetch_tracks(query, search_type=SearchType.YOUTUBE)
```

---

## Attempted Solutions (All Failed to Fix Plugin Version)

1. **Specify version 1.17.0 in config** - Lavalink ignores it
2. **Add repository URL** - Still downloads 1.16.0
3. **Pre-download 1.17.0 JAR** - Lavalink deletes it
4. **Rename 1.17.0 to 1.16.0** - Lavalink reads version from JAR manifest
5. **Use Lavalink dev image** - Same bug, built December 2025
6. **Build from plain Java image** - Same Lavalink plugin manager behavior
7. **Remove plugins config section** - Lavalink still forces 1.16.0

---

## Potential Solutions to Try

1. **Wait for new Lavalink release** - A version built after youtube-plugin 1.17.0 release should have it

2. **Build Lavalink from source** - Modify the embedded plugin version

3. **Use a poToken** instead of OAuth - May bypass signature issues

4. **Try alternative audio sources** - SoundCloud, Spotify plugin, etc.

5. **Use a public Lavalink node** - Find one that's been updated

---

## OAuth Setup (For Reference)

If you need to re-authenticate OAuth:

1. Remove `YOUTUBE_REFRESH_TOKEN` from Railway env vars
2. Redeploy Lavalink
3. Check logs for: `go to https://www.google.com/device and enter code XXXX-XXXX`
4. Go to that URL, sign in with a **burner Google account**
5. Enter the code
6. Check logs for: `Token retrieved successfully. Store your refresh token as this can be reused. (TOKEN_HERE)`
7. Add `YOUTUBE_REFRESH_TOKEN` = that token to Railway env vars
8. Redeploy

---

## Dependencies

- **Lavalink**: `ghcr.io/lavalink-devs/lavalink:dev` (commit a003505)
- **youtube-plugin**: Trying to use 1.17.0, but forced to 1.16.0
- **mafic**: `>=2.10.0`
- **discord.py**: Latest

---

## Files Changed in This Session

1. `cogs/music.py` - Fixed double ytsearch prefix
2. `lavalink/Dockerfile` - Multiple iterations trying to force 1.17.0
3. `lavalink/application.yml` - OAuth config, clients, refresh token env var
4. `requirements.txt` - Updated mafic version

