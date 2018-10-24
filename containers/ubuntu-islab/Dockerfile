FROM ubuntu:latest
MAINTAINER viktorxu
LABEL Description="ISLAB ubuntu image base with domestic APT source, etc"

# due to network issues, we must download all data before other operations.
# if other operations fail, we can resume from a downloaded cache layer.
COPY sources.list.1804 /etc/apt/sources.list
RUN apt-get update && apt-get -y install vim git python-pip traceroute openssh-server tree pv

# copy necessary files to /root/.deploy
COPY ./ /root/.deploy/
RUN /root/.deploy/deploy.sh

# this will run on every container boot
ENTRYPOINT /root/.deploy/startup.sh

# other settings
EXPOSE 22
ONBUILD RUN apt-get update
