# Cloud Engineer A/B Test Infrastructure

The goal of this particular case study was to build an infrastructure for A/B testing. Here I got two binaries, one Go based application, one Java-based application. The infrastructure should be built in a way that it will distribute 70% traffic to the Go app and 30% traffic to Java app.

This README.md file will explain the architecture of the infrastructure and the implementation. Also this documentation will explain in a way that this setup can be reproduced.

## Architecture

As explained before in this task there are two application, one is a Java application and the other one is a Go application. Both are web application providing similar endpoints:

| Route  | Description                                |
|--------|--------------------------------------------|
|/       | A static site                              |
|/hotels |JSON object containing hotel search results |
|/health |Exposes the health status of the application|
|/ready   |Readiness probe                            |
|/metrics|Exposes metrics of the application          |

Both application was running on `8080` port. According to this task there should be a load balancer which will split the traffic in a way that 30% request will go to Java app and rest of the traffic will go to Go app.

Also this whole setup has to be containerized according to the instruction. So idea was to containerize both application and expose on a particular port. And use a load balancer which will split the traffic between both containers. Here in this setup `nginx` has been used as load balancer.

> Please note, in this setup nginx is also a containerized application.

Also a DNS entry named `application.net` will be setup to access the application. So in summary, when users send a http requests to `http://application.net/`, these requests will go to nginx, and nginx will forward 70% requests to the Go app container, and the rest of the requests will be forwarded to Java app container.

## Environment

This complete setup has been done on a Ubuntu machine. Also docker and docker-compose was there.

* Operating system: Ubuntu 18.04.3 LTS
* Docker-CE: version 18.09.1
* docker-compose: version 1.21.0
* python3: version 3.6.8

## Implementation

The first step of this setup is to build the docker container for both Java application and the Go application.

The whole code has been placed under `trivago_cloud` folder. The complete folder structure will look like below

```
tanzeem@tanzeem-HP-EliteBook-820-G3 ~/Desktop/trivago_cloud (develop) $ tree
├── Go_app
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── golang-webserver
├── Java_app
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── java-webserver.jar
├── nginx
│   ├── default.conf
│   ├── defaultconfdockeripgenerator.sh
│   ├── defaultconfgenerator.sh
│   ├── default-conf-template.conf
│   ├── default-conf-template-dockerip.conf
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── getipaddress.sh
│   └── ip_address.txt
├── README.md
└── testing
    ├── logs.txt
    └── test.py

```
### Java application dockerization

All the necessary files to build the docker container using java app has been placed under `Java_app` folder.
Change the directory to execute the following stages.
```
cd Java_app
```
There are three files under Java_app folder.

```
├── docker-compose.yml
├── Dockerfile
└── java-webserver.jar

```
The `java-webserver.jar` is the binary which I got once I downloaded the resources for this challenge. The `Dockerfile` is used to build the container and `docker-compose.yml` is to run the container.


The `Dockerfile` will look like below

```
FROM openjdk:11-jre-slim
RUN apt-get update && apt-get install --assume-yes curl
RUN useradd -r -u 1000 -s /bin/bash app
USER app
ADD java-webserver.jar app.jar
ENTRYPOINT exec java $JAVA_OPTS -jar /app.jar

```
> As this application is Java 11 so openjdk:11-jre-slim has been used as base image.

To build the image

```
docker build -t javaapp .

```
After building the image it is visible in local
```
REPOSITORY                   TAG                 IMAGE ID            CREATED             SIZE
javaapp                      latest              730bd89b8f6b        8 seconds ago       245MB

```
The docker-compose.yml will like below

```
version: "3.3"

services:
  hotelsearchjava:
    image: javaapp:latest
    ports:
      - "8081:8080"

```
Here the application will be exposed on port `8081`. To deploy the container run `docker-compose up -d`

To check the application status we can do `curl http://localhost:8081/health` and the response is `{"status":"UP"}`

### Go application dockerization

All the necessary files to build the docker container using go app has been placed under `Go_app` folder.
Change the directory to execute the following stages.
```
cd Go_app
```
Very similar to the Java app here we also have three files

```
.
├── docker-compose.yml
├── Dockerfile
└── golang-webserver

```
Similar to the Java app, here I also got the binary of go application. And `Dockerfile` is to build the image and `docker-compose.yml` is for deployment.

