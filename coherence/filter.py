# Copyright (c) 2022 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

from abc import ABC
from typing import Any, Generic, TypeVar

from .extractor import UniversalExtractor, ValueExtractor
from .serialization import proxy

K = TypeVar("K", covariant=True)
V = TypeVar("V", covariant=True)
R = TypeVar("R", covariant=True)


class Filter(ABC):
    def __init__(self) -> None:
        """
        Constructs a new `Filter`.
        """
        super().__init__()

    def and_(self, other: Filter) -> Filter:
        """
        Return a composed filter that represents a short-circuiting logical `AND` of this filter and another.  When
        evaluating the composed filter, if this filter is `false`, then the *other* filter is not evaluated.

        Any exceptions thrown during evaluation of either filter are relayed to the caller; if evaluation of this
        filter throws an exception, the *other* filter will not be evaluated.

        :param other: a filter that will be logically-`AND` ed with this filter
        :return: a composed filter that represents the short-circuiting logical
         `AND` of this filter and the *other* filter
        """
        return AndFilter(self, other)

    def or_(self, other: Filter) -> Filter:
        """
        Return a composed predicate that represents a short-circuiting logical `OR` of this predicate and another.
        When evaluating the composed predicate, if this predicate is `true`, then the *other* predicate is not
        evaluated.

        Any exceptions thrown during evaluation of either predicate are relayed to the caller; if evaluation of this
        predicate throws an exception, the *other* predicate will not be evaluated.

        :param other: a predicate that will be logically-`OR` ed with this predicate
        :return: a composed predicate that represents the short-circuiting logical
         `OR` of this predicate and the *other* predicate
        """
        return OrFilter(self, other)

    def xor_(self, other: Filter) -> Filter:
        """
        Return a composed predicate that represents a logical `XOR` of this predicate and another.

        Any exceptions thrown during evaluation of either predicate are relayed to the caller; if evaluation of this
        predicate throws an exception, the *other* predicate will not be evaluated.

        :param other: a predicate that will be logically-`XOR` ed with this predicate
        :return: a composed predicate that represents the logical `XOR` of this predicate and the *other* predicate
        """
        return XorFilter(self, other)


class Filters:
    @staticmethod
    def all(filters: list[Filter]) -> AllFilter:
        """
        Return a composite filter representing logical `AND` of all specified filters.

        :param filters: a variable number of filters
        :return: a composite filter representing logical `AND` of all specified filters
        """
        return AllFilter(filters)

    @staticmethod
    def always() -> AlwaysFilter:
        """
        Return a filter that always evaluates to true.

        :return: a filter that always evaluates to true.
        """
        return AlwaysFilter()

    @staticmethod
    def any(filters: list[Filter]) -> AnyFilter:
        """
        Return a composite filter representing logical OR of all specified filters.

        :param filters: a variable number of filters
        :return: a composite filter representing logical `OR` of all specified filters
        """
        return AnyFilter(filters)

    @staticmethod
    def between(
        extractor_or_method: ValueExtractor | str,
        from_range: int,
        to_range: int,
        include_lower_bound: bool = False,
        include_upper_bound: bool = False,
    ) -> BetweenFilter:
        """
        Return a filter that tests if the extracted value is `between` the specified values (inclusive).

        :param extractor_or_method: the {@link extractor.ValueExtractor} used by this filter or the name of the
         method to invoke via reflection
        :param from_range: the lower bound to compare the extracted value with
        :param to_range:   the upper bound to compare the extracted value with
        :param include_lower_bound: a flag indicating whether values matching the lower bound evaluate to `true`
        :param include_upper_bound: a flag indicating whether values matching the upper bound evaluate to `true`
        :return: a filter that tests if the extracted value is between the specified values
        """
        return BetweenFilter(extractor_or_method, from_range, to_range, include_lower_bound, include_upper_bound)

    @staticmethod
    def equals(extractor_or_method: ValueExtractor | str, value: Any) -> EqualsFilter:
        """
        Return a filter that tests for equality against the extracted value.

        :param extractor_or_method: the {@link extractor.ValueExtractor} used by this filter or the name of the
         method to invoke via reflection
        :param value: the value to compare the extracted value with
        :return: a filter that tests for equality
        """
        return EqualsFilter(extractor_or_method, value)


