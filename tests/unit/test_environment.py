# Copyright (c) 2024, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

import pytest

from coherence import Options, TlsOptions


def test_options_address(monkeypatch: pytest.MonkeyPatch) -> None:
    try:
        options: Options = Options()
        assert options.address == "localhost:1408"

        custom_address: str = "acme.com:1409"
        options = Options(address=custom_address)
        assert options.address == custom_address

        custom_address = "acme.com:1409"
        monkeypatch.setenv(name=Options.ENV_SERVER_ADDRESS, value=custom_address)
        options = Options()
        assert options.address == custom_address

        options = Options(address="127.0.0.1:9000")
        assert options.address == custom_address
    finally:
        monkeypatch.undo()


def test_options_req_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    try:
        monkeypatch.delenv(name=Options.ENV_REQUEST_TIMEOUT, raising=False)
        options: Options = Options()
        assert options.request_timeout_seconds == 30

        options = Options(request_timeout_seconds=15)
        assert options.request_timeout_seconds == 15

        monkeypatch.setenv(Options.ENV_REQUEST_TIMEOUT, "35")
        options = Options()
        assert options.request_timeout_seconds == 35

        options = Options(request_timeout_seconds=15)
        assert options.request_timeout_seconds == 35
    finally:
        monkeypatch.undo()


def test_options_ready_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    try:
        options: Options = Options()
        assert options.ready_timeout_seconds == 0

        options = Options(ready_timeout_seconds=15)
        assert options.ready_timeout_seconds == 15

        monkeypatch.setenv(Options.ENV_READY_TIMEOUT, "35")
        options = Options()
        assert options.ready_timeout_seconds == 35

        options = Options(ready_timeout_seconds=15)
        assert options.ready_timeout_seconds == 35
    finally:
        monkeypatch.undo()


def test_disconnect_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    try:
        options: Options = Options()
        assert options.session_disconnect_timeout_seconds == 30

        options = Options(session_disconnect_seconds=15)
        assert options.session_disconnect_timeout_seconds == 15

        monkeypatch.setenv(Options.ENV_SESSION_DISCONNECT_TIMEOUT, "35")
        options = Options()
        assert options.session_disconnect_timeout_seconds == 35

        options = Options(ready_timeout_seconds=15)
        assert options.session_disconnect_timeout_seconds == 35
    finally:
        monkeypatch.undo()


def test_tls_options(monkeypatch: pytest.MonkeyPatch) -> None:
    tls_options: TlsOptions = TlsOptions()
    assert tls_options.enabled is False
    assert tls_options.ca_cert_path is None
    assert tls_options.client_cert_path is None
    assert tls_options.client_key_path is None

    ca_cert_path: str = "/tmp/ca.pem"
    client_cert_path: str = "/tmp/client.pem"
    client_key_path: str = "/tmp/client.key"
    ca_cert_path2: str = "/tmp/ca2.pem"
    client_cert_path2: str = "/tmp/client2.pem"
    client_key_path2: str = "/tmp/client2.key"

    tls_options = TlsOptions(
        enabled=True, ca_cert_path=ca_cert_path, client_cert_path=client_cert_path, client_key_path=client_key_path
    )
    assert tls_options.enabled
    assert tls_options.ca_cert_path == ca_cert_path
    assert tls_options.client_cert_path == client_cert_path
    assert tls_options.client_key_path == client_key_path

    monkeypatch.setenv(name=TlsOptions.ENV_CA_CERT, value=ca_cert_path)
    monkeypatch.setenv(name=TlsOptions.ENV_CLIENT_CERT, value=client_cert_path)
    monkeypatch.setenv(name=TlsOptions.ENV_CLIENT_KEY, value=client_key_path)

    tls_options = TlsOptions()
    assert tls_options.enabled is False
    assert tls_options.ca_cert_path == ca_cert_path
    assert tls_options.client_cert_path == client_cert_path
    assert tls_options.client_key_path == client_key_path

    tls_options = TlsOptions(
        enabled=True, ca_cert_path=ca_cert_path2, client_cert_path=client_cert_path2, client_key_path=client_key_path2
    )
    assert tls_options.enabled
    assert tls_options.ca_cert_path == ca_cert_path
    assert tls_options.client_cert_path == client_cert_path
    assert tls_options.client_key_path == client_key_path

    monkeypatch.delenv(name=TlsOptions.ENV_CA_CERT)
    tls_options = TlsOptions(
        enabled=True, ca_cert_path=ca_cert_path2, client_cert_path=client_cert_path2, client_key_path=client_key_path2
    )
    assert tls_options.enabled
    assert tls_options.ca_cert_path == ca_cert_path2
    assert tls_options.client_cert_path == client_cert_path
    assert tls_options.client_key_path == client_key_path

    monkeypatch.delenv(name=TlsOptions.ENV_CLIENT_CERT)
    tls_options = TlsOptions(
        enabled=True, ca_cert_path=ca_cert_path2, client_cert_path=client_cert_path2, client_key_path=client_key_path2
    )
    assert tls_options.enabled
    assert tls_options.ca_cert_path == ca_cert_path2
    assert tls_options.client_cert_path == client_cert_path2
    assert tls_options.client_key_path == client_key_path

    monkeypatch.delenv(name=TlsOptions.ENV_CLIENT_KEY)
    tls_options = TlsOptions(
        enabled=True, ca_cert_path=ca_cert_path2, client_cert_path=client_cert_path2, client_key_path=client_key_path2
    )
    assert tls_options.enabled
    assert tls_options.ca_cert_path == ca_cert_path2
    assert tls_options.client_cert_path == client_cert_path2
    assert tls_options.client_key_path == client_key_path2
