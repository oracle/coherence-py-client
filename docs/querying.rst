..
   Copyright (c) 2022, 2023, Oracle and/or its affiliates.
   Licensed under the Universal Permissive License v 1.0 as shown at
   https://oss.oracle.com/licenses/upl.

Querying
========

Coherence provides a rich set of primitives that allow developers to create advanced queries against
a set of entries returning only those keys and/or values matching the specified criteria.
See the `documentation <https://oracle.github.io/coherence/23.03/api/java/index.html>`_ for details
on the Filters provided by this client.

Let's assume we have a `NamedMap` in which we're storing `string` keys and some objects with the structure of:

.. code-block:: javascript

    {
      "name"    : string,
      "age"     : number,
      "hobbies" : [] // of string
    }

First, let's insert a few objects:

.. code-block:: python

    await map.put("0001", {"name": "Bill Smith", "age": 38, "hobbies": ["gardening", "painting"]})
    await map.put("0002", {"name": "Fred Jones", "age": 56, "hobbies": ["racing", "golf"]})
    await map.put("0003", {"name": "Jane Doe", "age": 48, "hobbies": ["gardening", "photography"]})

Using a filter, we can limit the result set returned by the map:

.. code-block:: python

    from coherence import NamedMap, Session, Filters
    import asyncio

        # ...

        await map.entries(Filters.greater("age", 40))
        # [{key: "0002", value: {"name": "Fred Jones"...}}, {key: "0002", value: {"name": "Jane Doe"...}}]

        await map.keys(Filters.contains("hobbies", "gardening"))
        # ["0001", "0003"]

        await map.values(Filters.negate(Filters.array_contains("hobbies", "gardening")))
        # [{"name": "Fred Jones", "age": 56, "hobbies": ["racing", "golf"]}]