class ExtractorFilter(Filter):
    def __init__(self, extractor: ValueExtractor | str):
        """
        Construct an `ExtractorFilter` for the given {@link extractor.ValueExtractor}.

        :param extractor: the {@link extractor.ValueExtractor} to use by this :func:`coherence.filter.Filter` or a
         method name to make a {@link UniversalExtractor} for; this parameter can also be a dot-delimited sequence of
         method names which would result in an ExtractorFilter based on the {@link ChainedExtractor} that is based on
         an array of corresponding ReflectionExtractor objects
        """
        super().__init__()
        if isinstance(extractor, ValueExtractor):
            self.extractor = extractor
        elif type(extractor) == str:
            if extractor.find(".") == -1:
                self.extractor = UniversalExtractor(extractor)
            else:
                pass  # TODO for ChainedExtractor
        else:
            raise ValueError("extractor cannot be any other type")


@proxy("filter.ComparisonFilter")
class ComparisonFilter(ExtractorFilter):
    def __init__(self, extractor: ValueExtractor | str, value: V):
        """
        Construct a `ComparisonFilter`.

        :param extractor: the {@link extractor.ValueExtractor} to use by this :func:`coherence.filter.Filter` or the
         name of the method to invoke via reflection
        :param value: the object to compare the result with
        """
        super().__init__(extractor)
        self.value = value


@proxy("filter.EqualsFilter")
class EqualsFilter(ComparisonFilter):
    def __init__(self, extractor: ValueExtractor | str, value: V):
        """
        Construct an EqualsFilter for testing equality.

        :param extractor: the {@link extractor.ValueExtractor} to use by this :func:`coherence.filter.Filter` or the
         name of the method to invoke via reflection
        :param value: the object to compare the result with
        """
        super().__init__(extractor, value)

    @classmethod
    def create(cls, extractor: ValueExtractor | str, value: Any) -> EqualsFilter:
        """
        Class method to construct an EqualsFilter

        :param extractor: the {@link extractor.ValueExtractor} to use by this :func:`coherence.filter.Filter` or the
         name of the method to invoke via reflection
        :param value: the object to compare the result with
        :return: an instance of EqualsFilter
        """
        return cls(extractor, value)


@proxy("filter.NotEqualsFilter")
class NotEqualsFilter(ComparisonFilter):
    def __init__(self, extractor: ValueExtractor | str, value: V):
        """
        Construct a `NotEqualsFilter` for testing inequality.

        :param extractor: the {@link extractor.ValueExtractor} to use by this :func:`coherence.filter.Filter` or the
         name of the method to invoke via reflection
        :param value: the object to compare the result with
        """
        super().__init__(extractor, value)

    @classmethod
    def create(cls, extractor: ValueExtractor | str, value: Any) -> NotEqualsFilter:
        """
        Class method to construct a NotEqualsFilter instance

        :param extractor: the {@link extractor.ValueExtractor} to use by this :func:`coherence.filter.Filter` or the
         name of the method to invoke via reflection
        :param value: the object to compare the result with
        :return: an instance of :func:`coherence.filter.NotEqualsFilter`
        """
        return cls(extractor, value)


@proxy("filter.GreaterFilter")
class GreaterFilter(ComparisonFilter):
    def __init__(self, extractor: ValueExtractor | str, value: V):
        """
        Construct a `GreaterFilter` for testing `Greater` condition.

        :param extractor: the {@link extractor.ValueExtractor} to use by this :func:`coherence.filter.Filter` or the
         name of the method to invoke via reflection
        :param value: the object to compare the result with
        """
        super().__init__(extractor, value)

    @classmethod
    def create(cls, extractor: ValueExtractor | str, value: Any) -> GreaterFilter:
        """
        Class method to construct a `GreaterFilter` instance

        :param extractor: the {@link extractor.ValueExtractor} to use by this :func:`coherence.filter.Filter` or the
         name of the method to invoke via reflection
        :param value: the object to compare the result with
        :return: an instance of :func:`coherence.filter.GreaterFilter`
        """
        return cls(extractor, value)


