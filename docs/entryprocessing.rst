..
   Copyright (c) 2022, 2023, Oracle and/or its affiliates.
   Licensed under the Universal Permissive License v 1.0 as shown at
   https://oss.oracle.com/licenses/upl.

Entry Processing
================

An entry processor allows mutation of map entries in-place within the cluster instead of bringing the entire object
to the client, updating, and pushing the value back.  See the `documentation <https://oracle.github.io/coherence/23.03/api/java/index.html>`_ for the processors provided by this client.

Assume the same set of keys and values are present from the filtering and aggregation examples:

.. code-block:: python

    from coherence import NamedMap, Session, Filters, Aggregators, Processors
    import asyncio

        # ...

        # targeting a specific entry
        await map.invoke("0001", Processors.extract("age"))
        # returns: 38

        # targeting all entries
        await map.invoke_all(Processors.extract("age"))
        # returns: [["0001", 38], ["0002", 56], ["0003", 48]]

        # incrementing a number 'in-place'
        await map.invoke_all(Filters.greater("age", 40), Processors.increment("age", 1))
        # returns [["0002", 57], ["0003", 49]]

        # update a value 'in-place'
        await map.invoke("0001", Processors.update("age", 100))
        # returns true meaning the value was updated
        await map.get("0001")
        # the value will reflect the new age value
