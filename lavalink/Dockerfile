# Build from plain Java image to avoid base image's default configs
FROM eclipse-temurin:17-jre-alpine

WORKDIR /opt/Lavalink

# Download Lavalink JAR
RUN wget -O Lavalink.jar https://github.com/lavalink-devs/Lavalink/releases/download/4.0.8/Lavalink.jar

# Create plugins directory and download youtube-plugin 1.17.0 directly
RUN mkdir -p plugins && \
    wget -O plugins/youtube-plugin-1.17.0.jar \
    https://github.com/lavalink-devs/youtube-source/releases/download/1.17.0/youtube-plugin-1.17.0.jar

# Copy our config
COPY application.yml .

EXPOSE 2333

CMD ["java", "-Xmx768m", "-Xms256m", "-jar", "Lavalink.jar"]