@proxy("filter.GreaterEqualsFilter")
class GreaterEqualsFilter(ComparisonFilter):
    def __init__(self, extractor: ValueExtractor | str, value: V):
        """
        Construct a `GreaterEqualFilter` for testing `Greater or Equal` condition.

        :param extractor: the {@link extractor.ValueExtractor} to use by this :func:`coherence.filter.Filter` or the
         name of the method to invoke via reflection
        :param value: the object to compare the result with
        """
        super().__init__(extractor, value)

    @classmethod
    def create(cls, extractor: ValueExtractor | str, value: Any) -> GreaterEqualsFilter:
        """
        Class method to construct a `GreaterEqualsFilter` instance

        :param extractor: the {@link extractor.ValueExtractor} to use by this :func:`coherence.filter.Filter` or the
         name of the method to invoke via reflection
        :param value: the object to compare the result with
        :return: an instance of :func:`coherence.filter.GreaterEqualsFilter`
        """
        return cls(extractor, value)


@proxy("filter.LessFilter")
class LessFilter(ComparisonFilter):
    def __init__(self, extractor: ValueExtractor | str, value: V):
        """
        Construct a LessFilter for testing `Less` condition.

        :param extractor: the {@link extractor.ValueExtractor} to use by this :func:`coherence.filter.Filter` or the
         name of the method to invoke via reflection
        :param value: the object to compare the result with
        """
        super().__init__(extractor, value)

    @classmethod
    def create(cls, extractor: ValueExtractor | str, value: Any) -> LessFilter:
        """
        Class method to construct a `LessFilter` instance

        :param extractor: the {@link extractor.ValueExtractor} to use by this :func:`coherence.filter.Filter` or the
         name of the method to invoke via reflection
        :param value: the object to compare the result with
        :return: an instance of :func:`coherence.filter.LessFilter`
        """
        return cls(extractor, value)


@proxy("filter.LessEqualsFilter")
class LessEqualsFilter(ComparisonFilter):
    def __init__(self, extractor: ValueExtractor | str, value: V):
        """
        Construct a `LessEqualsFilter` for testing `Less or Equals` condition.

        :param extractor: the {@link extractor.ValueExtractor} to use by this :func:`coherence.filter.Filter` or the
         name of the method to invoke via reflection
        :param value: the object to compare the result with
        """
        super().__init__(extractor, value)

    @classmethod
    def create(cls, extractor: ValueExtractor | str, value: Any) -> LessEqualsFilter:
        """
        Class method to construct a `LessEqualsFilter` instance

        :param extractor: the {@link extractor.ValueExtractor} to use by this :func:`coherence.filter.Filter` or the
         name of the method to invoke via reflection
        :param value: the object to compare the result with
        :return: an instance of :func:`coherence.filter.LessEqualsFilter`
        """
        return cls(extractor, value)


@proxy("filter.NotFilter")
class NotFilter(Filter):
    def __init__(self, filter: Filter):
        """
        Construct a `NotFilter` which negates the results of another filter.

        :param filter: The Filter whose results are negated by this filter.
        """
        super().__init__()
        self.filter = filter

    @classmethod
    def create(cls, filter: Filter) -> NotFilter:
        """
        Class method to construct a `NotFilter` instance

        :param filter: The Filter whose results are negated by this filter.
        :return: an instance of :func:`coherence.filter.NotFilter`
        """
        return cls(filter)


@proxy("filter.IsNullFilter")
class IsNoneFilter(EqualsFilter):
    def __init__(self, extractor_or_method: ValueExtractor | str):
        """
        Construct a `IsNoneFilter` for testing equality to `None`.

        :param extractor_or_method: the {@link extractor.ValueExtractor} to use by this
         :func:`coherence.filter.Filter` or the name of the method to invoke via reflection
        """
        super().__init__(extractor_or_method, None)

    @classmethod
    def create(cls, extractor: ValueExtractor | str, value: Any = None) -> IsNoneFilter:
        """
        Class method to construct a `IsNoneFilter` instance

        :param extractor: the {@link extractor.ValueExtractor} to use by this :func:`coherence.filter.Filter` or the
         name of the method to invoke via reflection
        :return: an instance of :func:`coherence.filter.IsNoneFilter`
        """
        return cls(extractor)


