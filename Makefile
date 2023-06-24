# ----------------------------------------------------------------------------------------------------------------------
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.
#
# ----------------------------------------------------------------------------------------------------------------------
# This is the Makefile to build the Coherence Python Client
# ----------------------------------------------------------------------------------------------------------------------

VERSION ?=0.9.0
CURRDIR := $(shell pwd)
USER_ID := $(shell echo "`id -u`:`id -g`")

override BUILD_BIN           := $(CURRDIR)/bin
override PROTO_DIR			 := $(CURRDIR)/etc/proto

# ----------------------------------------------------------------------------------------------------------------------
# Set the location of various build tools
# ----------------------------------------------------------------------------------------------------------------------
override BUILD_OUTPUT        := $(CURRDIR)/build/_output
override BUILD_BIN           := $(CURRDIR)/bin
override PROTO_OUT           := $(CURRDIR)/proto
override BUILD_TARGETS       := $(BUILD_OUTPUT)/targets
override TEST_LOGS_DIR       := $(BUILD_OUTPUT)/test-logs
override COVERAGE_DIR        := $(BUILD_OUTPUT)/coverage
override COPYRIGHT_JAR       := glassfish-copyright-maven-plugin-2.4.jar
override BUILD_CERTS         := $(CURRDIR)/tests/utils/certs
override ENV_FILE            := tests/utils/.env

# Maven version is always 1.0.0 as it is only for testing
MVN_VERSION ?= 1.0.0

# Coherence CE version to run base tests against
COHERENCE_VERSION ?= 22.06.4
COHERENCE_GROUP_ID ?= com.oracle.coherence.ce
COHERENCE_WKA1 ?= server1
COHERENCE_WKA2 ?= server1
CLUSTER_PORT ?= 7574
# Profiles to include for building
PROFILES ?=
COHERENCE_BASE_IMAGE ?= gcr.io/distroless/java17-debian11

# ----------------------------------------------------------------------------------------------------------------------
# Set the location of various build tools
# ----------------------------------------------------------------------------------------------------------------------
TOOLS_DIRECTORY   = $(CURRDIR)/build/tools
TOOLS_BIN         = $(TOOLS_DIRECTORY)/bin

# ----------------------------------------------------------------------------------------------------------------------
# The test application images used in integration tests
# ----------------------------------------------------------------------------------------------------------------------
RELEASE_IMAGE_PREFIX     ?= ghcr.io/oracle/
TEST_APPLICATION_IMAGE_1 := $(RELEASE_IMAGE_PREFIX)coherence-python-test-1:1.0.0
TEST_APPLICATION_IMAGE_2 := $(RELEASE_IMAGE_PREFIX)coherence-python-test-2:1.0.0
GO_TEST_FLAGS ?= -timeout 20m

# ----------------------------------------------------------------------------------------------------------------------
# Options to append to the Maven command
# ----------------------------------------------------------------------------------------------------------------------
MAVEN_OPTIONS ?= -Dmaven.wagon.httpconnectionManager.ttlSeconds=25 -Dmaven.wagon.http.retryHandler.count=3
MAVEN_BUILD_OPTS :=$(USE_MAVEN_SETTINGS) -Drevision=$(MVN_VERSION) -Dcoherence.version=$(COHERENCE_VERSION) -Dcoherence.group.id=$(COHERENCE_GROUP_ID) $(MAVEN_OPTIONS)

CURRDIR := $(shell pwd)

# ----------------------------------------------------------------------------------------------------------------------
# Clean-up all of the build artifacts
# ----------------------------------------------------------------------------------------------------------------------
.PHONY: clean
clean: ## Cleans the build
	@echo "Cleaning Project"
	-rm -rf $(CURRDIR)/build
#	-rm -rf $(PROTO_DIR)
	-rm -rf $(CURRDIR)/htmlcov
	-rm -rf $(CURRDIR)/.pytest_cache
	-rm -rf $(BUILD_CERTS)
	@mkdir -p $(BUILD_CERTS)
	mvn -B -f tests/java/coherence-python-test $(MAVEN_BUILD_OPTS) clean

.PHONY: certs
certs: ## Generates certificates for TLS tests
	@echo "Generating certs"
	./tests/scripts/keys.sh $(BUILD_CERTS)

# ----------------------------------------------------------------------------------------------------------------------
# Configure the build properties
# ----------------------------------------------------------------------------------------------------------------------
$(BUILD_PROPS):
	@echo "Creating build directories"
	@mkdir -p $(BUILD_OUTPUT)
	@mkdir -p $(BUILD_BIN)

# ----------------------------------------------------------------------------------------------------------------------
# Build the Coherence Go Client Test Image
# ----------------------------------------------------------------------------------------------------------------------
.PHONY: build-test-images
build-test-images: ## Build the Test images
	@echo "${MAVEN_BUILD_OPTS}"
	mvn -B -f tests/java/coherence-python-test clean package jib:dockerBuild -DskipTests -P member1$(PROFILES) -Djib.to.image=$(TEST_APPLICATION_IMAGE_1) -Dcoherence.test.base.image=$(COHERENCE_BASE_IMAGE) $(MAVEN_BUILD_OPTS)
	mvn -B -f tests/java/coherence-python-test clean package jib:dockerBuild -DskipTests -P member2$(PROFILES) -Djib.to.image=$(TEST_APPLICATION_IMAGE_2) -Dcoherence.test.base.image=$(COHERENCE_BASE_IMAGE) $(MAVEN_BUILD_OPTS)
	echo "CURRENT_UID=$(USER_ID)" >> $(ENV_FILE)


