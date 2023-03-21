![CI/CD](https://github.com/oracle/coherence-py-client/actions/workflows/validate.yml/badge.svg)
# Coherence Python Client

The Coherence Python Client allows Python applications to act as cache clients to an Oracle Coherence cluster using
the Google gRPC framework as the network transport.

#### Features
* Familiar, dict-like, interface for manipulating dict entries
* Cluster-side querying and aggregation of dict entries
* Cluster-side manipulation of map entries using ``EntryProcessors``
* Registration of listeners that will be notified of dict entry mutations

#### Requirements
* [Coherence CE](https://github.com/oracle/coherence) 22.06 or later (or equivalent non-open source editions) with a configured [gRPCProxy](https://docs.oracle.com/en/middleware/standalone/coherence/14.1.1.2206/develop-remote-clients/using-coherence-grpc-server.html).
* Python 3.10.1

#### Starting a Coherence Cluster

Before testing the Python client, you must ensure a Coherence cluster is available.
For local development, we recommend using the Coherence CE Docker image; it contains
everything necessary for the client to operate correctly.

```bash
docker run -d -p 1408:1408 ghcr.io/oracle/coherence-ce:22.06.3
```

## Installation

```bash
pip install coherence
```

## Documentation


## Examples

The following example connects to a Coherence cluster running gRPC Proxy on default
port of 1408, creates a new `NamedCache` with key `str` and value of a `str|int` and
issues `put()`, `get()`, `size()` and `remove` operations.

```python
from coherence import NamedCache, Session

# create a new Session to the Coherence server
session: Session = Session(None)

# create a new NamedCache with key of string|int and value of string|int
cache: NamedCache[str, str|int] = await session.get_cache("test")

# put a new key/value
k: str = "one"
v: str = "only-one"
await cache.put(k, v)

# get the value for a key in the cache
r = await cache.get(k)

# print the value got for a key in the cache
print("The value of key \"one\" is " + r)

k1: str = "two"
v1: int = 2
await cache.put(k1, v1)
r = await cache.get(k1)
print("The value of key \"two\" is " + r)

# print the size of the cache
print("Size of the cache test is " + str(await cache.size()))

# remove an entry from the cache
await cache.remove(k1)
```
## Help

## Contributing

This project welcomes contributions from the community. Before submitting a pull request, please [review our contribution guide](./CONTRIBUTING.md)

## Security

Please consult the [security guide](./SECURITY.md) for our responsible security vulnerability disclosure process

## License

Copyright (c) 2022, 2023 Oracle and/or its affiliates.

Released under the Universal Permissive License v1.0 as shown at
<https://oss.oracle.com/licenses/upl/>.
