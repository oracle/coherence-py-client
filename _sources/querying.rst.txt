..
   Copyright (c) 2022, 2023, Oracle and/or its affiliates.
   Licensed under the Universal Permissive License v 1.0 as shown at
   https://oss.oracle.com/licenses/upl.

Querying
========

Being able to store and access data based on a key is great, but sometimes
you need more than that. Coherence allows you to query on any data attribute
present in your data model, and even allows you to define your own query
filter if one of the built-in ones doesn't fit the bill. If you defined an
index for a given query attribute, it will be used to optimize the query
execution and avoid unnecessary deserialization.

See the utility class `Filters <api_reference.html#filters>`_ for the
filters supported out-of-the-box by this client.

The following example demonstrates various querying operations
against a `NamedMap`:

.. literalinclude:: ../examples/filters.py
    :language: python
    :emphasize-lines: 40-41, 46, 50, 55
    :linenos:

* Lines 40-41 - insert twenty random Hobbits
* Line 46 - find all Hobbits, including their associated key, between the age of 17 and 21
* Line 50 - find all Hobbits, including their associated key, between the age of 17 and 30 that live in Hobbiton
* Line 55 - find all Hobbits, including their associated key, between the age of 17 and 25 that live in Hobbiton or Frogmorton
