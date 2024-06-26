import asyncio

from coherence.client_v1 import Session_v1 as Session
from coherence.client_v1 import Cache_v1 as Cache

async def run_test():
    session = Session("localhost", 1408)
    cache :Cache = await session.get_cache("example_cache")

    await cache.put("example_key", "example_value")

    v = await cache.get("example_key")
    assert v == "example_value"
    print(f"value: {v}")

    await session.close()

if __name__ == "__main__":
    asyncio.run(run_test())
