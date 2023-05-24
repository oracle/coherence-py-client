..
   Copyright (c) 2022, 2023, Oracle and/or its affiliates.
   Licensed under the Universal Permissive License v 1.0 as shown at
   https://oss.oracle.com/licenses/upl.

The Basics
==========

`NamedMap <api_reference.html#namedmap>`_ and `NamedCache <api_reference.html#namedcache>`_ are `dict`-like structures allowing users
to store data within a remote `Coherence <https://coherence.community/>`_ cluster.

The following is an example of using a `NamedMap` to `store`, `get`, and
`remove` simple keys and values:

.. literalinclude:: ../examples/basics.py
    :language: python
    :emphasize-lines: 17, 19, 21-34
    :linenos:

* Line 17 - Create a new `Session` that will connect to `localhost:1408`.  See the :doc:`Sessions <sessions>` documentation for more details.
* Line 50 - Obtain a `NamedMap` identified by `my-map` from the Session
* Lines 21-34 - Various CRUD operations against the NamedMap such as `get() <api_reference.html#coherence.NamedMap.get>`_, `put() <api_reference.html#coherence.NamedMap.put>`_, and `remove() <api_reference.html#coherence.NamedMap.remove>`_
