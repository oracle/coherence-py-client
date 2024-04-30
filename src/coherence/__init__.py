# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

__version__ = "1.0rc2"

import logging

# expose these symbols in top-level namespace
from .aggregator import Aggregators as Aggregators
from .client import MapEntry as MapEntry
from .client import NamedCache as NamedCache
from .client import NamedMap as NamedMap
from .client import Options as Options
from .client import Session as Session
from .client import TlsOptions as TlsOptions
from .comparator import Comparator as Comparator
from .extractor import Extractors as Extractors
from .filter import Filters as Filters
from .processor import Processors as Processors

# default logging configuration for coherence
handler: logging.StreamHandler = logging.StreamHandler()  # type: ignore
handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

COH_LOG = logging.getLogger("coherence")
COH_LOG.setLevel(logging.INFO)
COH_LOG.addHandler(handler)
