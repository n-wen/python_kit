import grpc
from concurrent import futures
import multiprocessing
import time
import os
from importlib import import_module
import sys

_25_HOURS_IN_SECONDS = 60 * 60 * 25

PYTHON3 = True if sys.version_info[0] == 3 else False

if PYTHON3:
    # https://gist.github.com/seglberg/0b4487b57b4fd425c56ad72aba9971be#file-grpc_asyncio-py-L72
    import asyncio
    import functools
    import inspect
    import threading
    from grpc import _server


    def _loop_mgr(loop: asyncio.AbstractEventLoop):

        asyncio.set_event_loop(loop)
        loop.run_forever()

        # If we reach here, the loop was stopped.
        # We should gather any remaining tasks and finish them.
        pending = asyncio.Task.all_tasks(loop=loop)
        if pending:
            loop.run_until_complete(asyncio.gather(*pending))


    class AsyncioExecutor(futures.Executor):

        def __init__(self, *, loop=None):

            super().__init__()
            self._shutdown = False
            self._loop = loop or asyncio.get_event_loop()
            self._thread = threading.Thread(target=_loop_mgr, args=(self._loop,),
                                            daemon=True)
            self._thread.start()

        def submit(self, fn, *args, **kwargs):

            if self._shutdown:
                raise RuntimeError('Cannot schedule new futures after shutdown')

            if not self._loop.is_running():
                raise RuntimeError("Loop must be started before any function can "
                                   "be submitted")

            if inspect.iscoroutinefunction(fn):
                coro = fn(*args, **kwargs)
                return asyncio.run_coroutine_threadsafe(coro, self._loop)

            else:
                func = functools.partial(fn, *args, **kwargs)
                return self._loop.run_in_executor(None, func)

        def shutdown(self, wait=True):
            self._loop.stop()
            self._shutdown = True
            if wait:
                self._thread.join()


    async def _call_behavior(rpc_event, state, behavior, argument, request_deserializer):
        context = _server._Context(rpc_event, state, request_deserializer)
        try:
            behavior_result = behavior(argument, context)
            if inspect.iscoroutine(behavior_result):
                return await behavior_result, True
            else:
                return behavior_result, True
        except Exception as e:  # pylint: disable=broad-except
            with state.condition:
                if e not in state.rpc_errors:
                    details = 'Exception calling application: {}'.format(e)
                    _server.logging.exception(details)
                    _server._abort(state, rpc_event.operation_call,
                                   _server.cygrpc.StatusCode.unknown, _server._common.encode(details))
            return None, False


    async def _take_response_from_response_iterator(rpc_event, state, response_iterator):
        try:
            if inspect.isgenerator(response_iterator):
                return response_iterator.__next__(), True
            return await response_iterator.__anext__(), True
        except StopIteration:
            return None, True
        except StopAsyncIteration:
            return None, True
        except Exception as e:  # pylint: disable=broad-except
            with state.condition:
                if e not in state.rpc_errors:
                    details = 'Exception iterating responses: {}'.format(e)
                    _server.logging.exception(details)
                    _server._abort(state, rpc_event.operation_call,
                                   _server.cygrpc.StatusCode.unknown, _server._common.encode(details))
            return None, False


    async def _unary_response_in_pool(rpc_event, state, behavior, argument_thunk,
                                      request_deserializer, response_serializer):
        argument = argument_thunk()
        if argument is not None:
            response, proceed = await _call_behavior(rpc_event, state, behavior,
                                                     argument, request_deserializer)
            if proceed:
                serialized_response = _server._serialize_response(
                    rpc_event, state, response, response_serializer)
                if serialized_response is not None:
                    _server._status(rpc_event, state, serialized_response)


    async def _stream_response_in_pool(rpc_event, state, behavior, argument_thunk,
                                       request_deserializer, response_serializer):
        argument = argument_thunk()
        if argument is not None:
            # Notice this calls the normal `_call_behavior` not the awaitable version.
            response_iterator, proceed = _server._call_behavior(
                rpc_event, state, behavior, argument, request_deserializer)
            if proceed:
                while True:
                    response, proceed = await _take_response_from_response_iterator(
                        rpc_event, state, response_iterator)
                    if proceed:
                        if response is None:
                            _server._status(rpc_event, state, None)
                            break
                        else:
                            serialized_response = _server._serialize_response(
                                rpc_event, state, response, response_serializer)
                            print(response)
                            if serialized_response is not None:
                                print("Serialized Correctly")
                                proceed = _server._send_response(rpc_event, state,
                                                                 serialized_response)
                                if not proceed:
                                    break
                            else:
                                break
                    else:
                        break


    _server._unary_response_in_pool = _unary_response_in_pool
    _server._stream_response_in_pool = _stream_response_in_pool


