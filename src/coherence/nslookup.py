import asyncio
import random
import struct
from typing import List, Optional, Tuple

DEFAULT_PORT = 7574
DEFAULT_HOST = "localhost"
CLUSTER_NAME_LOOKUP = "Cluster/name"
CLUSTER_INFO_LOOKUP = "Cluster/info"
CLUSTER_FOREIGN_LOOKUP = "Cluster/foreign"
MANAGEMENT_LOOKUP = "management/HTTPManagementURL"
JMX_LOOKUP = "management/JMXServiceURL"
METRICS_LOOKUP = "metrics/HTTPMetricsURL"
GRPC_PROXY_LOOKUP = "$GRPC:GrpcProxy"
NS_PREFIX = "NameService/string/"
NS_LOCAL_PORT = "/NameService/localPort"
DEFAULT_TIMEOUT = 10

MULTIPLEXED_SOCKET = bytes([90, 193, 224, 0])
NAME_SERVICE_SUB_PORT = bytes([0, 0, 0, 3])
# fmt: off
CONNECTION_OPEN = bytes([
    0, 1, 2, 0, 66, 0, 1, 14, 0, 0, 66, 166, 182, 159, 222, 178, 81,
    1, 65, 227, 243, 228, 221, 15, 2, 65, 143, 246, 186, 153, 1, 3,
    65, 248, 180, 229, 242, 4, 4, 65, 196, 254, 220, 245, 5, 5, 65, 215,
    206, 195, 141, 7, 6, 65, 219, 137, 220, 213, 10, 64, 2, 110, 3,
    93, 78, 87, 2, 17, 77, 101, 115, 115, 97, 103, 105, 110, 103, 80,
    114, 111, 116, 111, 99, 111, 108, 2, 65, 2, 65, 2, 19, 78, 97, 109,
    101, 83, 101, 114, 118, 105, 99, 101, 80, 114, 111, 116, 111, 99,
    111, 108, 2, 65, 1, 65, 1, 5, 160, 2, 0, 0, 14, 0, 0, 66, 174, 137,
    158, 222, 178, 81, 1, 65, 129, 128, 128, 240, 15, 5, 65, 152, 159,
    129, 128, 8, 6, 65, 147, 158, 1, 64, 1, 106, 2, 110, 3, 106, 4, 113,
    5, 113, 6, 78, 8, 67, 108, 117, 115, 116, 101, 114, 66, 9, 78, 9, 108,
    111, 99, 97, 108, 104, 111, 115, 116, 10, 78, 5, 50, 48, 50, 51, 51, 12,
    78, 16, 67, 111, 104, 101, 114, 101, 110, 99, 101, 67, 111, 110, 115,
    111, 108, 101, 64, 64,
])
CHANNEL_OPEN = bytes([
    0, 11, 2, 0, 66, 1, 1, 78, 19, 78, 97, 109, 101, 83, 101, 114, 118,
    105, 99, 101, 80, 114, 111, 116, 111, 99, 111, 108, 2, 78, 11, 78,
    97, 109, 101, 83, 101, 114, 118, 105, 99, 101, 64,
])
NS_LOOKUP_REQ_ID = bytes([1, 1, 0, 66, 0, 1, 78])
REQ_END_MARKER = bytes([64])
# fmt: on


class DiscoveredCluster:
    def __init__(self) -> None:
        self.cluster_name = ""
        self.connection_name = ""
        self.ns_port = 0
        self.host = ""
        self.management_urls: List[str] = []
        self.selected_url = ""
        self.metrics_urls: List[str] = []
        self.jmx_urls: List[str] = []
        self.grpc_proxy_endpoints: List[str] = []


class ClusterNSPort:
    def __init__(
        self, host_name: str = "", cluster_name: str = "", port: Optional[int] = 0, is_local: bool = False
    ) -> None:
        self.host_name = host_name
        self.cluster_name = cluster_name
        self.port = port
        self.is_local = is_local


