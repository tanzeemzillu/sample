FROM openjdk:11-jre-slim
RUN apt-get update && apt-get install --assume-yes curl
RUN useradd -r -u 1000 -s /bin/bash app
USER app
ADD java-webserver.jar app.jar
ENTRYPOINT exec java $JAVA_OPTS -jar /app.jar