class Servicer(object):
    def __init__(self, name, server):
        self.name = name
        self.handlers = {}
        self.server = server

    def endpoint(self, endpoint_name):
        def decorator(f):
            if endpoint_name not in self.handlers:
                def wrapper(self, *args, **kwargs):
                    return f(*args, **kwargs)
                self.handlers[endpoint_name] = wrapper
            return
        return decorator

    def response(self, res_type_name, res_dict):
        response_class = getattr(self.server.pb2_module, res_type_name)
        return response_class(**res_dict)


class PythonKit(object):
    server = None

    def __init__(self, name, protos):
        self.name = name
        self.servicers = {}
        self.protos = os.path.abspath(protos)
        self.rel_protos = os.path.relpath(os.path.dirname(protos))
        self.protos_dir = ''
        self.server_name = protos.split('/')[-1].split('.')[0]
        self.pb2_module = None
        self.pb2_grpc_module = None

    def create_servicer(self, servicer_name):
        if servicer_name not in self.servicers:
            servicer = Servicer(servicer_name, self)
            self.servicers[servicer_name] = servicer
        return self.servicers[servicer_name]

    def add_servicer(self, servicer):
        servicer.server = self
        self.servicers[servicer.name] = servicer

    def build_pb(self):

        """
        use tools to compile protobuff
        """
        from grpc_tools import protoc
        from os.path import dirname
        import sys
        protos_dirname = dirname(self.protos)
        # python3 do not support implicitly relative import,
        # and python script auto generated by grpc tools using implicitly relative import.
        # so it must add protos dir to python path.
        sys.path.append(protos_dirname)
        self.protos_dir = protos_dirname
        protoc.main([__name__, "-I{}".format(protos_dirname),
                     "--python_out={}".format(protos_dirname),
                     "--grpc_python_out={}".format(protos_dirname),
                     self.protos])

    def run(self, address, is_test=False):
        self.build_pb()
        if PYTHON3:
            self.server = grpc.server(AsyncioExecutor())
        else:
            self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=(multiprocessing.cpu_count() * 2 + 1)))

        pb2_module_name = self.server_name + '_pb2'
        pb2_grpc_module_name = self.server_name + '_pb2_grpc'
        if self.rel_protos == '.':
            self.pb2_grpc_module = import_module('{}'.format(pb2_grpc_module_name))
            self.pb2_module = import_module('{}'.format(pb2_module_name))
        else:
            self.pb2_grpc_module = import_module('.{}'.format(pb2_grpc_module_name), self.rel_protos)
            self.pb2_module = import_module('.{}'.format(pb2_module_name), self.rel_protos)
        for servicer in self.servicers.values():
            # get grpc servicer class
            # create a class extend grpc servicer class
            servicer_class = getattr(self.pb2_grpc_module, '{}Servicer'.format(servicer.name))
            # add handler to this class
            servicer_class = type("test", (servicer_class,), servicer.handlers)

            add_method = getattr(self.pb2_grpc_module, 'add_{}Servicer_to_server'.format(servicer.name))
            add_method(servicer_class(), self.server)
        self.server.add_insecure_port(address)
        self.server.start()
        try:
            while True and not is_test:
                time.sleep(_25_HOURS_IN_SECONDS)
        except KeyboardInterrupt:
            self.server.stop(0)
