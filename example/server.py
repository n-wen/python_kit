from python_kit import PythonKit
import sys

server = PythonKit(__name__, protos='./protos/hello.proto')
servicer = server.create_servicer('Greeter')

if sys.version_info[0] == 3:
    import asyncio

    @servicer.endpoint('SayHello')
    async def SayHello(request, context):
        hello_to = request.name
        print("time to sleep")
        await asyncio.sleep(5)
        print("wake up to reply")
        return servicer.response('HelloReply', {
            'message': hello_to
        })
    @servicer.endpoint('ListNames')
    async def ListNames(request, context):
        for name in request.name.split(','):
            yield servicer.response('HelloReply', {
                'message': name
            })


    @servicer.endpoint('HelloMany')
    async def HelloMany(request, context):
        names = ""
        for single_request in request:
            names += single_request.name
        return servicer.response('HelloReply', {
            'message': 'Hello: {}'.format(names)
        })


    @servicer.endpoint('HelloChat')
    async def HelloChat(request, context):
        for single_reqeust in request:
            yield servicer.response('HelloReply', {
                'message': 'Hello: {}'.format(single_reqeust.name)
            })

else:
    @servicer.endpoint('SayHello')
    def SayHello(request, context):
        hello_to = request.name
        return servicer.response('HelloReply', {
            'message': hello_to
        })

    @servicer.endpoint('ListNames')
    def ListNames(request, context):
        for name in request.name.split(','):
            yield servicer.response('HelloReply', {
                'message': name
            })


    @servicer.endpoint('HelloMany')
    def HelloMany(request, context):
        names = ""
        for single_request in request:
            names += single_request.name
        return servicer.response('HelloReply', {
            'message': 'Hello: {}'.format(names)
        })


    @servicer.endpoint('HelloChat')
    def HelloChat(request, context):
        for single_reqeust in request:
            yield servicer.response('HelloReply', {
                'message': 'Hello: {}'.format(single_reqeust.name)
            })


if __name__ == "__main__":
    server.run('[::]:9094')