The `Dockerfile` looks like below

```
FROM golang:1.12-alpine
RUN  adduser -D -S app -u 1001
USER app
WORKDIR /app
ADD golang-webserver /app/
ENTRYPOINT ["./golang-webserver"]
```
> Golang 1.12 version has been used as base image because the application has been developed in same version

To build the image

```
docker build -t goapp .

```
It generate a image named `goapp:latest`. The docker-compose.yml will like below

```
version: "3.3"

services:
  hotelsearchgo:
    image: goapp:latest
    ports:
      - "8082:8080"

```
Here the application will be exposed on port `8082`. To deploy the container run `docker-compose up -d`

To check the application status we can do `curl http://localhost:8082/health` and the response is `OK`.

### Setting up DNS entry

To access the `application.net` we need to add the following DNS entry in `/etc/hosts` file like below  

```
127.0.0.1       application.net

```
### Setting up nginx container as load balancer

Here it is required to set the nginx in a way that it can forward 70% traffic to go container and 30% to java container as explained before.

The whole setup for nginx in `nginx` folder which contains following files

```
.
├── defaultconfdockeripgenerator.sh
├── defaultconfgenerator.sh
├── default-conf-template.conf
├── default-conf-template-dockerip.conf
├── docker-compose.yml
├── Dockerfile
├── getipaddress.sh

```
To execute all the below steps please go inside `nginx` folder.

#### Generate default.conf

`getipaddress.sh` file will get the IP address of the active interface of the host and write it in `ip_address.txt` file. The code of `getipaddress.sh` looks like below

```
#!/bin/bash

set -e

declare -a interface_name=($(find /sys/class/net -type l -not -lname '*virtual*' -printf '%f\n'))

for i in "${interface_name[@]}"
do
  ifconfig $i | grep inet | awk 'NR==1 {print $2}' > ip_address.txt

```
This IP address is required in the configuration file of nginx. `bash getipaddress.sh` has been used to run the bash file.

It is required to run `getipaddress.sh` at the first time when nginx is setting up. Also when nginx is shifted to another network at that time its needed to run to get the new IP address.

`defaultconfgenerator.sh` is used to generate the configuration file for nginx from `default-conf-template.conf`. The configuration file name is `default.conf`. The code of `default-conf-template.conf` is

```
log_format upstreamlog '$server_name to: $upstream_addr [$request] '
  'upstream_response_time $upstream_response_time '
  'msec $msec request_time $request_time';

upstream app{
  server {{ localIP }}:8082 weight=7;
  server {{ localIP }}:8081 weight=3;
}

server{

      listen 80;
      server_name application.net;

      access_log /var/log/nginx/access.log upstreamlog;

      location / {
        proxy_pass "http://app/";
        proxy_http_version 1.1;
        proxy_set_header X-Forwarded_Host $server_name;
      }

}
```
And the code for `defaultconfgenerator.sh` is

```
#!/bin/bash

localIP=`cat ip_address.txt`
echo $localIP
sed -e "s/{{ localIP }}/${localIP}/g" \
    < default-conf-template.conf \
    > default.conf

```
Here in `defaultconfgenerator.sh` it is reading the IP address from `ip_address.txt` and replace the `{{ localIP }}` with the IP address.
To generate the `default.conf` it is required to run `bash defaultconfgenerator.sh`.  In my setup the `default.conf` looks like below

```
log_format upstreamlog '$server_name to: $upstream_addr [$request] '
  'upstream_response_time $upstream_response_time '
  'msec $msec request_time $request_time';

upstream app{
  server 192.168.178.25:8082 weight=7;
  server 192.168.178.25:8081 weight=3;
}

server{

      listen 80;
      server_name application.net;

      access_log /var/log/nginx/access.log upstreamlog;

      location / {
        proxy_pass "http://app/";
#        proxy_http_version 1.1;
        proxy_set_header X-Forwarded_Host $server_name;
      }

}

```
Here in the `server` part the `application.net` is used as server name as this name is used to resolve the request. And the location for resolving this is `http://app/`. `app` is the upstream here where the containers has been mentioned. `192.168.178.25:8082` is used to access the go app where as `192.168.178.25:8081` to access java app. `weight` has been used for load balancing. From the configuration it is seen that go app is configured to have 70% traffic where as java is configured for 30% traffic.

