import grpc
from concurrent import futures
import multiprocessing
import time
import os

_25_HOURS_IN_SECONDS = 60 * 60 * 25


class Servicer(object):
    def __init__(self, name, server):
        self.name = name
        self.handlers = {}
        self.server = server

    def endpoint(self, endpoint_name):
        def decorator(f):
            if endpoint_name not in self.handlers:
                self.handlers[endpoint_name] = f
            return f
        return decorator

    def response(self, res_type_name, res_dict):
        response_class = getattr(getattr(self.server.pb_module, '{}_pb2'.format(self.server.server_name)), res_type_name)
        return response_class(**res_dict)



class PythonKit(object):
    def __init__(self, name, protos):
        self.name = name
        self.servicers = {}
        self.protos = os.path.abspath(protos)
        self.protos_dir = ''
        self.server_name = protos.split('/')[-1].split('.')[0]
        self.pb_module = None

    def create_servicer(self, servicer_name):
        if servicer_name not in self.servicers:
            servicer = Servicer(servicer_name, self)
            self.servicers[servicer_name] = servicer
        return self.servicers[servicer_name]

    def build_pb(self):

        """
        use tools to compile protobuff
        """
        from grpc_tools import protoc
        from os.path import dirname
        protos_dirname = dirname(self.protos)
        self.protos_dir = protos_dirname
        protoc.main([__name__, "-I{}".format(protos_dirname),
                     "--python_out={}".format(protos_dirname),
                     "--grpc_python_out={}".format(protos_dirname),
                     self.protos])

    def run(self, address):
        self.build_pb()

        server = grpc.server(futures.ThreadPoolExecutor(max_workers=(multiprocessing.cpu_count() * 2 + 1)))
        pb2_module_name = 'protos' + '.' + self.server_name + '_pb2'
        pb2_grpc_module_name = 'protos' + '.' + self.server_name + '_pb2_grpc'
        server_module = __import__(pb2_grpc_module_name)
        self.pb_module = server_module
        for servicer in self.servicers.values():
            # get grpc servicer class
            # create a class extend grpc servicer class
            servicer_class = getattr(getattr(server_module, '{}_pb2_grpc'.format(self.server_name)), '{}Servicer'.format(servicer.name))
            # add handler to this class
            servicer_class = type("test", (servicer_class,), servicer.handlers)

            add_method = getattr(getattr(server_module, '{}_pb2_grpc'.format(self.server_name)), 'add_{}Servicer_to_server'.format(servicer.name))
            add_method(servicer_class(), server)
        server.add_insecure_port(address)
        server.start()
        try:
            while True:
                time.sleep(_25_HOURS_IN_SECONDS)
        except KeyboardInterrupt:
            server.stop(0)
