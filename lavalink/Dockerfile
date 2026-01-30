FROM ghcr.io/lavalink-devs/lavalink:4-alpine

# Cache bust: 2026-01-31-v2 - Force rebuild to get youtube-plugin 1.17.0
RUN rm -rf /opt/Lavalink/plugins/* 2>/dev/null || true

COPY application.yml /opt/Lavalink/application.yml
