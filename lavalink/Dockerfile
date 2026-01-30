# Use Debian-based Java (has all required native libraries)
FROM eclipse-temurin:17-jre

WORKDIR /opt/Lavalink

# Download Lavalink 4.1.2
RUN apt-get update && apt-get install -y wget && \
    wget -O Lavalink.jar https://github.com/lavalink-devs/Lavalink/releases/download/4.1.2/Lavalink.jar && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create empty plugins directory - let Lavalink download the plugin itself
RUN mkdir -p plugins

# Copy our config
COPY application.yml .

EXPOSE 2333

CMD ["java", "-Xmx768m", "-Xms256m", "-jar", "Lavalink.jar"]
