#!/bin/bash

#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.
#

# Run compatability tests
set -e

# Set the following to include long running streaming tests
# INCLUDE_LONG_RUNNING=true

COH_VER=$1
if [ -z "${COH_VER}" ] ; then
  echo "Please provide Coherence version"
  exit 1
fi

BASE_IMAGE=$2
if [ -z "${BASE_IMAGE}" ] ; then
  echo "Please provide Base image"
  exit 1
fi

PROFILE_STR=$3
if [ -z "${PROFILE_STR}" ] ; then
  echo "Please provide Profile string"
  exit 1
fi

if [[ "${COH_VER}" =~ "22.06" ]] ; then
  echo "Coherence CE ${COH_VER}"
  COHERENCE_CLIENT_REQUEST_TIMEOUT=180.0 \
    COHERENCE_VERSION=$COH_VER \
    COHERENCE_BASE_IMAGE=$BASE_IMAGE \
    PROFILES=$PROFILE_STR \
    make clean test-cluster-shutdown remove-app-images build-test-images test-cluster-startup just-wait test
else
  echo "Coherence CE ${COH_VER}"
  COHERENCE_CLIENT_REQUEST_TIMEOUT=180.0 \
      COHERENCE_VERSION=$COH_VER \
      COHERENCE_BASE_IMAGE=$BASE_IMAGE \
      PROFILES=$PROFILE_STR \
      make clean test-cluster-shutdown remove-app-images build-test-images test-cluster-startup just-wait test-with-ai
fi

# Run tests with SSL
if [[ "${COH_VER}" =~ "22.06" ]] ; then
  echo "Coherence CE ${COH_VER} with SSL"
  RUN_SECURE=true COHERENCE_IGNORE_INVALID_CERTS=true \
    COHERENCE_TLS_CERTS_PATH=$(pwd)/tests/utils/certs/guardians-ca.crt \
    COHERENCE_TLS_CLIENT_CERT=$(pwd)/tests/utils/certs/star-lord.crt \
    COHERENCE_TLS_CLIENT_KEY=$(pwd)/tests/utils/certs/star-lord.pem \
    COHERENCE_CLIENT_REQUEST_TIMEOUT=180.0 \
    COHERENCE_VERSION=$COH_VER \
    COHERENCE_BASE_IMAGE=$BASE_IMAGE \
    PROFILES=$PROFILE_STR,secure \
    make clean certs test-cluster-shutdown remove-app-images \
                                                    build-test-images test-cluster-startup just-wait test
else
  echo "Coherence CE ${COH_VER} with SSL"
  RUN_SECURE=true COHERENCE_IGNORE_INVALID_CERTS=true \
    COHERENCE_TLS_CERTS_PATH=$(pwd)/tests/utils/certs/guardians-ca.crt \
    COHERENCE_TLS_CLIENT_CERT=$(pwd)/tests/utils/certs/star-lord.crt \
    COHERENCE_TLS_CLIENT_KEY=$(pwd)/tests/utils/certs/star-lord.pem \
    COHERENCE_CLIENT_REQUEST_TIMEOUT=180.0 \
    COHERENCE_VERSION=$COH_VER \
    COHERENCE_BASE_IMAGE=$BASE_IMAGE \
    PROFILES=$PROFILE_STR,secure \
    make clean certs test-cluster-shutdown remove-app-images \
                                                    build-test-images test-cluster-startup just-wait test-with-ai
fi
