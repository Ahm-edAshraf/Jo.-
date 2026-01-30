# Use Lavalink dev image - might not have hardcoded plugin versions
FROM ghcr.io/lavalink-devs/lavalink:dev

# Pre-download the 1.17.0 plugin
RUN mkdir -p /opt/Lavalink/plugins && \
    wget -O /opt/Lavalink/plugins/youtube-plugin-1.17.0.jar \
    https://github.com/lavalink-devs/youtube-source/releases/download/1.17.0/youtube-plugin-1.17.0.jar

COPY application.yml /opt/Lavalink/application.yml
