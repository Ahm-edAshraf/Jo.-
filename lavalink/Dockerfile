# Use Debian-based Java (has all required native libraries)
FROM eclipse-temurin:17-jre

WORKDIR /opt/Lavalink

# Download latest Lavalink (4.1.2) which doesn't have hardcoded plugin versions
RUN apt-get update && apt-get install -y wget && \
    wget -O Lavalink.jar https://github.com/lavalink-devs/Lavalink/releases/download/4.1.2/Lavalink.jar && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create plugins directory and download youtube-plugin 1.17.0
RUN mkdir -p plugins && \
    wget -O plugins/youtube-plugin-1.17.0.jar \
    https://github.com/lavalink-devs/youtube-source/releases/download/1.17.0/youtube-plugin-1.17.0.jar

# Copy our config
COPY application.yml .

EXPOSE 2333

CMD ["java", "-Xmx768m", "-Xms256m", "-jar", "Lavalink.jar"]
