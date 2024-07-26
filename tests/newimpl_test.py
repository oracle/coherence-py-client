import asyncio
import queue
import sys

from time import sleep
from typing import TypeVar, AsyncIterator, Awaitable

import grpc
import json
from google.protobuf.json_format import MessageToJson, Parse
from google.protobuf.any_pb2 import Any
from google.protobuf.wrappers_pb2 import BytesValue

# Import the generated protobuf and gRPC files
import coherence.proxy_service_v1_pb2 as proxy_service_v1_pb2
import coherence.proxy_service_v1_pb2_grpc as proxy_service_v1_pb2_grpc
import coherence.proxy_service_messages_v1_pb2 as proxy_service_messages_v1_pb2
import coherence.proxy_service_messages_v1_pb2_grpc as proxy_service_messages_v1_pb2_grpc
import coherence.cache_service_messages_v1_pb2 as cache_service_messages_v1_pb2
import coherence.cache_service_messages_v1_pb2_grpc as cache_service_messages_v1_pb2_grpc
import coherence.common_messages_v1_pb2 as common_messages_v1_pb2
import coherence.common_messages_v1_pb2_grpc as common_messages_v1_pb2_grpc
from coherence import Session, NamedCache
from coherence.serialization import SerializerRegistry

serializer = SerializerRegistry.serializer("json")

def create_init_request():

    init_request = proxy_service_messages_v1_pb2.InitRequest(
        scope =  "",
        format = "json",
        protocol = "CacheService",
        protocolVersion = 1,
        supportedProtocolVersion = 1,
        heartbeat= 0,
    )

    return init_request


def create_ensure_cache_request(cache_name):
    ensure_cache_request = cache_service_messages_v1_pb2.EnsureCacheRequest(
        cache = cache_name
    )

    any_ensure_cache_request = Any()
    any_ensure_cache_request.Pack(ensure_cache_request)

    named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
        type = cache_service_messages_v1_pb2.NamedCacheRequestType.EnsureCache,
        message = any_ensure_cache_request,
    )

    return named_cache_request


def create_put_request(cache_id, key, value):
    put_request = cache_service_messages_v1_pb2.PutRequest(
        key = serializer.serialize(key),     # Serialized key
        value = serializer.serialize(value), # Serialized value
    )

    any_put_request = Any()
    any_put_request.Pack(put_request)

    named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
        type = cache_service_messages_v1_pb2.NamedCacheRequestType.Put,
        cacheId = cache_id,
        message = any_put_request,
    )

    return named_cache_request

def create_get_request(cache_id, key):
    get_request = BytesValue(value=serializer.serialize(key))
    any_get_request = Any()
    any_get_request.Pack(get_request)

    named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
        type = cache_service_messages_v1_pb2.NamedCacheRequestType.Get,
        cacheId = cache_id,
        message = any_get_request,
    )

    return named_cache_request

async def send_init_request(stream):
    # InitRequest
    init_request = proxy_service_messages_v1_pb2.ProxyRequest(
        id = 2,
        init = create_init_request(),
    )
    await stream.write(init_request)
    try:
        response = await stream.read()
        print(response)
        print("InitRequest request completed.")
    except grpc.aio._call.AioRpcError as e:
        if e.details() == 'Method not found: coherence.proxy.v1.ProxyService/subChannel' :
            print("Server is running v1 gRPC version")
            await stream.write(init_request)
            print("Checking if stream is closed")
        raise e

async def send_ensure_cache_request(stream, cache_name):
    # Ensure Cache
    ensure_cache_request = create_ensure_cache_request(cache_name)
    any_named_cache_request = Any()
    any_named_cache_request.Pack(ensure_cache_request)

    proxy_request = proxy_service_messages_v1_pb2.ProxyRequest(
        id = 12,
        message = any_named_cache_request,
    )
    await stream.write(proxy_request)
    cache_id = None
    while True:
        response = await stream.read()
        if response.HasField("message"):
            named_cache_response = cache_service_messages_v1_pb2.NamedCacheResponse()
            response.message.Unpack(named_cache_response)
            response_json = MessageToJson(named_cache_response)
            print("EnsureCache request successful. Response:")
            print(named_cache_response)
            print(response_json)
            cache_id = named_cache_response.cacheId
        elif response.HasField("error"):
            error_message = response.error
            print(f"EnsureCache request failed with error: {error_message}")
            return
        elif response.HasField("complete"):
            print("EnsureRequest Complete response received successfully.")
            break

    if cache_id is None:
        print("Failed to ensure cache.")
    else:
        return cache_id

async def send_put_request(stream, cache_id, key, value):
    # Put Request
    put_request = create_put_request(cache_id, key, value)
    any_named_cache_request = Any()
    any_named_cache_request.Pack(put_request)

    proxy_request = proxy_service_messages_v1_pb2.ProxyRequest(
        id = 22,
        message = any_named_cache_request,
    )
    await stream.write(proxy_request)
    while True:
        response = await stream.read()
        if response.HasField("message"):
            named_cache_response = cache_service_messages_v1_pb2.NamedCacheResponse()
            response.message.Unpack(named_cache_response)
            response_json = MessageToJson(named_cache_response)
            print("PUT request successful. Response:")
            print(named_cache_response)
            print(response_json)
        elif response.HasField("error"):
            error_message = response.error
            print(f"PUT request failed with error: {error_message}")
        elif response.HasField("complete"):
            print("PutRequest Complete response received successfully.")
            break

