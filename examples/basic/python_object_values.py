# Copyright (c) 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

import asyncio
from dataclasses import dataclass

from coherence import NamedMap, Processors, Session


@dataclass
class Hobbit:
    """
    A simple class representing a person.
    """

    id: int
    name: str
    age: int


async def do_run() -> None:
    """
    Demonstrates basic CRUD operations against a NamedMap using
    `int` keys and a custom python type, Person, as the value.

    :return: None
    """
    session: Session = Session()
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

        await namedMap.remove(hobbit.id)

        print("NamedMap size is :", await namedMap.size())
    finally:
        await session.close()


asyncio.run(do_run())
