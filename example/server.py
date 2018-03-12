from python_kit import PythonKit

server = PythonKit(__name__, protos='./protos/hello.proto')
servicer = server.create_servicer('Greeter')


@servicer.endpoint('SayHello')
def SayHello(self, request, context):
    hello_to = request.name
    return servicer.response('HelloReply', {
        'message': hello_to
    })


@servicer.endpoint('ListNames')
def ListNames(self, request, context):
    for name in request.name.split(','):
        yield servicer.response('HelloReply', {
            'message': name
        })


@servicer.endpoint('HelloMany')
def HelloMany(self, request, context):
    names = ""
    for single_request in request:
        names += single_request.name
    return servicer.response('HelloReply', {
        'message': 'Hello: {}'.format(names)
    })


@servicer.endpoint('HelloChat')
def HelloChat(self, request, context):
    for single_reqeust in request:
        yield servicer.response('HelloReply', {
            'message': 'Hello: {}'.format(single_reqeust.name)
        })


if __name__ == "__main__":
    server.run('[::]:9094')
