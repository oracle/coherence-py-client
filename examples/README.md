### Coherence Python Client Examples

All examples in this directory assume that the Coherence Python Client has
been installed.

```bash
python3 -m pip install coherence-client
```

Be sure a Coherence gRPC proxy is available for the examples to work against.

```bash
docker run -d -p 1408:1408 ghcr.io/oracle/coherence-ce:22.06.11
```

> [!NOTE]
> Coherence AI  [vector_search.py](vector_search.py) example requires installation of `sentence-transformers` package so that the example code can use the `all-MiniLM-L6-v2` model for generating text embeddings
>
> ```bash
> python3 -m pip install sentence-transformers
> ```


### The Examples
* [basics.py](basics.py) - basic CRUD operations
* [python_object_keys_and_values.py](python_object_keys_and_values.py) - shows how to use standard Python objects as keys or values of a cache
* [filters.py](filters.py) - using filters to filter results
* [processors.py](processors.py) - using entry processors to mutate cache entries on the server without get/put
* [aggregators.py](aggregators.py) - using entry aggregators to query a subset of entries to produce a result
* [events.py](events.py) - demonstrates cache lifecycle and cache entry events
* [vector_search.py](vector_search.py) - shows how to use some of the Coherence AI features to store vectors and perform a k-nearest neighbors (k-nn) search on those vectors.
