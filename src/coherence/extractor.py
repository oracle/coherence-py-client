# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, Optional, Sequence, TypeVar, Union, cast

from typing_extensions import TypeAlias

from .serialization import proxy

E = TypeVar("E")
K = TypeVar("K")
V = TypeVar("V")
R = TypeVar("R")
T = TypeVar("T")


class ValueExtractor(ABC, Generic[T, E]):
    def __init__(self) -> None:
        """
        ValueExtractor is used to both extract values (for example, for sorting or filtering) from an object,
        and to provide an identity for that extraction.

        Construct a ValueExtractor.
        """
        super().__init__()

    def compose(self, before: ValueExtractor[T, E]) -> ValueExtractor[T, E]:
        """
        Returns a composed extractor that first applies the *before* extractor to its input, and then applies this
        extractor to the result. If evaluation of either extractor throws an exception, it is relayed to the caller
        of the composed extractor.

        :param before: the extractor to apply before this extractor is applied
        :return: a composed extractor that first applies the *before* extractor and then applies this extractor
        """
        if before is None:
            raise ValueError("before cannot be null")
        if type(before) == ValueExtractor:  # noqa: E721
            return before.and_then(self)
        else:
            return ChainedExtractor([before, self])

    def and_then(self, after: ValueExtractor[T, E]) -> ValueExtractor[T, E]:
        """
        Returns a composed extractor that first applies this extractor to its input, and then applies the *after*
        extractor to the result. If evaluation of either extractor throws an exception, it is relayed to the caller
        of the composed extractor.

        :param after: the extractor to apply after this extractor is applied
        :return: a composed extractor that first applies this extractor and then applies the *after* extractor
        """
        if after is None:
            raise ValueError("after cannot be null")
        if type(after) == ChainedExtractor:  # noqa: E721
            return ChainedExtractor([self, after])
        else:
            return after.compose(self)

    @classmethod
    def extract(cls, from_field_or_method: str, params: Optional[list[Any]] = None) -> ValueExtractor[T, E]:
        """
        Returns an extractor that extracts the value of the specified field.

        :param from_field_or_method: the name of the field or method to extract the value from.
        :param params: the parameters to pass to the method.
        :return: an instance of :class:`coherence.extractor.UniversalExtractor`
        """
        return UniversalExtractor(from_field_or_method, params)


