# Copyright (c) 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

import asyncio

from coherence import Filters, NamedMap, Session
from coherence.event import MapLifecycleEvent, MapListener
from coherence.filter import MapEventFilter


async def do_run() -> None:
    """
    Demonstrates listeners for entry events and cache lifecycle.

    :return: None
    """
    session: Session = Session()
    try:
        namedMap: NamedMap[int, str] = await session.get_map("listeners-map")
        await namedMap.put(1, "1")

        print("NamedMap lifecycle events")

        namedMap.on(MapLifecycleEvent.RELEASED, lambda x: print("RELEASED", x))
        namedMap.on(MapLifecycleEvent.TRUNCATED, lambda x: print("TRUNCATE", x))
        namedMap.on(MapLifecycleEvent.DESTROYED, lambda x: print("DESTROYED", x))

        print("Truncating the NamedMap; this should generate an event ...")
        await namedMap.truncate()
        await asyncio.sleep(1)

        print("Releasing the NamedMap; this should generate an event ...")
        namedMap.release()
        await asyncio.sleep(1)

        print("Destroying the NamedMap; this should generate an event ...")
        await namedMap.destroy()
        await asyncio.sleep(1)

        print("\n\nNamedMap eventy events")

        namedMap = await session.get_map("listeners-map")

        listener1: MapListener[int, str] = MapListener()
        listener1.on_any(lambda e: print(e))

        print("Added listener for all events")
        print("Events will be generated when an entry is inserted, updated, and removed")
        await namedMap.add_map_listener(listener1)

        await namedMap.put(1, "1")
        await namedMap.put(1, "2")
        await namedMap.remove(1)
        await asyncio.sleep(1)

        await namedMap.remove_map_listener(listener1)

        print("\nAdded listener for all entries, but only when they are inserted")
        filter = Filters.event(Filters.always(), MapEventFilter.INSERTED)
        await namedMap.add_map_listener(listener1, filter)

        await namedMap.put(1, "1")
        await namedMap.put(1, "2")
        await namedMap.remove(1)
        await asyncio.sleep(1)

        await namedMap.remove_map_listener(listener1, filter)

        print("\nAdded listener for entries with a length larger than one, but only when they are updated or removed")
        filter = Filters.event(Filters.greater("length()", 1), MapEventFilter.UPDATED | MapEventFilter.DELETED)
        await namedMap.add_map_listener(listener1, filter)

        for i in range(12):
            await namedMap.put(i, str(i))
            await namedMap.put(i, str(i + 1))
            await namedMap.remove(i)

        await asyncio.sleep(1)

        await namedMap.remove_map_listener(listener1, filter)
        await namedMap.clear()
    finally:
        await session.close()


asyncio.run(do_run())