class AsyncNSLookup:
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        self.host = host
        self.port = port
        self.channel = bytes()

        # These get initialized in connect(). Commented below to satisfy mypy
        # self.reader: Optional[asyncio.StreamReader]  = None
        # self.writer: Optional[asyncio.StreamWriter]  = None

    @staticmethod
    async def open(host_port: str = "", timeout: int = DEFAULT_TIMEOUT) -> "AsyncNSLookup":
        ns_lookup = AsyncNSLookup()
        if host_port:
            parts = host_port.split(":")
            if len(parts) == 1:
                ns_lookup.host = parts[0]
                ns_lookup.port = DEFAULT_PORT
            elif len(parts) == 2:
                ns_lookup.host = parts[0]
                ns_lookup.port = int(parts[1])
            else:
                raise ValueError(f"Invalid value for host/port: {host_port}")
        else:
            ns_lookup.host = DEFAULT_HOST
            ns_lookup.port = DEFAULT_PORT

        await ns_lookup.connect((ns_lookup.host, ns_lookup.port), timeout)
        return ns_lookup

    async def connect(self, address: Tuple[str, int], timeout: int = DEFAULT_TIMEOUT) -> None:
        self.reader, self.writer = await asyncio.open_connection(address[0], address[1])
        self.writer.write(MULTIPLEXED_SOCKET)
        self.writer.write(NAME_SERVICE_SUB_PORT)
        self.writer.write(self.write_packed_int(len(CONNECTION_OPEN)))
        self.writer.write(CONNECTION_OPEN)
        self.writer.write(self.write_packed_int(len(CHANNEL_OPEN)))
        self.writer.write(CHANNEL_OPEN)
        await self.writer.drain()

        await self.read_response()
        data = await self.read_response()
        self.channel = data[8 : 8 + len(data) - 9]

    async def lookup(self, name: str) -> str:
        response = await self.lookup_internal(name)
        if len(response) <= 7:
            return ""
        return self.read_string(response)

    async def lookup_internal(self, name: str) -> bytes:
        request = self.channel + NS_LOOKUP_REQ_ID
        request += self.write_packed_int(len(name)) + name.encode() + REQ_END_MARKER
        self.writer.write(self.write_packed_int(len(request)))
        self.writer.write(request)
        await self.writer.drain()

        response = await self.read_response()
        return response[len(self.channel) + 1 :]

    async def read_response(self) -> bytes:
        length, _ = await self.read_packed_int()
        data = await self.reader.read(length)
        return data

    async def read_packed_int(self) -> Tuple[int, int]:
        value = ord(await self.reader.read(1))
        negative = value & 0x40 != 0
        result = value & 0x3F
        bits = 6

        while value & 0x80:
            value = ord(await self.reader.read(1))
            result |= (value & 0x7F) << bits
            bits += 7

        if negative:
            result = ~result

        return result, bits

    @staticmethod
    def write_packed_int(n: int) -> bytes:
        result = b""
        b = 0
        if n < 0:
            b = 0x40
            n = ~n

        b |= n & 0x3F
        n >>= 6

        while n != 0:
            result += struct.pack("B", b | 0x80)
            b = n & 0x7F
            n >>= 7

        result += struct.pack("B", b)
        return result

    def read_string(self, data: bytes) -> str:
        length, pos = self.read_packed_int_from_string(data)
        return data[7 + (pos // 7) : 7 + (pos // 7) + length].decode()

    @staticmethod
    def read_packed_int_from_string(s: bytes) -> Tuple[int, int]:
        value = s[6]
        negative = value & 0x40 != 0
        result = value & 0x3F
        bits = 6

        while value & 0x80:
            value = s[7]
            result |= (value & 0x7F) << bits
            bits += 7

        if negative:
            result = ~result

        return result, bits

    async def close(self) -> None:
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()

    async def discover_cluster_info(self) -> DiscoveredCluster:
        cluster = DiscoveredCluster()
        cluster.ns_port = self.port
        cluster.host = self.host

        cluster.cluster_name = await self.lookup(CLUSTER_NAME_LOOKUP)
        cluster.management_urls = parse_results(await self.lookup(NS_PREFIX + MANAGEMENT_LOOKUP))
        cluster.jmx_urls = parse_results(await self.lookup(NS_PREFIX + JMX_LOOKUP))
        cluster.metrics_urls = parse_results(await self.lookup(NS_PREFIX + METRICS_LOOKUP))
        cluster.grpc_proxy_endpoints = parse_results(await self.lookup(NS_PREFIX + GRPC_PROXY_LOOKUP))

        return cluster

    async def discover_name_service_ports(self) -> List[ClusterNSPort]:
        local_cluster = await self.lookup(CLUSTER_NAME_LOOKUP)
        other_clusters = await self.lookup(NS_PREFIX + CLUSTER_FOREIGN_LOOKUP)
        other_clusters_list = parse_results(other_clusters)

        cluster_names = [local_cluster] + other_clusters_list
        list_clusters = [
            ClusterNSPort(
                cluster_name=name,
                port=self.port if name == local_cluster else None,
                host_name=self.host,
                is_local=name == local_cluster,
            )
            for name in cluster_names
        ]

        for cluster_ns_port in list_clusters[1:]:
            cluster_ns_port.port = int(
                await self.lookup(f"{NS_PREFIX}{CLUSTER_FOREIGN_LOOKUP}/{cluster_ns_port.cluster_name}{NS_LOCAL_PORT}")
            )

        return list_clusters

    @staticmethod
    async def do_resolution(name: str) -> Optional[DiscoveredCluster]:
        nslookup = None
        try:
            nslookup = await AsyncNSLookup.open(name)
            cluster_info = await nslookup.discover_cluster_info()
            return cluster_info
        except Exception as e:
            print(f"Error: {e}")
        finally:
            if nslookup is not None:
                await nslookup.close()
            return None

    @staticmethod
    def resolve_nslookup(name: str) -> str:
        cluster = asyncio.run(AsyncNSLookup.do_resolution(name))

        if cluster is not None:
            # Combine the list into host:port pairs
            pairs = [
                f"{cluster.grpc_proxy_endpoints[i]}:{cluster.grpc_proxy_endpoints[i + 1]}"
                for i in range(0, len(cluster.grpc_proxy_endpoints), 2)
            ]
            # Return a random pair
            return random.choice(pairs)
        else:
            # Return default address
            return "localhost:1408"


def parse_results(results: str) -> List[str]:
    results = results.strip("[]")
    return results.split(", ") if results else []


async def main() -> None:
    try:
        nslookup = await AsyncNSLookup.open("localhost:7574")
        print(f"Connected to {nslookup.host}:{nslookup.port}")

        # Example: Perform a lookup
        cluster_info = await nslookup.discover_cluster_info()
        print(f"Cluster Name: {cluster_info.cluster_name}")
        print(f"Management URLs: {cluster_info.management_urls}")
        print(f"JMX URLs: {cluster_info.jmx_urls}")
        print(f"Metrics URLs: {cluster_info.metrics_urls}")
        print(f"GRPC Endpoints: {cluster_info.grpc_proxy_endpoints}")

        ns_ports = await nslookup.discover_name_service_ports()
        for port_info in ns_ports:
            print(
                f"Cluster Name: {port_info.cluster_name}, Port: {port_info.port}, "
                f"Host: {port_info.host_name}, Is Local: {port_info.is_local}"
            )

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if "nslookup" in locals():
            await nslookup.close()


if __name__ == "__main__":
    asyncio.run(main())
