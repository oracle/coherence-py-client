..
   Copyright (c) 2022, 2023, Oracle and/or its affiliates.
   Licensed under the Universal Permissive License v 1.0 as shown at
   https://oss.oracle.com/licenses/upl.

Sessions
========

Coherence uses the concept of a `Session` to manage a set of related Coherence resources,
such as maps and/or caches. When using the Coherence Python Client, a `Session` connects to a specific
gRPC endpoint and uses a specific serialization format to marshal requests and responses.
This means that different sessions using different serializers may connect to the same server endpoint. Typically,
for efficiency the client and server would be configured to use matching serialization formats to avoid
deserialization of data on the server, but this does not have to be the case. If the server is using a different
serializer for the server-side caches, it must be able to deserialize the client's requests, so there must be
a serializer configured on the server to match that used by the client.

.. note::
  Currently, the Coherence Python client only supports JSON serialization

A `Session` is constructed using an `Options` instance, or a generic object with the same keys and values.

The currently supported arguments foe `Options` are:
    - `address` - the address of the Coherence gRPC proxy.  This defaults to `localhost:1408`.
    - `request_timeout_seconds` - the gRPC request timeout in seconds.  This defaults to `30.0`.
    - `channel_options` - per-request gRPC channel options.
    - `tls_options` - options related to the configuration of TLS.

        - `enabled` - determines if TLS is enabled or not.  This defaults to `false` (NOTE: assumes `true` if all three `COHERENCE_TLS_*` (see subsequent bullets) environment variables are defined)
        - `ca_cert_path` - the path to the CA certificate.  This may be configured using the environment variable `COHERENCE_TLS_CERTS_PATH`
        - `client_cert_path` - the path to the client certificate. This may be configured with the environment variable `COHERENCE_TLS_CLIENT_CERT`
        - `client_key_path` - the path to the client certificate key. This may be configured with the environment variable `COHERENCE_TLS_CLIENT_KEY`

.. code-block::

    from coherence import NamedCache, Session
    import asyncio

       # create a new Session to the Coherence server
        session: Session = Session(None)

This is the simplest invocation which assumes the following defaults:
    - `address` is `localhost:1408`
    - `request_timeout_seconds` is `30.0`
    - `tls_options` is `disabled`

To use values other than the default, create a new `Options` instance, configure as desired,
and pass it to the constructor of the `Session`:

.. code-block::

    from coherence import NamedCache, Session
    import asyncio

       # create a new Session to the Coherence server
        addr: str = 'example.com:4444'
        opt: Options = Options(addr, default_scope, default_request_timeout, default_format)
        session: Session = Session(opt)

It's also possible to control the default address the session will bind to by providing
an address via the `COHERENCE_SERVER_ADDRESS` environment variable.  The format of the value would
be the same as if you configured it programmatically as the above example shows. The default timeout
can also be configured using `COHERENCE_CLIENT_REQUEST_TIMEOUT` environment variable.

Once the session has been constructed, it will now be possible to create maps and caches.