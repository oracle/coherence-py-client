# Copyright (c) 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

import asyncio
import logging
import os
import urllib
import urllib.request
from asyncio import Event
from time import time
from typing import Final

import pytest

import tests
from coherence import NamedCache, Session, Options, TlsOptions
from coherence.event import MapLifecycleEvent, SessionLifecycleEvent
from tests import CountingMapListener

COH_LOG = logging.getLogger("coherence-test")
EVENT_TIMEOUT: Final[float] = 5.0


@pytest.mark.asyncio
async def test_basics() -> None:
    """Test initial session state and post-close invocations raise error"""

    run_secure: str = "RUN_SECURE"
    session: Session = await tests.get_session()

    assert session.channel is not None
    assert session.scope == Options.DEFAULT_SCOPE
    assert session.format == Options.DEFAULT_FORMAT
    assert session.session_id is not None
    assert session.options is not None

    if run_secure in os.environ:
        assert session.options.tls_options is not None
        assert session.options.tls_options.enabled
        assert session.options.tls_options.client_key_path == os.environ.get(TlsOptions.ENV_CLIENT_KEY)
        assert session.options.tls_options.ca_cert_path == os.environ.get(TlsOptions.ENV_CA_CERT)
        assert session.options.tls_options.client_cert_path == os.environ.get(TlsOptions.ENV_CLIENT_CERT)
    else:
        assert session.options.tls_options is None
        assert session.options.channel_options is None

    assert session.options.session_disconnect_timeout_seconds == Options.DEFAULT_SESSION_DISCONNECT_TIMEOUT

    if Options.ENV_REQUEST_TIMEOUT in os.environ:
        assert session.options.request_timeout_seconds == float(os.environ.get(Options.ENV_REQUEST_TIMEOUT))
    else:
        assert session.options.request_timeout_seconds == Options.DEFAULT_REQUEST_TIMEOUT

    assert session.options.ready_timeout_seconds == Options.DEFAULT_READY_TIMEOUT
    assert session.options.format == Options.DEFAULT_FORMAT
    assert session.options.scope == Options.DEFAULT_SCOPE
    assert session.options.address == Options.DEFAULT_ADDRESS
    assert session.is_ready()
    assert not session.closed

    await session.close()
    await asyncio.sleep(.1)

    assert session.channel is None
    assert session.scope == ""
    assert session.options is not None

    if run_secure in os.environ:
        assert session.options.tls_options is not None
        assert session.options.tls_options.enabled
        assert session.options.tls_options.client_key_path == os.environ.get(TlsOptions.ENV_CLIENT_KEY)
        assert session.options.tls_options.ca_cert_path == os.environ.get(TlsOptions.ENV_CA_CERT)
        assert session.options.tls_options.client_cert_path == os.environ.get(TlsOptions.ENV_CLIENT_CERT)
    else:
        assert session.options.tls_options is None
        assert session.options.channel_options is None

    assert session.options.session_disconnect_timeout_seconds == Options.DEFAULT_SESSION_DISCONNECT_TIMEOUT

    if Options.ENV_REQUEST_TIMEOUT in os.environ:
        assert session.options.request_timeout_seconds == float(os.environ.get(Options.ENV_REQUEST_TIMEOUT))
    else:
        assert session.options.request_timeout_seconds == Options.DEFAULT_REQUEST_TIMEOUT

    assert session.options.ready_timeout_seconds == Options.DEFAULT_READY_TIMEOUT
    assert session.options.format == Options.DEFAULT_FORMAT
    assert session.options.scope == Options.DEFAULT_SCOPE
    assert session.options.address == Options.DEFAULT_ADDRESS
    assert not session.is_ready()
    assert session.closed

    with pytest.raises(Exception):
        await session.get_cache("test")

    with pytest.raises(Exception):
        session.on(SessionLifecycleEvent.CLOSED, lambda: None)


@pytest.mark.asyncio
async def test_cache_release_event() -> None:
    await _validate_cache_event(MapLifecycleEvent.RELEASED)


@pytest.mark.asyncio
async def test_cache_destroy_event() -> None:
    await _validate_cache_event(MapLifecycleEvent.DESTROYED)


@pytest.mark.asyncio
async def test_session_lifecycle() -> None:
    conn_event: Event = Event()
    disconn_event: Event = Event()
    reconn_event: Event = Event()
    close_event: Event = Event()

    def conn_callback() -> None:
        COH_LOG.info("Connection active")
        nonlocal conn_event
        conn_event.set()

    def disconn_callback() -> None:
        COH_LOG.info("Detected disconnect")
        nonlocal disconn_event
        disconn_event.set()

    def reconn_callback() -> None:
        COH_LOG.info("Detected reconnect")
        nonlocal reconn_event
        reconn_event.set()

    def close_callback() -> None:
        COH_LOG.info("Detected close")
        nonlocal close_event
        close_event.set()

    session: Session = await tests.get_session()
    session.on(SessionLifecycleEvent.CONNECTED, conn_callback)
    session.on(SessionLifecycleEvent.DISCONNECTED, disconn_callback)
    session.on(SessionLifecycleEvent.RECONNECTED, reconn_callback)
    session.on(SessionLifecycleEvent.CLOSED, close_callback)

    await asyncio.wait_for(_waiter(conn_event), EVENT_TIMEOUT)
    assert session.is_ready()

    await _shutdown_proxy()

    await asyncio.wait_for(_waiter(disconn_event), EVENT_TIMEOUT)
    assert session.is_ready()
    await asyncio.wait_for(_waiter(reconn_event), EVENT_TIMEOUT)
    assert session.is_ready()

    await session.close()
    assert not session.is_ready()

    await asyncio.wait_for(_waiter(close_event), EVENT_TIMEOUT)
    assert not session.is_ready()


