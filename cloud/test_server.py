#!/usr/bin/python
import pyjsonrpc
import socket

if __name__ == "__main__":
    cli = pyjsonrpc.HttpClient(
        url = "http://viktorlab.cn:9000/jsonrpc")
    print cli.run("counter")
    
    
