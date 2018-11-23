#!/usr/bin/python
import pyjsonrpc
import socket

hostname = socket.gethostname()
ip = socket.gethostbyname(hostname)

if __name__ == "__main__":
    cli = pyjsonrpc.HttpClient(
        url = "http://localhost:9000/jsonrpc")
    print cli.prepare(ip, "counter")
    
    