@pytest.mark.asyncio
async def test_wait_for_ready() -> None:
    session: Session = await tests.get_session(10.0)
    print(f"Session -> {session}")

    logging.debug("Getting cache ...")

    try:
        count: int = 50
        cache: NamedCache[str, str] = await session.get_cache("test-" + str(int(time() * 1000)))
        print(f"Cache -> {cache}")
        return

        listener: CountingMapListener[str, str] = CountingMapListener("Test")

        COH_LOG.debug("Adding MapListener ...")
        await cache.add_map_listener(listener)

        COH_LOG.debug("Inserting values ...")
        for i in range(count):
            await cache.put(str(i), str(i))

        COH_LOG.debug("Waiting for [%s] MapEvents ...", count)
        await listener.wait_for(count, 15)
        COH_LOG.debug("All events received!")

        listener.reset()

        disc_event: Event = Event()

        def disc() -> None:
            COH_LOG.debug("Detected session disconnect!")
            nonlocal disc_event
            disc_event.set()

        session.on(SessionLifecycleEvent.DISCONNECTED, disc)

        await _shutdown_proxy()

        COH_LOG.debug("Waiting for session disconnect ...")
        async with asyncio.timeout(10):
            await disc_event.wait()

        # start inserting values as soon as disconnect occurs to ensure
        # that we properly wait for the session to reconnect before
        # issuing RPC
        COH_LOG.debug("Inserting second set of values ...")
        for i in range(count):
            await cache.put(str(i), str(i))

        COH_LOG.debug("Waiting for [%s] MapEvents ...", count)
        await listener.wait_for(count, 15)
        COH_LOG.debug("All events received!")

    finally:
        await session.close()


@pytest.mark.asyncio
async def test_fail_fast() -> None:
    session: Session = await tests.get_session()
    logging.debug("Getting cache ...")

    try:
        count: int = 10
        cache: NamedCache[str, str] = await session.get_cache("test-" + str(int(time() * 1000)))

        listener: CountingMapListener[str, str] = CountingMapListener("Test")

        COH_LOG.debug("Adding MapListener ...")
        await cache.add_map_listener(listener)

        COH_LOG.debug("Inserting values ...")
        for i in range(count):
            await cache.put(str(i), str(i))

        COH_LOG.debug("Waiting for [%s] MapEvents ...", count)
        await listener.wait_for(count, 15)
        COH_LOG.debug("All events received!")

        listener.reset()

        disc_event: Event = Event()
        reconn_event: Event = Event()

        def disc() -> None:
            COH_LOG.debug("Detected session disconnect!")
            nonlocal disc_event
            disc_event.set()

        def reconn() -> None:
            COH_LOG.debug("Detected session reconnect!")
            nonlocal reconn_event
            reconn_event.set()

        session.on(SessionLifecycleEvent.DISCONNECTED, disc)
        session.on(SessionLifecycleEvent.RECONNECTED, reconn)

        COH_LOG.debug("Shutting down the gRPC Proxy ...")
        req: urllib.request.Request = urllib.request.Request(
            "http://127.0.0.1:30000/management/coherence/cluster/services/$GRPC:GrpcProxy/members/1/stop", method="POST"
        )
        with urllib.request.urlopen(req) as response:
            response.read()

        COH_LOG.debug("Waiting for session disconnect ...")
        async with asyncio.timeout(10):
            await disc_event.wait()

        # start inserting values as soon as disconnect occurs to ensure
        # that we properly wait for the session to reconnect before
        # issuing RPC
        COH_LOG.debug("Inserting second set of values; expecting error")
        for i in range(count):
            try:
                await cache.put(str(i), str(i))
                pytest.fail("No exception thrown by RPC")
            except Exception as e:
                print("Caught error: " + str(e))

        COH_LOG.debug("Waiting for session reconnect ...")
        async with asyncio.timeout(10):
            await reconn_event.wait()

    finally:
        await session.close()


async def _validate_cache_event(lifecycle_event: MapLifecycleEvent) -> None:
    session: Session = await tests.get_session()
    cache: NamedCache[str, str] = await session.get_cache("test-" + str(int(time() * 1000)))
    name: str = "UNSET"
    event: Event = Event()

    def callback(n: str) -> None:
        nonlocal name
        name = n
        event.set()

    session.on(lifecycle_event, callback)

    try:
        await cache.put("A", "B")
        await cache.put("C", "D")
        assert await cache.size() == 2

        if lifecycle_event == MapLifecycleEvent.RELEASED:
            cache.release()
        else:
            await cache.destroy()

        await asyncio.wait_for(_waiter(event), EVENT_TIMEOUT)

        assert name == cache.name
        assert cache.released

        if lifecycle_event == MapLifecycleEvent.DESTROYED:
            assert cache.destroyed
        else:
            assert not cache.destroyed

        assert not cache.active
    finally:
        await session.close()


async def _waiter(event: Event) -> None:
    await event.wait()


async def _shutdown_proxy() -> None:
    COH_LOG.debug("Shutting down the gRPC Proxy ...")
    req: urllib.request.Request = urllib.request.Request(
        "http://127.0.0.1:30000/management/coherence/cluster/services/$GRPC:GrpcProxy/members/1/stop", method="POST"
    )
    with urllib.request.urlopen(req) as response:
        response.read()
