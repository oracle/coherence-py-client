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
init_request = proxy_service_messages_v1_pb2.InitRequest(
    scope =  "",
    format = "json",
    protocol = "CacheService",
    protocolVersion = 1,
    supportedProtocolVersion = 1,
    heartbeat= 0,
)

init_request_json = serializer.serialize(init_request)

proxy_request = proxy_service_messages_v1_pb2.ProxyRequest(
    id = 2,
    init = init_request,
)

ensure_cache_request = cache_service_messages_v1_pb2.EnsureCacheRequest(
    cache = "test_cache"
)
ensure_cache_request_json = serializer.serialize(ensure_cache_request)
any_ensure_cache_request = Any()
any_ensure_cache_request.value = ensure_cache_request_json

named_cache_request = cache_service_messages_v1_pb2.NamedCacheRequest(
    type = cache_service_messages_v1_pb2.NamedCacheRequestType.EnsureCache,
    message = any_ensure_cache_request,
)

print(init_request)