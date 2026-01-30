# Use Debian-based Java (has all required native libraries)
FROM eclipse-temurin:17-jre

WORKDIR /opt/Lavalink

# Download Lavalink 4.1.2
RUN apt-get update && apt-get install -y wget && \
    wget -O Lavalink.jar https://github.com/lavalink-devs/Lavalink/releases/download/4.1.2/Lavalink.jar && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# TRICK: Download 1.17.0 but name it as 1.16.0 so Lavalink thinks it's the version it wants
RUN mkdir -p plugins && \
    wget -O plugins/youtube-plugin-1.16.0.jar \
    https://github.com/lavalink-devs/youtube-source/releases/download/1.17.0/youtube-plugin-1.17.0.jar

# Copy our config (without plugin section so Lavalink doesn't try to download)
COPY application.yml .

EXPOSE 2333

CMD ["java", "-Xmx768m", "-Xms256m", "-jar", "Lavalink.jar"]
