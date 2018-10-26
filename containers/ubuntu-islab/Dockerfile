FROM ubuntu:latest
MAINTAINER viktorxu
LABEL Description="ISLAB ubuntu image base with domestic APT source, etc"

# create deploy dir
COPY ./ /root/.deploy/
WORKDIR /root/.deploy/

# due to network issues, we must download all data before other operations.
# if other operations fail, we can resume from a downloaded cache layer.
RUN cp sources.list.1804 /etc/apt/sources.list && \
    ./repeat.sh apt-get update && \
    ./repeat.sh apt-get -y install vim git python-pip traceroute openssh-server tree pv net-tools

RUN ./deploy.sh
    
# this will run on every container boot
ENTRYPOINT /root/.deploy/startup.sh

# other settings
EXPOSE 22
ONBUILD RUN apt-get update
