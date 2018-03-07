# PythonKit
Write grpc application like Flask.

## Installing

```bash
pip install git+https://github.com/htwenning/python_kit
```

## Note

This project is based on Python2.

## Example

```python
from python_kit import PythonKit


server = PythonKit(__name__, protos='./protos/hello.proto')
servicer = server.create_servicer('Greeter')

@servicer.endpoint('SayHello')
def SayHello(self, request, context):
    hello_to = request.name
    return servicer.response('HelloReply', {
        'message': hello_to
    })


if __name__ == "__main__":
    server.run('[::]:9094')
```

For details please read [example dir](https://github.com/htwenning/python_kit/tree/master/example) in project
