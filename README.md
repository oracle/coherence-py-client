# Python Client for Oracle Coherence

![CI/CD](https://github.com/oracle/coherence-py-client/actions/workflows/validate.yml/badge.svg)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=oracle_coherence-py-client&metric=alert_status)](https://sonarcloud.io/project/overview?id=oracle_coherence-py-client)
[![License](http://img.shields.io/badge/license-UPL%201.0-blue.svg)](https://oss.oracle.com/licenses/upl/)

<img src=https://oracle.github.io/coherence/assets/images/logo-red.png width="30%"><img>

The Coherence Python Client allows Python applications to act as cache clients to an Oracle Coherence cluster using gRPC as the network transport.

#### Features
* Familiar Map-like interface for manipulating cache entries including but not limited to:
    * `put`, `put_if_absent`, `put_all`, `get`, `get_all`, `remove`, `clear`, `get_or_default`, `replace`, `replace_mapping`, `size`, `is_empty`, `contains_key`, `contains_value`
* Cluster-side querying, aggregation and filtering of map entries
* Cluster-side manipulation of map entries using EntryProcessors
* Registration of listeners to be notified of:
    * mutations such as insert, update and delete on Maps
    * map lifecycle events such as truncated, released or destroyed
    * session lifecycle events such as connected, disconnected, reconnected and closed
* Support for storing Python objects as JSON as well as the ability to serialize to Java objects on the server for access from other Coherence language API's

#### Requirements
* [Coherence CE](https://github.com/oracle/coherence) 22.06.11+ or Coherence 14.1.1.2206.11+ Commercial edition with a configured [gRPCProxy](https://docs.oracle.com/en/middleware/standalone/coherence/14.1.1.2206/develop-remote-clients/using-coherence-grpc-server.html).
* Python 3.9.x


#### Starting a Coherence Cluster

Before testing the Python client, you must ensure a Coherence cluster is available.
For local development, we recommend using the Coherence CE Docker image; it contains
everything necessary for the client to operate correctly.

```bash
docker run -d -p 1408:1408 ghcr.io/oracle/coherence-ce:24.09.02
```

## Installation

```bash
python3 -m pip install coherence-client
```

## Documentation

[https://oracle.github.io/coherence-py-client/](https://oracle.github.io/coherence-py-client/)

## Examples

The following example connects to a Coherence cluster running gRPC Proxy on default
port of 1408, creates a new `NamedCache` with key `str` and value of a `str|int` and
issues `put()`, `get()`, `size()` and `remove` operations.

```python
from coherence import NamedCache, Session
import asyncio
from typing import Union


async def run_test():

    # create a new Session to the Coherence server
    session: Session = await Session.create()

    # create a new NamedCache with key of string|int and value of string|int
    cache: NamedCache[str, Union[str,int]] = await session.get_cache("test")

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
    print("The value of key \"two\" is " + str(r))

    # print the size of the cache
    print("Size of the cache test is " + str(await cache.size()))

    # remove an entry from the cache
    await cache.remove(k1)


# run the test
asyncio.run(run_test())
```
## Help

We have a **public Slack channel** where you can get in touch with us to ask questions about using the Coherence Python Client
or give us feedback or suggestions about what features and improvements you would like to see. We would love
to hear from you. To join our channel,
please [visit this site to get an invitation](https://join.slack.com/t/oraclecoherence/shared_invite/enQtNzcxNTQwMTAzNjE4LTJkZWI5ZDkzNGEzOTllZDgwZDU3NGM2YjY5YWYwMzM3ODdkNTU2NmNmNDFhOWIxMDZlNjg2MzE3NmMxZWMxMWE).
The invitation email will include details of how to access our Slack
workspace.  After you are logged in, please come to `#coherence` and say, "hello!"

If you would like to raise an issue please see [here](https://github.com/oracle/coherence-py-client/issues/new/choose).

## Contributing

This project welcomes contributions from the community. Before submitting a pull request, please [review our contribution guide](./CONTRIBUTING.md)

## Security

Please consult the [security guide](./SECURITY.md) for our responsible security vulnerability disclosure process

## License

Copyright (c) 2023, 2025, Oracle and/or its affiliates.

Released under the Universal Permissive License v1.0 as shown at
<https://oss.oracle.com/licenses/upl/>.
