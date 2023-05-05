..
   Copyright (c) 2022, 2023, Oracle and/or its affiliates.
   Licensed under the Universal Permissive License v 1.0 as shown at
   https://oss.oracle.com/licenses/upl.

Aggregation
===========

Sometimes you don't need the actual data objects that are stored within the
data grid, but the derived, calculated result based on them. This is where
Coherence aggregation features come in handy.

Aggregations can be executed against the whole data set, or they can be
limited to a subset of the data using a query or a key set.  See the utility
class `Aggregators <api_reference.html#aggregators>`_ for the aggregators
supported out-of-the-box by this client.

The following example demonstrates various aggregation operations against
a `NamedMap`:

.. literalinclude:: ../examples/aggregators.py
    :language: python
    :emphasize-lines: 47, 50, 53, 56, 60
    :linenos:

* Line 47 - Returns a list of distinct hobbies across all entries
* Line 50 - Returns a count of all Hobbits
* Line 53 - Returns a count of all Hobbits over age 40
* Line 56 - Returns an average of all Hobbits under the age of 40
* Line 60 - For each hobby, list the oldest Hobbit for that interest
