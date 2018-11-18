FROM ubuntu:latest
MAINTAINER viktorxu
LABEL Description="Xonotic server!"

# create deploy dir
COPY ./*.sh /root/.deploy/
# copy app
COPY xonotic/ /opt/xonotic/

RUN /root/.deploy/deploy.sh
WORKDIR /opt/xonotic
    
# this will run on every container boot
ENTRYPOINT /root/.deploy/startup.sh

# other settings
EXPOSE 26000
