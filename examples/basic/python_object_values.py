# Copyright (c) 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

import asyncio

from dataclasses import dataclass

from coherence import NamedMap, Processors, Session


@dataclass
class Person:
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
        namedMap: NamedMap[int, Person] = await session.get_map("people")

        await namedMap.clear()

        person: Person = Person(1, "Bilbo", 111)
        print("Add new person : ", person)
        await namedMap.put(person.id, person)

        print("NamedMap size is : ", await namedMap.size())

        print("Person from get() : ", await namedMap.get(person.id))

        print("Update person using processor ...")
        await namedMap.invoke(person.id, Processors.update("age", 112))

        print("Updated person is : ", await namedMap.get(person.id))

        await namedMap.remove(person.id)

        print("NamedMap size is : ", await namedMap.size())
    finally:
        await session.close()


asyncio.run(do_run())
