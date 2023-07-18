#!/bin/bash

#
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.
#

# Run compatability tests
set -e

# Set the following to include long running streaming tests
# INCLUDE_LONG_RUNNING=true

echo "Coherence CE 22.06.2"
COHERENCE_CLIENT_REQUEST_TIMEOUT=180.0 \
  make clean test-cluster-shutdown remove-app-images build-test-images test-cluster-startup just-wait test

echo "Coherence CE 22.06.2 with SSL"
RUN_SECURE=true COHERENCE_IGNORE_INVALID_CERTS=true \
  COHERENCE_TLS_CERTS_PATH=$(pwd)/tests/utils/certs/guardians-ca.crt \
  COHERENCE_TLS_CLIENT_CERT=$(pwd)/tests/utils/certs/star-lord.crt \
  COHERENCE_TLS_CLIENT_KEY=$(pwd)/tests/utils/certs/star-lord.pem \
  COHERENCE_CLIENT_REQUEST_TIMEOUT=180.0 \
  PROFILES=,secure make clean certs test-cluster-shutdown remove-app-images \
                                                  build-test-images test-cluster-startup just-wait test