@proxy("filter.IsNotNullFilter")
class IsNotNoneFilter(NotEqualsFilter):
    def __init__(self, extractor_or_method: ValueExtractor | str):
        """
        Construct a `IsNotNoneFilter` for testing inequality to `None`.

        :param extractor_or_method: the {@link extractor.ValueExtractor} to use by this
         :func:`coherence.filter.Filter` or the name of the method to invoke via reflection
        """
        super().__init__(extractor_or_method, None)

    @classmethod
    def create(cls, extractor: ValueExtractor | str, value: Any = None) -> IsNotNoneFilter:
        """
        Class method to construct a `IsNotNoneFilter` instance

        :param extractor: the {@link extractor.ValueExtractor} to use by this :func:`coherence.filter.Filter` or the
         name of the method to invoke via reflection
        :return: an instance of :func:`coherence.filter.IsNotNoneFilter`
        """
        return cls(extractor)


@proxy("filter.AlwaysFilter")
class AlwaysFilter(Filter):
    _instance: Any = None

    def __init__(self) -> None:
        """
        Construct a Filter which always evaluates to `true`.
        """
        super().__init__()
        if AlwaysFilter._instance is None:
            AlwaysFilter._instance = self

    @classmethod
    def get_instance(cls) -> Any:
        """
        Return an instance of :func:`coherence.filter.AlwaysFilter`

        :return: an instance of :func:`coherence.filter.AlwaysFilter`
        """
        if AlwaysFilter._instance is None:
            AlwaysFilter()
        return AlwaysFilter._instance


@proxy("filter.NeverFilter")
class NeverFilter(Filter):
    _instance: Any = None

    def __init__(self) -> None:
        """
        Construct a Filter which always evaluates to `false`.
        """
        super().__init__()
        if NeverFilter._instance is None:
            NeverFilter._instance = self

    @classmethod
    def get_instance(cls) -> Any:
        """
        Return an instance of :func:`coherence.filter.NeverFilter`

        :return: an instance of :func:`coherence.filter.NeverFilter`
        """
        if NeverFilter._instance is None:
            NeverFilter()
        return NeverFilter._instance


class ArrayFilter(Filter):
    def __init__(self, filters: list[Filter]):
        """
        Construct a logical filter that applies a binary operator to a filter array. The result is defined as:

          `filter[0] <op> filter[1] ... <op> filter[n]`

        :param filters: the filter array
        """
        super().__init__()
        self.filters = filters


@proxy("filter.AllFilter")
class AllFilter(ArrayFilter):
    def __init__(self, filters: list[Filter]):
        """
        Construct an `all` filter. The result is defined as:

            `filter[0] && filter[1] ... && filter[n]`

        :param filters: an array of filters
        """
        super().__init__(filters)


@proxy("filter.AnyFilter")
class AnyFilter(ArrayFilter):
    def __init__(self, filters: list[Filter]):
        """
        Construct an `any` filter. The result is defined as:

            `filter[0] || filter[1] ... || filter[n]`

        :param filters: an array of filters
        """
        super().__init__(filters)


@proxy("filter.AndFilter")
class AndFilter(AllFilter):
    def __init__(self, left: Filter, right: Filter):
        """
        Construct an `AND` filter. The result is defined as:

              `filterLeft && filterRight`

        :param left: the "left" filter
        :param right: the "right" filter
        """
        super().__init__([left, right])


@proxy("filter.OrFilter")
class OrFilter(AnyFilter):
    def __init__(self, left: Filter, right: Filter):
        """
        Construct an `OR` filter. The result is defined as:

              `filterLeft || filterRight`

        :param left: the "left" filter
        :param right: the "right" filter
        """
        super().__init__([left, right])


@proxy("filter.XorFilter")
class XorFilter(ArrayFilter):
    def __init__(self, left: Filter, right: Filter):
        """
        Construct an `XOR` filter. The result is defined as:

              `filterLeft ^ filterRight`

        :param left: the "left" filter
        :param right: the "right" filter
        """
        super().__init__([left, right])