# ----------------------------------------------------------------------------------------------------------------------
# Download and build proto files
# ----------------------------------------------------------------------------------------------------------------------
.PHONY: generate-proto
generate-proto:  ## Generate Proto Files
	mkdir -p $(PROTO_DIR) || true
	curl -o $(PROTO_DIR)/services.proto https://raw.githubusercontent.com/oracle/coherence/$(COHERENCE_VERSION)/prj/coherence-grpc/src/main/proto/services.proto
	curl -o $(PROTO_DIR)/messages.proto https://raw.githubusercontent.com/oracle/coherence/$(COHERENCE_VERSION)/prj/coherence-grpc/src/main/proto/messages.proto
	python -m grpc_tools.protoc --proto_path=$(CURRDIR)/etc/proto --python_out=$(CURRDIR)/src/coherence --grpc_python_out=$(CURRDIR)/src/coherence $(CURRDIR)/etc/proto/messages.proto $(CURRDIR)/etc/proto/services.proto
	sed -e 's/import messages_pb2 as messages__pb2/import coherence.messages_pb2 as messages__pb2/' \
		< $(CURRDIR)/src/coherence/services_pb2_grpc.py > $(CURRDIR)/src/coherence/services_pb2_grpc.py.out
	mv $(CURRDIR)/src/coherence/services_pb2_grpc.py.out $(CURRDIR)/src/coherence/services_pb2_grpc.py

# ----------------------------------------------------------------------------------------------------------------------
# Run tests with code coverage
# ----------------------------------------------------------------------------------------------------------------------
.PHONY: test
test:  ##
	pytest -W error --cov src/coherence --capture=tee-sys --cov-report=term --cov-report=html \
		tests/test_serialization.py \
		tests/test_session.py \
		tests/test_client.py \
		tests/test_filters.py \
		tests/test_processors.py \
		tests/test_aggregators.py \

# ----------------------------------------------------------------------------------------------------------------------
# Run standards validation across project
# ----------------------------------------------------------------------------------------------------------------------
.PHONY: validate-setup
validate-setup:  ##
	poetry update
	pre-commit autoupdate

# ----------------------------------------------------------------------------------------------------------------------
# Run standards validation across project
# ----------------------------------------------------------------------------------------------------------------------
.PHONY: validate
validate:  ##
	pre-commit run --all-files

# ----------------------------------------------------------------------------------------------------------------------
# Obtain the protoc binary
# ----------------------------------------------------------------------------------------------------------------------
$(TOOLS_BIN)/protoc:
	@mkdir -p $(TOOLS_BIN)
	curl -Lo $(TOOLS_DIRECTORY)/protoc-3.19.4-osx-x86_64.zip https://github.com/protocolbuffers/protobuf/releases/download/v3.19.4/protoc-3.19.4-osx-x86_64.zip
	cd $(TOOLS_DIRECTORY)
	unzip -d $(TOOLS_DIRECTORY) $(TOOLS_DIRECTORY)/protoc-3.19.4-osx-x86_64.zip

#-----------------------------------------------------------------------------------------------------------------------
# Generate HTML documentation
# Run this target only in poetry shell
# The generated html pages are in $(CURRDIR)/docs/_build
# ----------------------------------------------------------------------------------------------------------------------
.PHONY: docs
docs:  ## Generate doc
	cd $(CURRDIR)/docs;	\
	poetry run sphinx-build -b html . _build

# ----------------------------------------------------------------------------------------------------------------------
# Startup cluster members via docker compose
# ----------------------------------------------------------------------------------------------------------------------
.PHONY: test-cluster-startup
test-cluster-startup: $(BUILD_PROPS) ## Startup any test cluster members using docker-compose
	cd tests/utils && docker-compose -f docker-compose-2-members.yaml up -d

# ----------------------------------------------------------------------------------------------------------------------
# Shutdown any cluster members via docker compose
# ----------------------------------------------------------------------------------------------------------------------
.PHONY: test-cluster-shutdown
test-cluster-shutdown: ## Shutdown any test cluster members using docker-compose
	cd tests/utils && docker-compose -f docker-compose-2-members.yaml down || true


# ----------------------------------------------------------------------------------------------------------------------
# Startup standalone coherence via java -jar
# ----------------------------------------------------------------------------------------------------------------------
.PHONY: test-coherence-startup
test-coherence-startup: ## Startup standalone cluster
	scripts/startup-clusters.sh $(TEST_LOGS_DIR) $(CLUSTER_PORT) $(COHERENCE_GROUP_ID) ${COHERENCE_VERSION}
	@echo "Clusters started up"

# ----------------------------------------------------------------------------------------------------------------------
# Shutdown coherence via java -jar
# ----------------------------------------------------------------------------------------------------------------------
.PHONY: test-coherence-shutdown
test-coherence-shutdown: ## shutdown standalone cluster
	@ps -ef | grep shutMeDownPlease | grep -v grep | awk '{print $$2}' | xargs kill -9 || true
	@echo "Clusters shutdown"

# ----------------------------------------------------------------------------------------------------------------------
# wait for 30 seconds
# ----------------------------------------------------------------------------------------------------------------------
.PHONY: just-wait
just-wait: ## sleep for 30 seconds
	@echo "Sleep for 30 seconds"
	sleep 30

# ----------------------------------------------------------------------------------------------------------------------
# Remove docker images
# ----------------------------------------------------------------------------------------------------------------------
.PHONY: remove-app-images
remove-app-images: ## Remove docker images
	@echo "Remove docker images"
	docker image rmi $(TEST_APPLICATION_IMAGE_1) $(TEST_APPLICATION_IMAGE_2) || true
