FROM ghcr.io/lavalink-devs/lavalink:4-alpine

# Remove old plugins and download latest youtube-plugin directly
RUN rm -rf /opt/Lavalink/plugins/* 2>/dev/null || true && \
    mkdir -p /opt/Lavalink/plugins && \
    wget -O /opt/Lavalink/plugins/youtube-plugin-1.17.0.jar \
    https://github.com/lavalink-devs/youtube-source/releases/download/1.17.0/youtube-plugin-1.17.0.jar

COPY application.yml /opt/Lavalink/application.yml