The formatting of the `access.log` has been changed so that it can be realize which server is resolving the request. In nginx container this log can be retrieve from docker logs. A sample log is in below

```
2019-08-24T06:53:11.249341175Z application.net to: 192.168.178.25:8081 [HEAD /health HTTP/1.1] upstream_response_time 0.004 msec 1566629591.249 request_time 0.003
2019-08-24T06:53:11.271393682Z application.net to: 192.168.178.25:8082 [HEAD /health HTTP/1.1] upstream_response_time 0.004 msec 1566629591.270 request_time 0.007
2019-08-24T06:53:11.323002916Z application.net to: 192.168.178.25:8082 [HEAD /health HTTP/1.1] upstream_response_time 0.000 msec 1566629591.322 request_time 0.002
2019-08-24T06:53:11.362283993Z application.net to: 192.168.178.25:8081 [HEAD /health HTTP/1.1] upstream_response_time 0.004 msec 1566629591.361 request_time 0.002
2019-08-24T06:53:11.380160058Z application.net to: 192.168.178.25:8082 [HEAD /health HTTP/1.1] upstream_response_time 0.000 msec 1566629591.380 request_time 0.001

```   

It is also possible to use the docker default gateway which is `docker0` IP to use as the IP address in nginx configuration. In this case please run `bash defaultconfdockeripgenerator.sh` which will generate the `default.conf` from `default-conf-template-dockerip.conf` using `docker0` IP.

> docker0 IP might not work in system like macOS or windows where docker desktop normally been used. This is documented in [docker networking for macOS](https://docs.docker.com/docker-for-mac/networking/).

#### Build nginx container

Its required to build a nginx container locally to use the generated `default.conf`. The `Dockerfile` looks like below  

```
FROM nginx:1.17
COPY default.conf /etc/nginx/conf.d/default.conf
```
to build the image `docker build -t nginxlocal .` need to run. Which will generate `nginxlocal:latest` image.

The code for `docker-compose.yml` is

```
version: "3.3"
services:
  nginx:
    image: nginxlocal:latest
    ports:
      - "80:80"

```
Finally `docker-compose up -d` has been run to bring up the nginx. At this point java app container, go app container and nginx all are up. To check `docker ps` can run.

```
CONTAINER ID        IMAGE                         COMMAND                  CREATED             STATUS              PORTS                                      NAMES
71a46b5ed3c7        nginxlocal:latest             "nginx -g 'daemon of…"   4 minutes ago       Up 4 minutes        0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp   nginx_nginx_1
91f824e55003        goapp:latest                  "./golang-webserver"     3 hours ago         Up 3 hours          0.0.0.0:8082->8080/tcp                     go_app_hotelsearchgo_1
cd3760eee413        javaapp:latest                "/bin/sh -c 'exec ja…"   3 hours ago         Up 3 hours          0.0.0.0:8081->8080/tcp                     java_app_hotelsearchjava_1

```
## Testing

For the testing a python script has been written. This python script has two definition beside the main definition. In definition `checkresponse` two argument need to pass which are `api` and `no_of_request`.

* api = The url where user want to send request
* no_of_request = The no of request user want to send

In this definition a particular no of request has send to the api and the nginx logs has written to `logs.txt`

In definition `calculatetraficdistribution` the access logs of nginx has been checked from `logs.txt` and based on that the percentage of response of both java and go application has calculated.

In this script the main method looks like below

```python
if __name__=='__main__':

    checkresponse('http://application.net/', 100)
    checkresponse('http://application.net/hotels', 100)
    checkresponse('http://application.net/ready', 100)
    checkresponse('http://application.net/metrics', 100)
    checkresponse('http://application.net/health', 100)
    calculatetraficdistribution()

```
To run the script

```python
python3 test.py

```
Here towards every api 100 request has been sent, which means in total 1500 request has been sent. And the result of this python script looks like below

```python
total no of request is 1500
total no of response from go app are 1050
total no of response from java app are 450
Result in percentage
 Response from Golang app 70.0
 Response from Java app 30.0
```
> The complete log is also available in logs.txt file

So it has been observed that by this setup 70% of traffic has been redirected towards Go app whereas 30% traffic has been redirected towards Java app.  
