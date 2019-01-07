#!/bin/bash -x
docker run --rm -v `pwd`/ftproot:/home/vsftpd \
           -p 20:20 -p 21:21 -p 21100-21110:21100-21110 \
           -e FTP_USER=ftp -e FTP_PASS=ftp --name vsftpd \
           fauria/vsftpd