@proxy("extractor.UniversalExtractor")
class UniversalExtractor(ValueExtractor[T, Any]):
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
        :param params: the parameter array. Must be `null` or `zero length` for a property based extractor.
        """
        super().__init__()
        self.name: str = name
        self.params = params

    @classmethod
    def create(cls, name: str, params: Optional[list[Any]] = None) -> UniversalExtractor[T]:
        """
        Class method to create an instance of :class:`coherence.extractor.UniversalExtractor`

        :param name: A method or property name.
        :param params: the parameter array. Must be `null` or `zero length` for a property based extractor.
        :return: an instance of :class:`coherence.extractor.UniversalExtractor`
        """
        return cls(name, params)


class AbstractCompositeExtractor(ValueExtractor[T, E]):
    def __init__(self, extractors: Sequence[ValueExtractor[T, E]]) -> None:
        """
        Abstract super class for :class:`coherence.extractor.ValueExtractor` implementations that are based on an
        underlying array of :class:`coherence.extractor.ValueExtractor` objects.

        :param extractors: an array of extractors
        """
        super().__init__()
        self.extractors = extractors


@proxy("extractor.ChainedExtractor")
class ChainedExtractor(AbstractCompositeExtractor[T, Any]):
    def __init__(self, extractors_or_method: str | Sequence[ValueExtractor[T, Any]]) -> None:
        """
        Composite :class:`coherence.extractor.ValueExtractor` implementation based on an array of extractors. The
        extractors in the array are applied sequentially left-to-right, so a result of a previous extractor serves as
        a target object for a next one.

        :param extractors_or_method: an array of :class:`coherence.extractor.ValueExtractor`, or a dot-delimited
         sequence of method names which results in a ChainedExtractor that is based on an array of corresponding
         :class:`coherence.extractor.UniversalExtractor` objects
        """
        if type(extractors_or_method) == str:  # noqa: E721
            e = list()
            names = extractors_or_method.split(".")
            for name in names:
                v: UniversalExtractor[T] = UniversalExtractor(name)
                e.append(v)
            super().__init__(e)
        else:
            super().__init__(cast(Sequence[ValueExtractor[T, Any]], extractors_or_method))


@proxy("extractor.MultiExtractor")
class MultiExtractor(AbstractCompositeExtractor[Any, Any]):
    def __init__(self, extractors_or_method: str | Sequence[ValueExtractor[Any, Any]]) -> None:
        """
        Composite :class:`coherence.extractor.ValueExtractor` implementation based on an array of extractors. The
        extractors in the array are applied sequentially left-to-right, so a result of a previous extractor serves as
        a target object for a next one.

        :param extractors_or_method: an array of :class:`coherence.extractor.ValueExtractor`, or a dot-delimited
         sequence of method names which results in a ChainedExtractor that is based on an array of corresponding
         :class:`coherence.extractor.UniversalExtractor` objects
        """
        if type(extractors_or_method) == str:  # noqa: E721
            e = list()
            names = extractors_or_method.split(",")
            for name in names:
                v: UniversalExtractor[Any] = UniversalExtractor(name)
                e.append(v)
            super().__init__(e)
        else:
            super().__init__(cast(Sequence[ValueExtractor[Any, Any]], extractors_or_method))


@proxy("extractor.IdentityExtractor")
class IdentityExtractor(ValueExtractor[T, Any]):
    __instance = None

    def __init__(self) -> None:
        """
        A Trivial :class:`coherence.extractor.ValueExtractor` implementation that does not actually extract anything
        from the passed value, but returns the value itself.

        Constructs a new `IdentityExtractor` instance.
        """
        super().__init__()


class ValueUpdater(ABC, Generic[T, R]):
    def __init__(self) -> None:
        """
        ValueUpdater is used to update an object's state.

        Constructs a new `ValueUpdater`.
        """
        super().__init__()


class ValueManipulator(Generic[T, R]):
    """ValueManipulator represents a composition of :class:`coherence.extractor.ValueExtractor` and
    :class:`coherence.extractor.ValueUpdater` implementations."""

    @abstractmethod
    def get_extractor(self) -> ValueExtractor[T, R]:
        """
        Retrieve the underlying ValueExtractor reference.

        :rtype: the ValueExtractor
        """

    @abstractmethod
    def get_updator(self) -> ValueUpdater[T, R]:
        """
        Retrieve the underlying ValueUpdater reference.

        :rtype: the ValueUpdater
        """


@proxy("extractor.CompositeUpdater")
class CompositeUpdater(ValueManipulator[T, R], ValueUpdater[T, R]):
    """A ValueUpdater implementation based on an extractor-updater pair that could also be used as a
    ValueManipulator."""

    def __init__(
        self, method_or_extractor: ExtractorExpression[T, R], updater: Optional[ValueUpdater[T, R]] = None
    ) -> None:
        """
        Constructs a new `CompositeUpdater`.

        :param method_or_extractor: The ValueExtractor part.
        :param updater: The ValueUpdater part.
        """
        super().__init__()
        if updater is not None:  # Two arg constructor
            self.extractor = cast(ValueExtractor[T, R], method_or_extractor)
            self.updater = updater
        else:  # One arg with method name
            last = str(method_or_extractor).rfind(".")
            if last == -1:
                self.extractor = IdentityExtractor()
            else:
                self.extractor = ChainedExtractor(str(method_or_extractor)[0:last])
            self.updater = UniversalUpdater(str(method_or_extractor)[last + 1 :])

    def get_extractor(self) -> ValueExtractor[T, R]:
        return self.extractor

    def get_updator(self) -> ValueUpdater[T, R]:
        return self.updater


@proxy("extractor.UniversalUpdater")
class UniversalUpdater(ValueUpdater[V, R]):
    """Universal ValueUpdater implementation.

    Either a property-based and method-based {@link ValueUpdater} based on whether constructor parameter *name*
    is evaluated to be a property or method."""

    def __init__(self, method: str) -> None:
        """
        Construct a UniversalUpdater for the provided name.

        If method ends in a '()', then the name is a method name. This implementation assumes that a target's class
        will have one and only one method with the specified name and this method will have exactly one parameter; if
        the method is a property name, there should be a corresponding JavaBean property modifier method, or it will
        be used as a key in a Map.

        :param method: a method or property name
        """
        super().__init__()
        self.name = method


class Extractors:
    """
    A Utility class for creating extractors.
    """

    @classmethod
    def extract(cls, expression: str, params: Optional[list[Any]] = None) -> ValueExtractor[T, E]:
        """
        If providing only an expression, the following rules apply:
          - if the expression contains multiple values separated by a period,
            the expression will be treated as a chained expression.  E.g.,
            the expression 'a.b.c' would be treated as extract the 'a'
            property, from that result, extract the 'b' property, and finally
            from that result, extract the 'c' property.
          - if the expression contains multiple values separated by a comma,
            the expression will be treated as a multi expression.  E.g.,
            the expression 'a,b,c' would be treated as extract the 'a', 'b',
            and 'c' properties from the same object.
          - for either case, the params argument is ignored.

        It is also possible to invoke, and pass arguments to, arbitrary methods.
        For example, if the target object of the extraction is a String, it's
        possible to call the length() function by passing an expression of
        "length()".  If the target method accepts arguments, provide a list
        of one or more arguments to be passed.

        :param expression: the extractor expression
        :param params:  the params to pass to the method invocation
        :return: a ValueExtractor based on the provided inputs
        """
        if expression is None:
            raise ValueError("An expression must be provided")

        if params is None or len(params) == 0:
            if "." in expression:
                return ChainedExtractor(expression)
            elif "," in expression:
                return MultiExtractor(expression)
            else:
                return UniversalExtractor(expression)

        expr: str = expression
        if not expr.endswith("()"):
            expr = expr + "()"

        return UniversalExtractor(expr, params)

    @classmethod
    def identity(cls) -> IdentityExtractor[Any]:
        """
        Returns an extractor that does not actually extract anything
        from the passed value, but returns the value itself.

        :return: an extractor that does not actually extract anything
          from the passed value, but returns the value itself
        """
        return IdentityExtractor()


ExtractorExpression: TypeAlias = Union[ValueExtractor[T, E], str]
ManipulatorExpression: TypeAlias = Union[ValueManipulator[T, E], str]
UpdaterExpression: TypeAlias = Union[ValueUpdater[T, R], str]
