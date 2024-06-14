import grpc
import json
from google.protobuf.json_format import MessageToJson, Parse
from google.protobuf.any_pb2 import Any

# Import the generated protobuf and gRPC files
import coherence.proxy_service_v1_pb2 as proxy_service_v1_pb2
import coherence.proxy_service_v1_pb2_grpc as proxy_service_v1_pb2_grpc
import coherence.proxy_service_messages_v1_pb2 as proxy_service_messages_v1_pb2
import coherence.proxy_service_messages_v1_pb2_grpc as proxy_service_messages_v1_pb2_grpc
import coherence.cache_service_messages_v1_pb2 as cache_service_messages_v1_pb2
import coherence.cache_service_messages_v1_pb2_grpc as cache_service_messages_v1_pb2_grpc
import coherence.common_messages_v1_pb2 as common_messages_v1_pb2
import coherence.common_messages_v1_pb2_grpc as common_messages_v1_pb2_grpc
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
    any_ensure_cache_request.value = ensure_cache_request.SerializeToString()

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
    any_put_request.value = put_request.SerializeToString()

    named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
        type = cache_service_messages_v1_pb2.NamedCacheRequestType.Put,
        cacheId = cache_id,
        message = any_put_request,
    )

    return named_cache_request

def create_get_request(cache_id, key):
    get_request = cache_service_messages_v1_pb2.GetRequest(
        key = serializer.serialize(key)  # Serialized key
    )
    any_get_request = Any()
    any_get_request.value = get_request.SerializeToString()

    named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
        type = cache_service_messages_v1_pb2.NamedCacheRequestType.Get,
        cacheId = cache_id,
        message = any_get_request,
    )

    return named_cache_request

def run_requests():
    channel = grpc.insecure_channel('localhost:1408')
    stub = proxy_service_v1_pb2_grpc.ProxyServiceStub(channel)

    # InitRequest
    proxy_request = proxy_service_messages_v1_pb2.ProxyRequest(
        id = 2,
        init = create_init_request(),
    )
    responses = stub.subChannel(iter([proxy_request]))

    # for response in responses:
    #     print(response)
    #     print("InitRequest request completed.")
    response = next(responses)
    print(response)
    print("InitRequest request completed.")

    # Ensure Cache
    ensure_cache_request = create_ensure_cache_request("example_cache")
    any_named_cache_request = Any()
    any_named_cache_request.value = ensure_cache_request.SerializeToString()

    proxy_request = proxy_service_messages_v1_pb2.ProxyRequest(
        id = 12,
        message = any_named_cache_request,
    )
    responses = stub.subChannel(iter([proxy_request]))

    cache_id = None
    for response in responses:
        if response.HasField("message"):
            named_cache_response = cache_service_messages_v1_pb2.NamedCacheResponse()
            response.message.Unpack(named_cache_response)
            response_json = MessageToJson(named_cache_response)
            print("EnsureCache request successful. Response:")
            print(response_json)

            cache_id = named_cache_response.cacheId
            break
        elif response.HasField("error"):
            error_message = response.error
            print(f"EnsureCache request failed with error: {error_message}")
            return
        elif response.HasField("complete"):
            print("EnsureCache request completed.")

    if cache_id is None:
        print("Failed to ensure cache.")
        return

    # Put Request
    put_request = create_put_request(cache_id, b"example_key", b"example_value")
    any_named_cache_request = Any()
    any_named_cache_request.value = put_request.SerializeToString()

    proxy_request = proxy_service_messages_v1_pb2.ProxyRequest(
        id = 22,
        message = any_named_cache_request,
    )
    responses = stub.subChannel(iter([proxy_request]))
    for response in responses:
        if response.HasField("message"):
            named_cache_response = cache_service_messages_v1_pb2.NamedCacheResponse()
            response.message.Unpack(named_cache_response)
            response_json = MessageToJson(named_cache_response)
            print("PUT request successful. Response:")
            print(response_json)
        elif response.HasField("error"):
            error_message = response.error
            print(f"PUT request failed with error: {error_message}")
        elif response.HasField("complete"):
            print("PUT request completed.")

    # Get Request
    get_request = create_get_request(cache_id, b"example_key")

    any_named_cache_request = Any()
    any_named_cache_request.value = get_request.SerializeToString()

    proxy_request = proxy_service_messages_v1_pb2.ProxyRequest(
        id = 32,
        message = any_named_cache_request,
    )
    responses = stub.subChannel(iter([proxy_request]))
    for response in responses:
        if response.HasField("message"):
            named_cache_response = cache_service_messages_v1_pb2.NamedCacheResponse()
            response.message.Unpack(named_cache_response)
            response_json = MessageToJson(named_cache_response)
            print("GET request successful. Response:")
            print(response_json)
        elif response.HasField("error"):
            error_message = response.error
            print(f"GET request failed with error: {error_message}")
        elif response.HasField("complete"):
            print("GET request completed.")


def run_requests_mine():
    channel = grpc.insecure_channel('localhost:1408')
    stub = proxy_service_v1_pb2_grpc.ProxyServiceStub(channel)

    # InitRequest
    responses = stub.subChannel(iter([create_init_request()]))
    # responses = stub.subChannel(create_init_request())
    print(responses)

    cache_id = None
    for response in responses:
        print(response)
        if response.HasField("message"):
            named_cache_response = cache_service_messages_v1_pb2.NamedCacheResponse()
            response.message.Unpack(named_cache_response)
            response_json = MessageToJson(named_cache_response)
            print("EnsureCache request successful. Response:")
            print(response_json)

            cache_id = named_cache_response.cacheId
            break
        elif response.HasField("error"):
            error_message = response.error
            print(f"EnsureCache request failed with error: {error_message}")
            return
        elif response.HasField("complete"):
            print("EnsureCache request completed.")

    if cache_id is None:
        print("Failed to ensure cache.")
        return

if __name__ == "__main__":
    run_requests()
    # run_requests_mine()

