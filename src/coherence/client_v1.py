from __future__ import annotations

import asyncio
import uuid
from asyncio import Event

import grpc
from google.protobuf.json_format import MessageToJson, Parse
from google.protobuf.any_pb2 import Any
from google.protobuf.wrappers_pb2 import BytesValue

# Import the generated protobuf and gRPC files
import coherence.proxy_service_v1_pb2_grpc as proxy_service_v1_pb2_grpc
import coherence.proxy_service_messages_v1_pb2 as proxy_service_messages_v1_pb2
import coherence.cache_service_messages_v1_pb2 as cache_service_messages_v1_pb2
import coherence.common_messages_v1_pb2 as common_messages_v1_pb2
from coherence.serialization import SerializerRegistry

serializer = SerializerRegistry.serializer("json")


class Session_v1:
    def __init__(self, address: str, port: int):
        self.address = address
        self.port = port
        self.channel = grpc.aio.insecure_channel(address + ":" + str(port))
        self.stub = proxy_service_v1_pb2_grpc.ProxyServiceStub(self.channel)
        self.stream = self.stub.subChannel()
        self.is_open = True
        self.util = Util_v1(self)
        self.cache_map = dict()
        self.request_map = dict()
        self.is_initialized = False
        asyncio.create_task(self.util.handle_response())


    async def get_cache(self, cache_name: str) -> Cache_v1:
        if not self.is_initialized:
            await self.send_init_request()
            await asyncio.wait_for(self.util.get_result(), 1.0)
        if cache_name in self.cache_map:
            return self.cache_map[cache_name]
        else:
            await self.send_ensure_request(cache_name)
            cache_id = await asyncio.wait_for(self.util.get_result(), 1.0)
            self.cache_map[cache_name] = Cache_v1(self, cache_name, cache_id)
            return self.cache_map[cache_name]

    async def close(self):
        self.is_open = False
        await self.channel.close()


    async def send_init_request(self):
        # InitRequest
        req_id = Util_v1.create_unique_request_id()
        init_request = proxy_service_messages_v1_pb2.ProxyRequest(
            id = req_id,
            init = Util_v1.create_init_request(),
        )
        self.request_map[req_id] = init_request
        await self.stream.write(init_request)

    async def send_ensure_request(self, cache_name: str):
        # Ensure Cache
        req_id = Util_v1.create_unique_request_id()
        ensure_cache_request = Util_v1.create_ensure_cache_request(cache_name)
        any_named_cache_request = Any()
        any_named_cache_request.Pack(ensure_cache_request)

        proxy_request = proxy_service_messages_v1_pb2.ProxyRequest(
            id = req_id,
            message = any_named_cache_request,
        )
        self.request_map[req_id] = ensure_cache_request
        await self.stream.write(proxy_request)


class Cache_v1:
    def __init__(self, session: Session_v1, cache_name: str, cache_id: int):
        self.session = session
        self.cache_name = cache_name
        self.cache_id = cache_id

    @property
    def get_cache_name(self):
        return self.cache_name

    @property
    def get_cache_id(self):
        return self.cache_id

    async def put(self, key, value):
        # Put Request
        req_id = Util_v1.create_unique_request_id()
        put_request = Util_v1.create_put_request(self.cache_id, key, value)
        any_named_cache_request = Any()
        any_named_cache_request.Pack(put_request)

        proxy_request = proxy_service_messages_v1_pb2.ProxyRequest(
            id = req_id,
            message = any_named_cache_request,
        )
        self.session.request_map[req_id] = put_request
        await self.session.stream.write(proxy_request)
        await asyncio.wait_for(self.session.util.get_result(), 1.0)

    async def get(self, key):
        # Get Request
        req_id = Util_v1.create_unique_request_id()
        get_request = Util_v1.create_get_request(self.cache_id, key)

        any_named_cache_request = Any()
        any_named_cache_request.Pack(get_request)

        proxy_request = proxy_service_messages_v1_pb2.ProxyRequest(
            id = req_id,
            message = any_named_cache_request,
        )
        self.session.request_map[req_id] = get_request
        await self.session.stream.write(proxy_request)
        return await asyncio.wait_for(self.session.util.get_result(), 1.0)

class Util_v1:
    def __init__(self, session: Session_v1):
        self.session = session
        self.stream = self.session.stream
        self.result_available = Event()
        self.result_available.clear()
        self.response_result = None


    async def handle_response(self):
        while self.session.is_open:
            await asyncio.sleep(0.1)
            response = await self.stream.read()
            response_id = response.id
            if response.HasField("message"):
                req_type = self.session.request_map.get(response_id).type
                if req_type == cache_service_messages_v1_pb2.NamedCacheRequestType.EnsureCache:
                    named_cache_response = cache_service_messages_v1_pb2.NamedCacheResponse()
                    response.message.Unpack(named_cache_response)
                    response_json = MessageToJson(named_cache_response)
                    print("EnsureCache request successful. Response:")
                    print(named_cache_response)
                    print(response_json)
                    print(f"cache_id: {named_cache_response.cacheId}")
                    self.response_result = named_cache_response.cacheId
                elif req_type == cache_service_messages_v1_pb2.NamedCacheRequestType.Put:
                    named_cache_response = cache_service_messages_v1_pb2.NamedCacheResponse()
                    response.message.Unpack(named_cache_response)
                    response_json = MessageToJson(named_cache_response)
                    print("PUT request successful. Response:")
                    print(named_cache_response)
                    print(response_json)
                elif req_type == cache_service_messages_v1_pb2.NamedCacheRequestType.Get:
                    named_cache_response = cache_service_messages_v1_pb2.NamedCacheResponse()
                    response.message.Unpack(named_cache_response)
                    if named_cache_response.HasField("message"):
                        optional_value = common_messages_v1_pb2.OptionalValue()
                        named_cache_response.message.Unpack(optional_value)
                        if optional_value.present:
                            self.response_result = serializer.deserialize(optional_value.value)
                    print("GET request successful. Response:")
                    print(named_cache_response)
                    print(f"optional_value.present : {optional_value.present}")
                    print(f"optional_value.value : {optional_value.value}")
                    print(f"Retrieved value : {serializer.deserialize(optional_value.value)}")
                else:
                    pass
            elif response.HasField("init"):
                self.session.request_map.pop(response_id)
                print("InitRequest request completed.")
                self.result_available.set()
            elif response.HasField("error"):
                error_message = response.error
                print(f"EnsureCache request failed with error: {error_message}")
                return
            elif response.HasField("complete"):
                self.session.request_map.pop(response_id)
                print("EnsureRequest Complete response received successfully.")
                self.result_available.set()



    async def get_result(self):
        await self.result_available.wait()
        result = self.response_result
        self.response_result = None
        self.result_available.clear()
        return result


    @staticmethod
    def create_unique_request_id():
        # return uuid.uuid4().int & (1<<64)-1
        return uuid.uuid1().int>>96

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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