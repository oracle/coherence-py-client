# Copyright (c) 2022 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional, Sequence, TypeVar, cast

from coherence.serialization import proxy

K = TypeVar("K", covariant=True)
V = TypeVar("V", covariant=True)
R = TypeVar("R", covariant=True)


class ValueExtractor(ABC):
    def __init__(self) -> None:
        """
        ValueExtractor is used to both extract values (for example, for sorting or filtering) from an object,
        and to provide an identity for that extraction.

        Construct a ValueExtractor.
        """
        super().__init__()

    def compose(self, before: ValueExtractor) -> ValueExtractor:
        """
        Returns a composed extractor that first applies the *before* extractor to its input, and then applies this
        extractor to the result. If evaluation of either extractor throws an exception, it is relayed to the caller
        of the composed extractor.

        :param before: the extractor to apply before this extractor is applied
        :return: a composed extractor that first applies the *before* extractor and then applies this extractor
        """
        if before is None:
            raise ValueError("before cannot be null")
        if type(before) == ValueExtractor:
            return before.and_then(self)
        else:
            return ChainedExtractor([before, self])

    def and_then(self, after: ValueExtractor) -> ValueExtractor:
        """
        Returns a composed extractor that first applies this extractor to its input, and then applies the *after*
        extractor to the result. If evaluation of either extractor throws an exception, it is relayed to the caller
        of the composed extractor.

        :param after: the extractor to apply after this extractor is applied
        :return: a composed extractor that first applies this extractor and then applies the *after* extractor
        """
        if after is None:
            raise ValueError("after cannot be null")
        if type(after) == ChainedExtractor:
            return ChainedExtractor([self, after])
        else:
            return after.compose(self)

    @classmethod
    def extract(cls, from_field_or_method: str, params: Optional[list[Any]] = None) -> ValueExtractor:
        """
        Returns an extractor that extracts the value of the specified field.

        :param from_field_or_method: he name of the field or method to extract the value from.
        :param params: the parameters to pass to the method.
        :return: an instance of :func:`coherence.extractor.UniversalExtractor`
        """
        return UniversalExtractor(from_field_or_method, params)


@proxy("extractor.UniversalExtractor")
class UniversalExtractor(ValueExtractor):
    def __init__(self, name: str, params: Optional[list[Any]] = None) -> None:
        """
        Universal ValueExtractor implementation.

        Either a property or method based extractor based on parameters passed to constructor. Generally,
        the name value passed to the `UniversalExtractor` constructor represents a property unless the *name* value
        ends in `()`, then this instance is a reflection based method extractor.

        Construct a UniversalExtractor based on a name and optional parameters.

        If *name* does not end in `()`, this extractor is a property extractor. If `name` is prefixed with one of
        `set` or `get` and ends in `()`, this extractor is a property extractor. If the *name* just ends in `()`,
        this extractor is considered a method extractor.

        :param name: A method or property name.
        :param params: he parameter array. Must be `null` or `zero length` for a property based extractor.
        """
        super().__init__()
        self.name: str = name
        self.params = params

    @classmethod
    def create(cls, name: str, params: Optional[list[Any]] = None) -> UniversalExtractor:
        """
        Class method to create an instance of :func:`coherence.extractor.UniversalExtractor`

        :param name: A method or property name.
        :param params: he parameter array. Must be `null` or `zero length` for a property based extractor.
        :return: an instance of :func:`coherence.extractor.UniversalExtractor`
        """
        return cls(name, params)


class AbstractCompositeExtractor(ValueExtractor):
    def __init__(self, extractors: Sequence[ValueExtractor]) -> None:
        """
        Abstract super class for :func:`coherence.extractor.ValueExtractor` implementations that are based on an
        underlying array of :func:`coherence.extractor.ValueExtractor` objects.

        :param extractors: an array of extractors
        """
        super().__init__()
        self.extractors = extractors