async def send_get_request(stream, cache_id, key):
    # Get Request
    get_request = create_get_request(cache_id, key)

    any_named_cache_request = Any()
    any_named_cache_request.Pack(get_request)

    proxy_request = proxy_service_messages_v1_pb2.ProxyRequest(
        id = 32,
        message = any_named_cache_request,
    )
    await stream.write(proxy_request)
    while True:
        response = await stream.read()
        if response.HasField("message"):
            named_cache_response = cache_service_messages_v1_pb2.NamedCacheResponse()
            response.message.Unpack(named_cache_response)
            if named_cache_response.HasField("message"):
                optional_value = common_messages_v1_pb2.OptionalValue()
                named_cache_response.message.Unpack(optional_value)
            print("GET request successful. Response:")
            print(named_cache_response)
            print(f"optional_value.present : {optional_value.present}")
            print(f"optional_value.value : {optional_value.value}")
            print(f"Retrieved value : {serializer.deserialize(optional_value.value)}")
        elif response.HasField("error"):
            error_message = response.error
            print(f"GET request failed with error: {error_message}")
        elif response.HasField("complete"):
            print("PutRequest Complete response received successfully.")
            break


async def run_requests():
    channel = grpc.aio.insecure_channel('localhost:1408')
    stub = proxy_service_v1_pb2_grpc.ProxyServiceStub(channel)
    stream = stub.subChannel()

    # InitRequest
    await send_init_request(stream)

    # Ensure Cache
    cache_name = "example_cache"
    cache_id = await send_ensure_cache_request(stream, cache_name)

    # Put Request
    key = "example_key"
    value = "example_value"
    await send_put_request(stream, cache_id, key, value)

    # Get Request
    await send_get_request(stream, cache_id, key)


# def exception_hook(exc_type, exc_value, tb):
#     print('Traceback:')
#     filename = tb.tb_frame.f_code.co_filename
#     name = tb.tb_frame.f_code.co_name
#     line_no = tb.tb_lineno
#     print(f"File {filename} line {line_no}, in {name}")
#
#     # Exception type and value
#     print(f"{exc_type.__name__}, Message: {exc_value}")
#
# sys.excepthook = exception_hook

async def run_request_real():
    s: Session = Session()
    c: NamedCache = await s.get_cache('new_example_cache')
    await c.put("example_key1", "example_value1")
    v = await c.get("example_key1")
    print(v)
    await s.close()

async def run_request_real2():
    s: Session = Session()
    c: NamedCache = await s.get_cache('new_example_cache')
    c2: NamedCache = await s.get_cache('new_example_cache2')
    await c.put("example_key1", "example_value1")
    await c2.put("example_key2", "example_value2")
    v = await c.get("example_key1")
    v2 = await c2.get("example_key2")
    print(v)
    print(v2)
    await s.close()

async def run_request_real3():
    s: Session = Session()
    c: NamedCache = await s.get_cache('new_example_cache')
    await c.put("example_key1", "example_value1")
    v = await c.get("example_key1")
    print(v)
    await c.truncate()
    await s.close()

async def run_request_real4():
    s: Session = Session()
    c: NamedCache = await s.get_cache('new_example_cache')
    await c.put("example_key1", "example_value1")
    v = await c.get("example_key1")
    print(v)
    await c.clear()
    v = await c.get("example_key1")
    print(v)
    await s.close()

async def run_request_real5():
    s: Session = Session()
    c: NamedCache = await s.get_cache('new_example_cache')
    await c.put("example_key1", "example_value1")
    v = await c.get("example_key1")
    print(v)
    await c.destroy()
    await s.close()

T = TypeVar("T")


class SimulateAsyncIterator(AsyncIterator):
    def __init__(self, the_list: list):
        super().__init__()
        self.the_list = the_list
        self.index = 0

    def __aiter__(self):
        self.index = 0
        return self

    async def __anext__(self):
        if self.index >= len(self.the_list):
            raise StopAsyncIteration
        await asyncio.sleep(0)  # Simulate an asynchronous operation
        item = self.the_list[self.index]
        self.index += 1
        return item

async def run_sumulator():
    data = [1, 2, 3, 4, 5]
    async for item in SimulateAsyncIterator(data):
        print(item)

if __name__ == "__main__":
    # asyncio.run(run_requests())
    # run_requests_mine()
    # asyncio.run(run_request_real())
    # asyncio.run(run_request_real2())
    # asyncio.run(run_request_real3())
    # asyncio.run(run_request_real4())
    #asyncio.run(run_request_real5())

    asyncio.run(run_sumulator())

