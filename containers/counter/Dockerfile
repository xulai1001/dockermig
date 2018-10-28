FROM python
# create deploy dir
COPY ./ /root/
WORKDIR /root/

RUN ./deploy.sh
    
# this will run on every container boot
ENTRYPOINT ["python", "/root/counter.py"]

