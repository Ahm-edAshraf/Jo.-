# Use stable Lavalink v4
FROM ghcr.io/lavalink-devs/lavalink:4

# Ensure clean state to avoid pre-bundled plugins interfering
RUN rm -rf /opt/Lavalink/plugins && mkdir -p /opt/Lavalink/plugins

COPY application.yml /opt/Lavalink/application.yml
