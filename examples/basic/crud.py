# Copyright (c) 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

import asyncio

from coherence import NamedMap, Session


async def do_run() -> None:
    """
    Demonstrates basic CRUD operations against a NamedMap using
    `int` keys and `str` values.

    :return: None
    """
    session: Session = Session()
    try:
        namedMap: NamedMap[int, str] = await session.get_map("my-map")

        print("Put key 1; value one")
        await namedMap.put(1, "one")

        print("Value for key 1 is : ", await namedMap.get(1))

        print("NamedMap size is : ", await namedMap.size())

        print("Updating value of key 1 to ONE from ", await namedMap.put(1, "ONE"))

        print("Value for key 1 is : ", await namedMap.get(1))

        print("Removing key 1, current value : ", await namedMap.remove(1))

        print("NamedMap size is : ", await namedMap.size())
    finally:
        await session.close()


asyncio.run(do_run())
