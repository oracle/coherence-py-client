..
   Copyright (c) 2022, 2023, Oracle and/or its affiliates.
   Licensed under the Universal Permissive License v 1.0 as shown at
   https://oss.oracle.com/licenses/upl.

The Basics
==========

he map (`NamedMap`) and cache (`NamedCache`) implementations provide the same basic features as the Map provided
by Python except for the following differences:

* key equality isn't restricted to reference equality
* insertion order is not maintained
* `set()` calls cannot be chained because of the asynchronous nature of the API

.. note::
    The only difference between `NamedCache` and `NamedMap` is that the `NamedCache` allows associating a `time-to-live` on the cache entry, while `NamedMap` does not

For the following examples, let's assume that we have a Map defined in Coherence named `Test`.
To get access to the map from the client:

.. code-block:: python

    from coherence import NamedMap, Session
    import asyncio

        # create a new Session to the Coherence server
        session: Session = Session(None)
        # create or get a map named Test from the session
        map: NamedMap = session.get_map("Test")

Once we have a handle to our map, we can invoke the same basic operations in Python:

.. code-block:: python

    await map.size()
    # returns 0

    await map.put("key1", "value1")
    await map.put("key2", "value2")

    await map.size()
    # returns 2

    await map.get("key1")
    # returns "value1"

    await map.get("key2")
    # returns "value2"

    await map.contains_key("key2")
    # returns true

    await map.contains_key("key3")
    # returns false

    await map.keys()
    # ["key1", "key2"]

    await map.values()
    # ["value1", "value2"]

    await map.entries()
    # [{key: "key1", value: "value1"}, {key: "key2", value: "value2"}]