@proxy("extractor.ChainedExtractor")
class ChainedExtractor(AbstractCompositeExtractor):
    def __init__(self, extractors_or_method: str | Sequence[ValueExtractor]) -> None:
        """
        Composite :func:`coherence.extractor.ValueExtractor` implementation based on an array of extractors. The
        extractors in the array are applied sequentially left-to-right, so a result of a previous extractor serves as
        a target object for a next one.

        :param extractors_or_method: an array of :func:`coherence.extractor.ValueExtractor`, or a dot-delimited
         sequence of method names which results in a ChainedExtractor that is based on an array of corresponding
         :func:`coherence.extractor.UniversalExtractor` objects
        """
        if type(extractors_or_method) == str:
            e = list()
            names = extractors_or_method.split(".")
            for name in names:
                v = UniversalExtractor(name)
                e.append(v)
            super().__init__(e)
        else:
            super().__init__(cast(Sequence[ValueExtractor], extractors_or_method))


@proxy("extractor.IdentityExtractor")
class IdentityExtractor(ValueExtractor):
    __instance = None

    def __init__(self) -> None:
        """
        A Trivial :func:`coherence.extractor.ValueExtractor` implementation that does not actually extract anything
        from the passed value, but returns the value itself.

        Constructs a new `IdentityExtractor` instance.
        """
        super().__init__()


class ValueUpdater(ABC):
    def __init__(self) -> None:
        """
        ValueUpdater is used to update an object's state.

        Constructs a new `ValueUpdater`.
        """
        super().__init__()


class ValueManipulator(ValueUpdater):
    """ValueManipulator represents a composition of :func:`coherence.extractor.ValueExtractor` and
    :func:`coherence.extractor.ValueUpdater` implementations."""

    @abstractmethod
    def get_extractor(self) -> ValueExtractor:
        """
        Retrieve the underlying ValueExtractor reference.

        :rtype: the ValueExtractor
        """

    @abstractmethod
    def get_updator(self) -> ValueUpdater:
        """
        Retrieve the underlying ValueUpdater reference.

        :rtype: the ValueUpdater
        """


@proxy("extractor.CompositeUpdater")
class CompositeUpdater(ValueManipulator):
    """A ValueUpdater implementation based on an extractor-updater pair that could also be used as a
    ValueManipulator."""

    def __init__(self, method_or_extractor: str | ValueExtractor, updater: Optional[ValueUpdater] = None) -> None:
        """
        Constructs a new `CompositeUpdater`.

        :param method_or_extractor: The ValueExtractor part.
        :param updater: The ValueUpdater part.
        """
        super().__init__()
        if updater is not None:  # Two arg constructor
            self.extractor = cast(ValueExtractor, method_or_extractor)
            self.updater = updater
        else:  # One arg with method name
            last = str(method_or_extractor).rfind(".")
            if last == -1:
                self.extractor = IdentityExtractor()
            else:
                self.extractor = ChainedExtractor(str(method_or_extractor)[0:last])
            self.updater = UniversalUpdater(str(method_or_extractor)[last + 1 :])

    def get_extractor(self) -> ValueExtractor:
        return self.extractor

    def get_updator(self) -> ValueUpdater:
        return self.updater


@proxy("extractor.UniversalUpdater")
class UniversalUpdater(ValueUpdater):
    """Universal ValueUpdater implementation.

    Either a property-based and method-based {@link ValueUpdater} based on whether constructor parameter *name*
    is evaluated to be a property or method."""

    def __init__(self, method: str) -> None:
        """
        Construct a UniversalUpdater for the provided name.

        If method ends in a '()', then the name is a method name. This implementation assumes that a target's class
        will have one and only one method with the specified name and this method will have exactly one parameter; if
        the method is a property name, there should be a corresponding JavaBean property modifier method or it will
        be used as a key in a Map.

        :param method: a method or property name
        """
        super().__init__()
        self.name = method
