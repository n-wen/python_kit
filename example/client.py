from __future__ import print_function

import grpc

from protos import hello_pb2
from protos import hello_pb2_grpc


def run():
    channel = grpc.insecure_channel('localhost:9094')
    stub = hello_pb2_grpc.GreeterStub(channel)
    # simple
    response = stub.SayHello(hello_pb2.HelloRequest(name='you'))
    print("simple rpc: \n ==============\n")
    print("Greeter client received: " + response.message)
    # stream response
    print("response streaming rpc: \n ==============\n")
    responses = stub.ListNames(hello_pb2.HelloRequest(name='Peter,Harry,Mike'))
    for res in responses:
        print(res)
    # steam request
    print("request streaming rpc: \n ==============\n")

    def get_names():
        for i in ['name1', 'name2', 'name3', 'name4']:
            yield hello_pb2.HelloRequest(name=i)

    response = stub.HelloMany(get_names())
    print(response)

    # bidirectional
    print("bidirectional streaming rpc: \n ==============\n")
    responses = stub.HelloChat(get_names())
    for res in responses:
        print(res)


if __name__ == '__main__':
    run()
