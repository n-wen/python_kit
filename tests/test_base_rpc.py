import pytest
from python_kit import PythonKit
import sys

sys.path.append('./tests')
import grpc



@pytest.fixture(scope='session', autouse=True)
def server():
    return PythonKit(__name__, protos='./tests/hello.proto')


@pytest.fixture(scope='module')
def servicer(server):
    return server.create_servicer('Greeter')


@pytest.fixture(scope="module", autouse=True)
def register_unary_endpoint(servicer):
    @servicer.endpoint('SayHello')
    def SayHello(request, context):
        hello_to = request.name
        return servicer.response('HelloReply', {
            'message': hello_to
        })

    return servicer


@pytest.fixture(scope="module", autouse=True)
def register_server_streaming_endpoint(servicer):
    @servicer.endpoint('ListNames')
    def ListNames(request, context):
        for name in request.name.split(','):
            yield servicer.response('HelloReply', {
                'message': name
            })


@pytest.fixture(scope="module", autouse=True)
def register_client_streaming_endpoint(servicer):
    @servicer.endpoint('HelloMany')
    def HelloMany(request, context):
        names = ""
        for single_request in request:
            names += single_request.name
        return servicer.response('HelloReply', {
            'message': 'Hello: {}'.format(names)
        })


@pytest.fixture(scope="module", autouse=True)
def register_bidirectional_streaming_endpoint(servicer):
    @servicer.endpoint('HelloChat')
    def HelloChat(request, context):
        for single_reqeust in request:
            yield servicer.response('HelloReply', {
                'message': '{}'.format(single_reqeust.name)
            })


@pytest.fixture(scope='module', autouse=True)
def start_server(server):
    """
    start server before testing start, and stop it after finishing testing.
    :return:
    """
    server.run('[::]:9094', is_test=True)
    yield
    server.server.stop(0)


@pytest.fixture(scope='module')
def client_stub():
    import hello_pb2_grpc
    channel = grpc.insecure_channel('localhost:9094')
    stub = hello_pb2_grpc.GreeterStub(channel)
    return stub


def test_unary_rpc(client_stub):
    import hello_pb2
    # simple
    response = client_stub.SayHello(hello_pb2.HelloRequest(name='you'))
    assert response.message == 'you'


def test_server_streaming_rpc(client_stub):
    import hello_pb2
    names = ['Peter', 'Harry', 'Mike']
    response_list = client_stub.ListNames(hello_pb2.HelloRequest(name=','.join(names)))
    for response in response_list:
        assert response.message in names
        names.remove(response.message)


def test_client_streaming_rpc(client_stub):
    import hello_pb2
    def names():
        for name in ['Joe', 'Ben', 'Cooper']:
            yield hello_pb2.HelloRequest(name=name)

    response = client_stub.HelloMany(names())
    assert response.message == 'Hello: JoeBenCooper'


def test_bidirectional_streaming_rpc(client_stub):
    import hello_pb2
    name_list = ['Joe', 'Ben', 'Cooper']

    def names():
        for name in ['Joe', 'Ben', 'Cooper']:
            yield hello_pb2.HelloRequest(name=name)

    response_list = client_stub.HelloChat(names())
    for response in response_list:
        assert response.message in name_list
        name_list.remove(response.message)