@proxy("filter.BetweenFilter")
class BetweenFilter(AndFilter):
    def __init__(
        self,
        extractor_or_method: ValueExtractor | str,
        from_range: int,
        to_range: int,
        include_lower_bound: bool = False,
        include_upper_bound: bool = False,
    ):
        """
        Filter which compares the result of a method invocation with a value for "Between" condition.  We use the
        standard ISO/IEC 9075:1992 semantic, according to which "X between Y and Z" is equivalent to "X >= Y && X <=
        Z". In a case when either result of a method invocation or a value to compare are equal to None,
        then evaluate test yields `false`. This approach is equivalent to the way the NULL values are handled by SQL.

        Construct a `BetweenFilter` for testing "Between" condition.

        :param extractor_or_method: the {@link extractor.ValueExtractor} to use by this
         :func:`coherence.filter.Filter` or the name of the method to invoke via reflection
        :param from_range: the lower bound of the range
        :param to_range: the upper bound of the range
        :param include_lower_bound: a flag indicating whether values matching the lower bound evaluate to true
        :param include_upper_bound: a flag indicating whether values matching the upper bound evaluate to true
        """
        left = (
            GreaterEqualsFilter.create(extractor_or_method, from_range)
            if include_lower_bound
            else GreaterFilter(extractor_or_method, from_range)
        )
        right = (
            LessEqualsFilter.create(extractor_or_method, to_range)
            if include_upper_bound
            else LessFilter(extractor_or_method, to_range)
        )
        super().__init__(left, right)

    @classmethod
    def create(
        cls,
        extractor_or_method: ValueExtractor | str,
        from_range: int,
        to_range: int,
        include_lower_bound: bool = False,
        include_upper_bound: bool = False,
    ) -> BetweenFilter:
        """
        Class method to create an instance of :func:`coherence.filter.BetweenFilter`

        :param extractor_or_method: the {@link extractor.ValueExtractor} to use by this
         :func:`coherence.filter.Filter` or the name of the method to invoke via reflection
        :param from_range: the lower bound of the range
        :param to_range: the upper bound of the range
        :param include_lower_bound: a flag indicating whether values matching the lower bound evaluate to true
        :param include_upper_bound: a flag indicating whether values matching the upper bound evaluate to true
        :return: an instance of :func:`coherence.filter.BetweenFilter`
        """
        return cls(extractor_or_method, from_range, to_range, include_lower_bound, include_upper_bound)


@proxy("filter.ContainsFilter")
class ContainsFilter(ComparisonFilter):
    def __init__(self, extractor_or_method: ValueExtractor | str, value: V):
        """
        Filter which tests a collection or array value returned from a method invocation for containment of a given
        value.

        Construct a `ContainsFilter` for testing containment of the given object.

        :param extractor_or_method: the {@link extractor.ValueExtractor} to use by this
         :func:`coherence.filter.Filter` or the name of the method to invoke via reflection
        :param value: the object that a collection or array is tested to contain
        """
        super().__init__(extractor_or_method, value)

    @classmethod
    def create(cls, extractor_or_method: ValueExtractor | str, value: Any) -> ContainsFilter:
        """
        Class method to create an instance of :func:`coherence.filter.ContainsFilter`

        :param extractor_or_method: the {@link extractor.ValueExtractor} to use by this
         :func:`coherence.filter.Filter` or the name of the method to invoke via reflection
        :param value: the object that a collection or array is tested to contain
        :return: an instance of :func:`coherence.filter.ContainsFilter`
        """
        return cls(extractor_or_method, value)


@proxy("filter.ContainsAnyFilter")
class ContainsAnyFilter(ComparisonFilter):
    def __init__(self, extractor_or_method: ValueExtractor | str, set_values: V):
        """
        Filter which tests Collection or Object array value returned from a method invocation for containment of any
        value in a Set.

        Construct an `ContainsAllFilter` for testing containment of any value within the given Set.

        :param extractor_or_method: the {@link extractor.ValueExtractor} to use by this
         :func:`coherence.filter.Filter` or the name of the method to invoke via reflection
        :param set_values: the Set of values that a Collection or array is tested to contain
        """
        super().__init__(extractor_or_method, set_values)

    @classmethod
    def create(cls, extractor_or_method: ValueExtractor | str, set_values: Any) -> ContainsAnyFilter:
        """
        Class method to create an instance of :func:`coherence.filter.ContainsAnyFilter`

        :param extractor_or_method: the {@link extractor.ValueExtractor} to use by this
         :func:`coherence.filter.Filter` or the name of the method to invoke via reflection
        :param set_values: the Set of values that a Collection or array is tested to contain
        :return: an instance of :func:`coherence.filter.ContainsAnyFilter`
        """
        return cls(extractor_or_method, set_values)


