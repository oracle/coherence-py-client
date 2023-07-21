### Coherence Python Client Examples

All examples in this directory assume that the Coherence Python Client has
been installed.

```bash
python3 -m pip install coherence-client
```

Be sure a Coherence gRPC proxy is available for the examples to work against.

```bash
docker run -d -p 1408:1408 ghcr.io/oracle/coherence-ce:22.06.5
```

### The Examples
* basics.py - basic CRUD operations
* python_object_keys_and_values.py - shows how to use standard Python objects as keys or values of a cache
* filters.py - using filters to filter results
* processors.py - using entry processors to mutate cache entries on the server without get/put
* aggregators.py - using entry aggregators to query a subset of entries to produce a result
* events.py - demonstrates cache lifecycle and cache entry events
