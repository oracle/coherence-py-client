# Copyright (c) 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

import asyncio
from dataclasses import dataclass
from typing import List

from coherence import NamedMap, Processors, Session


@dataclass
class Hobbit:
    """
    A simple class representing a Hobbit.
    """

    id: int
    name: str
    age: int


async def do_run() -> None:
    """
    Demonstrates various EntryProcessor operations against a NamedMap.

    :return: None
    """
    session: Session = await Session.create()
    try:
        namedMap: NamedMap[int, Hobbit] = await session.get_map("hobbits")

        await namedMap.clear()

        hobbit: Hobbit = Hobbit(1, "Bilbo", 111)
        print("Add new hobbit :", hobbit)
        await namedMap.put(hobbit.id, hobbit)

        print("NamedMap size is :", await namedMap.size())

        print("Hobbit from get() :", await namedMap.get(hobbit.id))

        print("Update Hobbit using processor ...")
        await namedMap.invoke(hobbit.id, Processors.update("age", 112))

        print("Updated Hobbit is :", await namedMap.get(hobbit.id))

        hobbit2: Hobbit = Hobbit(2, "Frodo", 50)

        print("Add new hobbit :", hobbit2)
        await namedMap.put(hobbit2.id, hobbit2)

        print("NamedMap size is :", await namedMap.size())

        print("Sending all Hobbits ten years into the future!")
        keys: List[int] = []
        async for entry in namedMap.invoke_all(Processors.increment("age", 10)):
            keys.append(entry.key)
            print("Updated age of Hobbit with id ", entry.key, "to", entry.value)

        print("Displaying all updated Hobbits ...")
        async for result in namedMap.get_all(set(keys)):
            print(result.value)

        await namedMap.remove(hobbit.id)
        await namedMap.remove(hobbit2.id)
    finally:
        await session.close()


asyncio.run(do_run())
