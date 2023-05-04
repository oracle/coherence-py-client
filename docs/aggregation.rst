..
   Copyright (c) 2022, 2023, Oracle and/or its affiliates.
   Licensed under the Universal Permissive License v 1.0 as shown at
   https://oss.oracle.com/licenses/upl.

Aggregation
===========

Coherence provides developers with the ability to process some subset of the entries in a map, resulting in an
aggregated result. See the `documentation <https://oracle.github.io/coherence/23.03/api/java/index.html>`_ for aggregators provided by this client.

Assume the same set of keys and values are present from the filtering example:

.. code-block:: python

    from coherence import NamedMap, Session, Filters, Aggregators
    import asyncio

        # ...

        await map.aggregate(Aggregators.average("age"))
        # 47.3

        await map.aggregate(Aggregators.sum("age"))
        # 142

        await map.aggregate(Filters.greater("age", 40), Aggregators.count())
        # 2
