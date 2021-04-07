FROM golang:1.12-alpine
RUN  adduser -D -S app -u 1001
USER app
WORKDIR /app
ADD golang-webserver /app/
ENTRYPOINT ["./golang-webserver"]