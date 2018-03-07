from __future__ import print_function

import grpc

from protos import hello_pb2
from protos import hello_pb2_grpc


def run():
    channel = grpc.insecure_channel('localhost:9094')
    stub = hello_pb2_grpc.GreeterStub(channel)
    response = stub.SayHello(hello_pb2.HelloRequest(name='you'))
    print("Greeter client received: " + response.message)


if __name__ == '__main__':
    run()