# Use stable Lavalink v4
FROM ghcr.io/lavalink-devs/lavalink:4

# Ensure clean state and permissions
USER root
RUN mkdir -p /opt/Lavalink/plugins && chown -R lavalink:lavalink /opt/Lavalink/plugins
USER lavalink

WORKDIR /opt/Lavalink

COPY --chown=lavalink:lavalink application.yml /opt/Lavalink/application.yml
