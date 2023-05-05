..
   Copyright (c) 2022, 2023, Oracle and/or its affiliates.
   Licensed under the Universal Permissive License v 1.0 as shown at
   https://oss.oracle.com/licenses/upl.

Entry Processing
================

Entry processors are a defining feature of Coherence and provide the ability
to send the data modification code into the grid and execute it where
the data is, against one or more entries.  This can not only significantly
impact how much data needs to be moved over the wire, but it also takes care
of cluster-wide concurrency control — each entry processor has the exclusive
access to the entry it is processing for the duration of its execution.

See the utility class `Processors <api_reference.html#processors>`_ for the
entry processors supported out-of-the-box by this client.

The following example demonstrates various entry processing operations
against a `NamedMap`:

.. literalinclude:: ../examples/processors.py
    :language: python
    :emphasize-lines: 37, 44, 51, 57-58, 62
    :linenos:

* Line 37 - insert a new Hobbit into the `NamedMap`
* Line 44 - invoke an entry processor to update the age of the inserted Hobbit
* Line 51 - insert a second Hobbit into the `NamedMap`
* Lines 57 - 58 - Increment the ages of all Hobbits in the `NamedMap` by 10.  Store the keys of the updated Hobbits
* Line 62 - get all of the updated Hobbits to display
