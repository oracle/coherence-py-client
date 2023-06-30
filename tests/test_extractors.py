# Copyright (c) 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from typing import Any, Optional, cast

import pytest

from coherence import Extractors
from coherence.extractor import (
    AbstractCompositeExtractor,
    ChainedExtractor,
    MultiExtractor,
    UniversalExtractor,
    ValueExtractor,
)


def test_extract_simple() -> None:
    result = Extractors.extract("simple")
    _validate_universal(result, "simple")


def test_extract_chained() -> None:
    result = Extractors.extract("prop1.prop2.prop3")
    _validate_composite(result, ChainedExtractor, 3)

    _validate_universal(result.extractors[0], "prop1")
    _validate_universal(result.extractors[1], "prop2")
    _validate_universal(result.extractors[2], "prop3")


def test_extract_multi() -> None:
    result = Extractors.extract("prop1,prop2,prop3")
    _validate_composite(result, MultiExtractor, 3)

    _validate_universal(result.extractors[0], "prop1")
    _validate_universal(result.extractors[1], "prop2")
    _validate_universal(result.extractors[2], "prop3")


def test_extract_method_no_parens() -> None:
    args = ["arg1", 10]
    result = Extractors.extract("length", args)
    _validate_universal(result, "length()", args)


def test_extract_method_with_parens() -> None:
    args = ["arg1", 10]
    result = Extractors.extract("length()", args)
    _validate_universal(result, "length()", args)


def test_extract_no_expression() -> None:
    with pytest.raises(ValueError):
        Extractors.extract(None)


def test_compose() -> None:
    result = Extractors.extract("prop1")
    result = result.compose(Extractors.extract("prop2"))

    _validate_composite(result, ChainedExtractor, 2)

    _validate_universal(result.extractors[0], "prop2")
    _validate_universal(result.extractors[1], "prop1")


def test_compose_no_extractor_arg() -> None:
    result = Extractors.extract("prop1")
    with pytest.raises(ValueError):
        result.compose(None)


def test_and_then_no_extractor_arg() -> None:
    result = Extractors.extract("prop1")
    with pytest.raises(ValueError):
        result.and_then(None)


def test_and_then() -> None:
    result = Extractors.extract("prop1")
    result = result.and_then(Extractors.extract("prop2"))

    _validate_composite(result, ChainedExtractor, 2)

    _validate_universal(result.extractors[0], "prop1")
    _validate_universal(result.extractors[1], "prop2")


def _validate_universal(extractor: ValueExtractor[Any, Any], expr: str, params: Optional[list[Any]] = None) -> None:
    assert extractor is not None
    assert isinstance(extractor, UniversalExtractor)

    extractor_local = cast(UniversalExtractor, extractor)
    assert extractor_local.name == expr
    assert extractor_local.params == params


def _validate_composite(extractor: ValueExtractor[Any, Any], expected_type: type, length: int) -> None:
    assert extractor is not None
    assert isinstance(extractor, expected_type)

    extractor_local = cast(AbstractCompositeExtractor, extractor)
    assert extractor_local.extractors is not None
    assert len(extractor_local.extractors) == length