@proxy("filter.ContainsAllFilter")
class ContainsAllFilter(ComparisonFilter):
    def __init__(self, extractor_or_method: ValueExtractor | str, set_values: V):
        """
        Filter which tests a Collection or array value returned from a method invocation for containment of all
        values in a Set.

        Construct an `ContainsAllFilter` for testing containment of the given Set of values.

        :param extractor_or_method: the {@link extractor.ValueExtractor} to use by this
         :func:`coherence.filter.Filter` or the name of the method to invoke via reflection
        :param set_values: the Set of values that a Collection or array is tested to contain
        """
        super().__init__(extractor_or_method, set_values)

    @classmethod
    def create(cls, extractor_or_method: ValueExtractor | str, set_values: Any) -> ContainsAllFilter:
        """
        Class method to create an instance of :func:`coherence.filter.ContainsAllFilter`

        :param extractor_or_method: the {@link extractor.ValueExtractor} to use by this
         :func:`coherence.filter.Filter` or the name of the method to invoke via reflection
        :param set_values: the Set of values that a Collection or array is tested to contain
        :return: an instance of :func:`coherence.filter.ContainsAllFilter`
        """
        return cls(extractor_or_method, set_values)


@proxy("filter.InFilter")
class InFilter(ComparisonFilter):
    def __init__(self, extractor_or_method: ValueExtractor | str, set_values: V):
        """
        Filter which checks whether the result of a method invocation belongs to a predefined set of values.

        Construct an `InFilter` for testing `In` condition.

        :param extractor_or_method: the {@link extractor.ValueExtractor} to use by this
         :func:`coherence.filter.Filter` or the name of the method to invoke via reflection
        :param set_values: the Set of values that a Collection or array is tested to contain
        """
        super().__init__(extractor_or_method, set_values)

    @classmethod
    def create(cls, extractor_or_method: ValueExtractor | str, set_values: Any) -> InFilter:
        """
        Class method to create an instance of :func:`coherence.filter.InFilter`

        :param extractor_or_method: the {@link extractor.ValueExtractor} to use by this
         :func:`coherence.filter.Filter` or the name of the method to invoke via reflection
        :param set_values: the Set of values that a Collection or array is tested to contain
        :return: an instance of :func:`coherence.filter.InFilter`
        """
        return cls(extractor_or_method, set_values)


@proxy("filter.LikeFilter")
class LikeFilter(ComparisonFilter):
    def __init__(
        self, extractor_or_method: ValueExtractor | str, pattern: str, escape_char: str = "0", ignore_case: bool = False
    ):
        """
        Filter which compares the result of a method invocation with a value for pattern match. A pattern can include
        regular characters and wildcard characters `_` and `%`.

        During pattern matching, regular characters must exactly match the characters in an evaluated string.
        Wildcard character `_` (underscore) can be matched with any single character, and wildcard character `%` can
        be matched with any string fragment of zero or more characters.

        Construct a `LikeFilter` for pattern match.

        :param extractor_or_method: the {@link extractor.ValueExtractor} to use by this
         :func:`coherence.filter.Filter` or the name of the method to invoke via reflection
        :param pattern: the string pattern to compare the result with
        :param escape_char: the escape character for escaping `%` and `_`
        :param ignore_case: `true` to be case-insensitive
        """
        super().__init__(extractor_or_method, pattern)
        self.escapeChar = escape_char
        self.ignoreCase = ignore_case

    @classmethod
    def create(
        cls, extractor_or_method: ValueExtractor | str, pattern: str, escape_char: str = "0", ignore_case: bool = False
    ) -> LikeFilter:
        """
        Class method to create an instance of :func:`coherence.filter.LikeFilter`

        :param extractor_or_method: the {@link extractor.ValueExtractor} to use by this
         :func:`coherence.filter.Filter` or the name of the method to invoke via reflection
        :param pattern: the string pattern to compare the result with
        :param escape_char: the escape character for escaping `%` and `_`
        :param ignore_case: `true` to be case-insensitive
        :return: an instance of :func:`coherence.filter.LikeFilter`
        """
        return cls(extractor_or_method, pattern, escape_char, ignore_case)


