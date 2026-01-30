FROM ghcr.io/lavalink-devs/lavalink:4-alpine

# Clear any cached plugins to force fresh download
RUN rm -rf /opt/Lavalink/plugins/*

COPY application.yml /opt/Lavalink/application.yml
