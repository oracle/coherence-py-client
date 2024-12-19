# Copyright (c) 2024, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.
import asyncio
import time
from typing import Any, AsyncGenerator

import pytest_asyncio

import tests
from coherence import NamedCache, Session
from tests.person import Person


@pytest_asyncio.fixture
async def test_session() -> AsyncGenerator[Session, None]:
    session: Session = await tests.get_session()
    yield session
    await session.close()
    await asyncio.sleep(0)  # helps avoid loop already closed errors


@pytest_asyncio.fixture
async def cache(test_session: Session) -> AsyncGenerator[NamedCache[Any, Any], None]:
    cache: NamedCache[Any, Any] = await test_session.get_cache("test-" + str(time.time_ns()))
    yield cache
    await cache.truncate()


@pytest_asyncio.fixture
async def person_cache(cache: NamedCache[Any, Any]) -> AsyncGenerator[NamedCache[str, Person], None]:
    await Person.populate_named_map(cache)
    yield cache