@proxy("filter.RegexFilter")
class RegexFilter(ComparisonFilter):
    def __init__(self, extractor_or_method: ValueExtractor | str, regex: str):
        """
        Filter which uses the regular expression pattern match defined by the Java's `String.matches` contract. This
        implementation is not index aware and will not take advantage of existing indexes.

        :param extractor_or_method: the {@link extractor.ValueExtractor} to use by this
         :func:`coherence.filter.Filter` or the name of the method to invoke via reflection
        :param regex: the regular expression to match the result with
        """
        super().__init__(extractor_or_method, regex)

    @classmethod
    def create(cls, extractor_or_method: ValueExtractor | str, regex: str) -> RegexFilter:
        """
        Class method to create an instance of :func:`coherence.filter.RegexFilter`

        :param extractor_or_method: the {@link extractor.ValueExtractor} to use by this
         :func:`coherence.filter.Filter` or the name of the method to invoke via reflection
        :param regex: the regular expression to match the result with
        :return: an instance of :func:`coherence.filter.RegexFilter`
        """
        return cls(extractor_or_method, regex)


@proxy("filter.PredicateFilter")
class PredicateFilter(ExtractorFilter):
    def __init__(self, extractor_or_method: ValueExtractor | str, predicate: Any):
        """
        A predicate based :func:`coherence.filter.ExtractorFilter`

        Constructs a :func:`coherence.filter.PredicateFilter`

        :param extractor_or_method: the {@link extractor.ValueExtractor} to use by this
         :func:`coherence.filter.Filter` or the name of the method to invoke via reflection
        :param predicate: predicate for testing the value. The object must have an '@class' attribute.
        """
        super().__init__(extractor_or_method)
        self.predicate = predicate


@proxy("filter.PresentFilter")
class PresentFilter(Filter):
    _instance: Any = None

    def __init__(self) -> None:
        """
        Filter which returns true for entries that currently exist in a map.

        This Filter is intended to be used solely in combination with a
        :func:`coherence.processor.ConditionalProcessor` and is unnecessary for standard
        :func:`coherence.client.NamedMap` operations.
        """
        super().__init__()
        if PresentFilter._instance is None:
            PresentFilter._instance = self

    @classmethod
    def get_instance(cls) -> Any:
        """
        Returns an instance of :func:`coherence.filter.PresentFilter`

        :return: an instance of :func:`coherence.filter.PresentFilter`
        """
        if PresentFilter._instance is None:
            PresentFilter()
        return PresentFilter._instance


@proxy("filter.MapEventFilter")
class MapEventFilter(Filter, Generic[K, V]):
    INSERTED: int = 0x0001
    """This value indicates that insert events should be evaluated.
       The event will be fired if there is no filter specified or the
       filter evaluates to true for a new value."""

    UPDATED: int = 0x0002
    """This value indicates that update events should be evaluated.
       The event will be fired if there is no filter specified or the
       filter evaluates to true when applied to either old or new value."""

    DELETED: int = 0x0004
    """This value indicates that delete events should be evaluated.
       The event will be fired if there is no filter specified or the
       filter evaluates to true for an old value."""

    ALL: int = INSERTED | UPDATED | DELETED
    """This value indicates that all events should be evaluated."""

    def __init__(self, mask: int, filter: Filter) -> None:
        """
        Filter which evaluates the content of a MapEvent object according to the specified criteria.  This filter is
        intended to be used by various map listeners that are interested in particular subsets of MapEvent
        notifications emitted by the map.

        Construct a MapEventFilter that evaluates MapEvent objects based on the specified combination of event types.

        :param mask: combination of any of the E_* values or the filter passed previously to a keySet() query method
        :param filter: the filter used for evaluating event values
        """
        super().__init__()
        self.mask: int = mask
        self.filter: Filter = filter

    @classmethod
    def from_mask(cls, mask: int) -> MapEventFilter[K, V]:
        """TODO DOCS"""

        return cls(mask, AlwaysFilter())

    @classmethod
    def from_filter(cls, filter: Filter) -> MapEventFilter[K, V]:
        """TODO DOCS"""

        return cls(cls.ALL, filter)
