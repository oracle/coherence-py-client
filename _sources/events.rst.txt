..
   Copyright (c) 2022, 2023, Oracle and/or its affiliates.
   Licensed under the Universal Permissive License v 1.0 as shown at
   https://oss.oracle.com/licenses/upl.

Events
======

Coherence provides the ability to subscribe to notifications pertaining to
a particular map/cache. In addition to listening for specific
events, it is possible to listen to events for changes made to a specific
key, or using a Filter, it's possible to limit the events raised to be
for a subset of the map entries.

The following example demonstrates using lifecycle and map events.

.. literalinclude:: ../examples/events.py
    :language: python
    :emphasize-lines: 25-39, 45-46, 50-54, 60-66, 71-77
    :linenos:

* Lines 25-39 - Using `NamedMap.on() <api_reference.html#coherence.NamedMap.on>`_,
  define listeners supported events and pass in a lambda to print the invocation.
  Then one by one, trigger each of the events and ensure enough time is given
  for the event to occur.
* Lines 45-46 - Create a new `MapListener <api_reference/event.html#maplistener>`_
  and for any event, print the result.
* Lines 50-54 - Add the `MapListener` that will be triggered on all events
  For this section, events will be printed for inserted, updated, and deleted.
* Lines 60-66 - Add the `MapListener` that will be triggered when any entry
  is inserted.  For this section, only the inserted event will be printed.
* 71-77 - Add the `MapListener` that will be triggered when an entry's value's
  length is greater than 1 and only for updated and removed events.  For this
  section, only updated and deleted events will be printed once the loop progresses
  enough to insert values larger than "9"
