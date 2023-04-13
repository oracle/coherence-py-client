# Copyright (c) 2022, 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

from abc import ABC
from decimal import Decimal
from enum import Enum, IntEnum
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeAlias, TypeVar

from .comparator import Comparator, InverseComparator, SafeComparator
from .extractor import ExtractorExpression, IdentityExtractor, ValueExtractor, extract
from .filter import Filter
from .serialization import proxy

E = TypeVar("E")
G = TypeVar("G")
K = TypeVar("K")
R = TypeVar("R")
T = TypeVar("T")
V = TypeVar("V")

ReducerResult: TypeAlias = Dict[K, Any | List[Any]]
AggregationResult: TypeAlias = List[Tuple[G, T]]


class EntryAggregator(ABC, Generic[R]):
    """An EntryAggregator represents processing that can be directed to occur against some subset of the entries in
    n cache, resulting in an aggregated result. Common examples of aggregation include functions such as min(),
    max() and avg(). However, the concept of aggregation applies to any process that needs to evaluate a group of
    entries to come up with a single answer."""

    def __init__(self, extractor_or_property: Optional[ExtractorExpression[T, E]] = None):
        """
        Construct an AbstractAggregator that will aggregate values extracted from the cache entries.

        :param extractor_or_property: the extractor that provides values to aggregate or the name of the method that
            could be invoked via Java reflection and that returns values to aggregate; this parameter can also be a
            dot-delimited sequence of method names which would result in an aggregator based on the
            :func:`coherence.extractor.ChainedExtractor` that is based on an array of corresponding
            :func:`coherence.extractor.UniversalExtractor` objects; must not be `None`
        """
        super().__init__()
        if extractor_or_property is not None:
            if isinstance(extractor_or_property, ValueExtractor):
                self.extractor = extractor_or_property
            else:
                self.extractor = extract(extractor_or_property)

    def and_then(self, aggregator: EntryAggregator[R]) -> EntryAggregator[List[R]]:
        """
        Returns a :func:`coherence.aggregator.CompositeAggregator` comprised of this and the provided aggregator.

        :param aggregator: the next aggregator
        :return: a :func:`coherence.aggregator.CompositeAggregator` comprised of this and the provided aggregator
        """
        return CompositeAggregator[R]([self, aggregator])


class AbstractComparableAggregator(EntryAggregator[R]):
    """Abstract aggregator that processes values extracted from a set of entries in a Map, with knowledge of how to
    compare those values. There are two-way to use the AbstractComparableAggregator:

    * All the extracted objects must implement the Java Comparable interface, or

    * The AbstractComparableAggregator has to be provided with a :func:`coherence.comparator.Comparator` object.
      This :func:`coherence.comparator.Comparator` must exist on the server in order to be usable.

    If there are no entries to aggregate, the returned result will be `None`."""

    def __init__(self, extractor_or_property: ExtractorExpression[T, E]):
        """
        Construct an AbstractComparableAggregator that will aggregate Java-Comparable values extracted from the cache
        entries.

        :param extractor_or_property: the extractor that provides values to aggregate or the name of the method that
            could be invoked via Java reflection and that returns values to aggregate; this parameter can also be a
            dot-delimited sequence of method names which would result in an aggregator based on the
            :func:`coherence.extractor.ChainedExtractor` that is based on an array of corresponding
            :func:`coherence.extractor.UniversalExtractor` objects; must not be `None`
        """
        super().__init__(extractor_or_property)


class AbstractDoubleAggregator(EntryAggregator[Decimal]):
    """Abstract aggregator that processes numeric values extracted from a set of entries in a Map. All the extracted
    Number objects will be treated as Java `double` values and the result of the aggregator is a Double. If
    the set of entries is empty, a `None` result is returned."""

    def __init__(self, extractor_or_property: ExtractorExpression[T, E]):
        """
        Construct an AbstractDoubleAggregator that will aggregate numeric values extracted from the cache entries.

        :param extractor_or_property: the extractor that provides values to aggregate or the name of the method that
            could be invoked via Java reflection and that returns values to aggregate; this parameter can also be a
            dot-delimited sequence of method names which would result in an aggregator based on the
            :func:`coherence.extractor.ChainedExtractor` that is based on an array of corresponding
            :func:`coherence.extractor.UniversalExtractor` objects; must not be `None`
        """
        super().__init__(extractor_or_property)


@proxy("aggregator.CompositeAggregator")
class CompositeAggregator(EntryAggregator[List[R]]):
    """`CompositeAggregator` provides an ability to execute a collection of aggregators against the same subset of
    the entries in a Map, resulting in a list of corresponding aggregation results. The size of the returned list
    will always be equal to the length of the aggregators list."""

    def __init__(self, aggregators: list[EntryAggregator[R]]):
        """
        Construct a CompositeAggregator based on a specified :func:`coherence.aggregator.EntryAggregator` list.

        :param aggregators: an array of :func:`coherence.aggregator.EntryAggregator` objects; may not be `None`
        """
        super().__init__()
        if aggregators is not None:
            self.aggregators = aggregators
        else:
            raise ValueError("no aggregators provided")


@proxy("aggregator.ComparableMax")
class MaxAggregator(AbstractComparableAggregator[R]):
    """Calculates a maximum of numeric values extracted from a set of entries in a Map in a form of a numerical
    value. All the extracted objects will be treated as numerical values. If the set of entries is empty,
    a `None` result is returned."""

    def __init__(self, extractor_or_property: ExtractorExpression[T, E]):
        """
        Constructs a new `MaxAggregator`.

        :param extractor_or_property: the extractor that provides values to aggregate or the name of the method that
            could be invoked via Java reflection and that returns values to aggregate; this parameter can also be a
            dot-delimited sequence of method names which would result in an aggregator based on the
            :func:`coherence.extractor.ChainedExtractor` that is based on an array of corresponding
            :func:`coherence.extractor.UniversalExtractor` objects; must not be `None`
        """
        super().__init__(extractor_or_property)


@proxy("aggregator.ComparableMin")
class MinAggregator(AbstractComparableAggregator[R]):
    """Calculates a minimum of numeric values extracted from a set of entries in a Map in a form of a numerical
    value. All the extracted objects will be treated as numerical values. If the set of entries is empty,
    a `None` result is returned."""

    def __init__(self, extractor_or_property: ExtractorExpression[T, E]):
        """
        Constructs a new `MinAggregator`.

        :param extractor_or_property: the extractor that provides values to aggregate or the name of the method that
            could be invoked via Java reflection and that returns values to aggregate; this parameter can also be a
            dot-delimited sequence of method names which would result in an aggregator based on the
            :func:`coherence.extractor.ChainedExtractor` that is based on an array of corresponding
            :func:`coherence.extractor.UniversalExtractor` objects; must not be `None`
        """
        super().__init__(extractor_or_property)


@proxy("aggregator.BigDecimalSum")
class SumAggregator(AbstractDoubleAggregator):
    """Calculates a sum for values of any numeric type extracted from a set of entries in a Map in a form of a
    numeric value.

    If the set of entries is empty, a 'None' result is returned."""

    def __init__(self, extractor_or_property: ExtractorExpression[T, E]):
        """
        Constructs a new `SumAggregator`.

        :param extractor_or_property: the extractor that provides values to aggregate or the name of the method that
            could be invoked via Java reflection and that returns values to aggregate; this parameter can also be a
            dot-delimited sequence of method names which would result in an aggregator based on the
            :func:`coherence.extractor.ChainedExtractor` that is based on an array of corresponding
            :func:`coherence.extractor.UniversalExtractor` objects; must not be `None`
        """
        super().__init__(extractor_or_property)


@proxy("aggregator.BigDecimalAverage")
class AverageAggregator(AbstractDoubleAggregator):
    """Calculates an average for values of any numeric type extracted from a set of entries in a Map in a form of a
    numerical value. All the extracted objects will be treated as numerical values. If the set of entries is empty,
    a `None` result is returned."""

    def __init__(self, extractor_or_property: ExtractorExpression[T, E]):
        """
        Construct an `AverageAggregator` that will sum numeric values extracted from the cache entries.

        :param extractor_or_property: the extractor that provides values to aggregate or the name of the method that
            could be invoked via Java reflection and that returns values to aggregate; this parameter can also be a
            dot-delimited sequence of method names which would result in an aggregator based on the
            :func:`coherence.extractor.ChainedExtractor` that is based on an array of corresponding
            :func:`coherence.extractor.UniversalExtractor` objects; must not be `None`
        """
        super().__init__(extractor_or_property)


@proxy("aggregator.Count")
class CountAggregator(EntryAggregator[int]):
    """Calculates a number of values in an entry set."""

    def __init__(self) -> None:
        """
        Constructs a new `CountAggregator`.
        """
        super().__init__()


@proxy("aggregator.DistinctValues")
class DistinctValuesAggregator(EntryAggregator[R]):
    """Return the set of unique values extracted from a set of entries in a Map. If the set of entries is empty,
    an empty array is returned.

    This aggregator could be used in combination with :func:`coherence.extractor.UniversalExtractor` allowing to
    collect all unique combinations (tuples) of a given set of attributes.

    The DistinctValues aggregator covers a simple case of a more generic aggregation pattern implemented by the
    `GroupAggregator`, which in addition to collecting all distinct values or tuples, runs an aggregation against
    each distinct entry set (group)."""

    def __init__(self, extractor_or_property: ExtractorExpression[T, E]):
        """
        Construct a DistinctValuesAggregator that will aggregate numeric values extracted from the cache entries.

        :param extractor_or_property: the extractor that provides values to aggregate or the name of the method that
            could be invoked via Java reflection and that returns values to aggregate; this parameter can also be a
            dot-delimited sequence of method names which would result in an aggregator based on the
            :func:`coherence.extractor.ChainedExtractor` that is based on an array of corresponding
            :func:`coherence.extractor.UniversalExtractor` objects; must not be `None`
        """
        super().__init__(extractor_or_property)


@proxy("aggregator.TopNAggregator")
class TopAggregator(Generic[E, R], EntryAggregator[List[R]]):
    """`TopAggregator` aggregates the top *N* extracted values into an array.  The extracted values must not be
    `None`, but do not need to be unique."""

    def __init__(
        self,
        number: int = 0,
        inverse: bool = False,
        extractor: ValueExtractor[Any, Any] = IdentityExtractor(),
        comparator: Optional[Comparator] = None,
        property_name: Optional[str] = None,
    ):
        """
        Constructs a new `TopAggregator`.

        :param number: the maximum number of results to include in the aggregation result.
        :param inverse: Result order.  By default, results will be ordered in descending order.
        :param extractor: The extractor to obtain the values to aggregate.  If not explicitly set, this will default
            to an :func:`coherence.extractor.IdentityExtractor`.
        :param comparator: The :func:`coherence.comparator.Comparator` to apply against the extracted values.
        :param property_name:  The property that results will be ordered by.
        """
        super().__init__()
        self.results = number
        self.inverse = inverse
        self.extractor = extractor
        self.comparator = comparator
        self.property = property_name

    def order_by(self, property_name: str) -> TopAggregator[E, R]:
        """
        Order the results based on the values of the specified property.

        :param property_name: the property name
        :return: an instance of :func:`coherence.aggregator.TopAggregator`
        """
        self.property = property_name
        self.comparator = InverseComparator(property_name) if self.inverse else SafeComparator(property_name)
        return self

    @property
    def ascending(self) -> TopAggregator[E, R]:
        """
        Sort the returned values in ascending order.

        :return: an instance of :func:`coherence.aggregator.TopAggregator`
        """
        if self.property is not None:
            self.inverse = True
            self.comparator = InverseComparator(self.property)
        return self

    @property
    def descending(self) -> TopAggregator[E, R]:
        """
        Sort the returned values in descending order.

        :return: an instance of :func:`coherence.aggregator.TopAggregator`
        """
        if self.property is not None:
            self.inverse = False
            self.comparator = SafeComparator(self.property)
        return self

    def extract(self, property_name: str) -> TopAggregator[E, R]:
        """
        The property name of the value to extract.

        :param property_name: the property name
        :return:
        """
        self.inverse = True  # TODO why is this True?
        self.extractor = ValueExtractor.extract(property_name)
        return self


@proxy("aggregator.GroupAggregator")
class GroupAggregator(EntryAggregator[R]):
    """The `GroupAggregator` provides an ability to split a subset of entries in a Map into a collection of
    non-intersecting subsets and then aggregate them separately and independently. The splitting (grouping) is
    performed using the results of the underlying :func:`coherence.extractor.UniversalExtractor` in such a way that
    two entries will belong to the same group if and only if the result of the corresponding extract call produces
    the same value or tuple (list of values). After the entries are split into the groups, the underlying aggregator
    is applied separately to each group. The result of the aggregation by the` GroupAggregator` is a Map that has
    distinct values (or tuples) as keys and results of the individual aggregation as values. Additionally,
    those results could be further reduced using an optional :func:`coherence.filter.Filter` object.

    Informally speaking, this aggregator is analogous to the SQL `group by` and `having` clauses. Note that the
    `having` Filter is applied independently on each server against the partial aggregation results; this generally
    implies that data affinity is required to ensure that all required data used to generate a given result exists
    within a single cache partition. In other words, the `group by` predicate should not span multiple partitions if
    the `having` clause is used.

    The `GroupAggregator` is somewhat similar to the DistinctValues aggregator, which returns back a list of distinct
    values (tuples) without performing any additional aggregation work."""

    def __init__(
        self,
        extractor_or_property: ExtractorExpression[T, E],
        aggregator: EntryAggregator[R],
        filter: Optional[Filter] = None,
    ):
        """
        Construct a `GroupAggregator` based on a specified :func:`coherence.extractor.ValueExtractor` and underlying
        :func:`coherence.aggregator.EntryAggregator`.

        :param extractor_or_property:  a :func:`coherence.extractor.ValueExtractor` object that is used to split
         entries into non-intersecting subsets; may not be `None`. This parameter can also be a dot-delimited sequence
         of method names which would result in an aggregator based on the :func:`coherence.extractor.ChainedExtractor`
         that is based on an array of corresponding :func:`coherence.extractor.UniversalExtractor` objects; may not be
         `NONE`

        :param aggregator: an EntryAggregator object; may not be null
        :param filter: an optional Filter object used to filter out results of individual group aggregation results
        """
        super().__init__(extractor_or_property)
        if aggregator is not None:
            self.aggregator = aggregator
        else:
            raise ValueError("no aggregator provided")
        self.filter = filter


class Timeout(IntEnum):
    NONE: int = -1
    """A special timeout value to indicate that this task or request can run indefinitely."""

    DEFAULT: int = 0
    """A special timeout value to indicate that the corresponding service's default timeout value should be used."""


class Schedule(Enum):
    STANDARD = 0
    """Scheduling value indicating that this task is to be queued and execute in a natural (based on the request
    arrival time) order."""

    FIRST = 1
    """Scheduling value indicating that this task is to be queued in front of any equal or lower scheduling priority
    tasks and executed as soon as any of the worker threads become available."""

    IMMEDIATE = 2
    """Scheduling value indicating that this task is to be immediately executed by any idle worker thread; if all
    of them are active, a new thread will be created to execute this task."""


@proxy("aggregator.PriorityAggregator")
class PriorityAggregator(Generic[R], EntryAggregator[R]):
    """A `PriorityAggregator` is used to explicitly control the scheduling priority and timeouts for execution of
    EntryAggregator-based methods.

    For example, lets assume that there is an `Orders` cache that belongs to a partitioned cache service configured
    with a *request-timeout* and *task-timeout* of 5 seconds. Also assume that we are willing to wait longer for a
    particular aggregation request that scans the entire cache. Then we could override the default timeout values by
    using the PriorityAggregator as follows::

        sumAggr = SumAggregator("cost")
        priorityAgg = PriorityAggregator(sumAggr)
        priorityAgg.executionTimeout = Timeout.NONE
        priorityAgg.requestTimeout = Timeout.NONE
        cacheOrders.aggregate(aFilter, priorityAgg)

    This is an advanced feature which should be used judiciously."""

    def __init__(
        self,
        aggregator: EntryAggregator[R],
        execution_timeout: int = Timeout.DEFAULT,
        request_timeout: int = Timeout.DEFAULT,
        scheduling_priority: Schedule = Schedule.STANDARD,
    ):
        """
        Construct a new `PriorityAggregator`.

        :param aggregator: The wrapped :func:`coherence.aggregator.EntryAggregator`.
        :param execution_timeout: The task execution timeout value.
        :param request_timeout: The request timeout value.
        :param scheduling_priority: The scheduling priority.
        """
        super().__init__()
        self.aggregator = aggregator
        self._execution_timeout = execution_timeout
        self._request_timeout = request_timeout
        self._scheduling_priority = scheduling_priority

    @property
    def scheduling_priority(self) -> Schedule:
        """
        Return the scheduling priority or, if not explicitly set, the default is
        :func:`coherence.aggregator.Schedule.STANDARD`

        :return: the scheduling priority
        """
        return self._scheduling_priority

    @scheduling_priority.setter
    def scheduling_priority(self, scheduling_priority: Schedule) -> None:
        """
        Set the scheduling priority.

        :param scheduling_priority: the scheduling priority.
        """
        self._scheduling_priority = scheduling_priority

    @property
    def execution_timeout_in_millis(self) -> int:
        """
        Return the execution timeout in milliseconds.

        :return: the execution timeout
        """
        return self._execution_timeout

    @execution_timeout_in_millis.setter
    def execution_timeout_in_millis(self, execution_timeout: int) -> None:
        """
        Set the execution timeout in milliseconds.

        :param execution_timeout: the new execution timeout in milliseconds
        """
        self._execution_timeout = execution_timeout

    @property
    def request_timeout_in_millis(self) -> int:
        """
        Return the request timeout in milliseconds.

        :return: the request timeout
        """
        return self._request_timeout

    @request_timeout_in_millis.setter
    def request_timeout_in_millis(self, request_timeout: int) -> None:
        """
        Set the request timeout in milliseconds.

        :param request_timeout: the new request timeout in milliseconds
        """
        self._request_timeout = request_timeout


@proxy("aggregator.ScriptAggregator")
class ScriptAggregator(Generic[R], EntryAggregator[R]):
    """ScriptAggregator is a :func:`coherence.aggregator.EntryAggregator` that wraps a script written in one of the
    languages supported by Graal VM."""

    def __init__(self, language: str, script_name: str, characteristics: int = 0, *args: Any):
        """
        Create a :func:`coherence.aggregator.EntryAggregator` that wraps the specified script.

        :param language: The language with which the script is written in.
        :param script_name: The name of the :func:`coherence.aggregator.EntryAggregator` that needs to be evaluated.
        :param characteristics: Present only for serialization purposes.
        :param args: The arguments to be passed to the script for evaluation
        """
        super().__init__()
        self.language = language
        self.name = script_name
        self.args = list()
        for arg in args:
            self.args.append(arg)
        self.characteristics = characteristics


class RecordType(Enum):
    EXPLAIN = 0
    """Produce an object that contains an estimated cost of the query execution."""

    TRACE = 1
    """Produce an object that contains the actual cost of the query execution."""


# TODO IMPROVE
@proxy("aggregator.QueryRecorder")
class QueryRecorder(EntryAggregator[Any]):
    """This aggregator is used to produce an object that contains an estimated or actual cost of the query execution
    for a given :func:`coherence.filter.Filter`.

    For example, the following code will print a *QueryRecord*,
    containing the estimated query cost and corresponding execution steps::

        agent  = QueryRecorder(RecordType.EXPLAIN);
        record = cache.aggregate(someFilter, agent);
        print(json.dumps(record));
    """

    EXPLAIN: str = "EXPLAIN"
    """String constant for serialization purposes."""

    TRACE: str = "TRACE"
    """String constant for serialization purposes."""

    def __init__(self, query_type: RecordType):
        """
        Construct a new `QueryRecorder`.

        :param query_type: the type for this aggregator
        """
        super().__init__()
        self.type = QueryRecorder.get_type(query_type)

    @classmethod
    def get_type(cls, query_type: RecordType) -> dict[str, str]:
        match query_type:
            case RecordType.EXPLAIN:
                return {"enum": cls.EXPLAIN}
            case RecordType.TRACE:
                return {"enum": cls.TRACE}


@proxy("aggregator.ReducerAggregator")
class ReducerAggregator(EntryAggregator[R]):
    """The `ReducerAggregator` is used to implement functionality similar to :func:`coherence.client.NamedMap.getAll(
    )` API.  Instead of returning the complete set of values, it will return a portion of value attributes based on
    the provided :func:`coherence.extractor.ValueExtractor`.

    This aggregator could be used in combination with {@link MultiExtractor} allowing one to collect tuples that are
    a subset of the attributes of each object stored in the cache."""

    def __init__(self, extractor_or_property: ExtractorExpression[T, E]):
        """
        Creates a new `ReducerAggregator`.

        :param extractor_or_property: the extractor that provides values to aggregate or the name of the method that
            could be invoked via Java reflection and that returns values to aggregate; this parameter can also be a
            dot-delimited sequence of method names which would result in an aggregator based on the
            :func:`coherence.extractor.ChainedExtractor` that is based on an array of corresponding
            :func:`coherence.extractor.UniversalExtractor` objects; must not be `None`
        """
        super().__init__(extractor_or_property)


class Aggregators:
    """Simple Aggregator DSL.

    The methods in this class are for the most part simple factory methods for various
    :func:`coherence.aggregator.EntryAggregator`  classes, but in some cases provide additional type safety. They
    also tend to make the code more readable, especially if imported statically, so their use is strongly encouraged
    in lieu of direct construction of :func:`coherence.aggregator.EntryAggregator`  classes."""

    @staticmethod
    def max(extractor_or_property: ExtractorExpression[T, E]) -> MaxAggregator[R]:
        """
        Return an aggregator that calculates a maximum of the numeric values extracted from a set of entries in a Map.

        :param extractor_or_property: the extractor or method/property name to provide values for aggregation
        :return: an aggregator that calculates a maximum of the numeric values extracted from a set of entries in a Map
        """
        return MaxAggregator(extractor_or_property)

    @staticmethod
    def min(extractor_or_property: ExtractorExpression[T, E]) -> MinAggregator[R]:
        """
        Return an aggregator that calculates a minimum of the numeric values extracted from a set of entries in a Map.

        :param extractor_or_property: the extractor or method/property name to provide values for aggregation
        :return: an aggregator that calculates a minimum of the numeric values extracted from a set of entries in a Map.
        """
        return MinAggregator(extractor_or_property)

    @staticmethod
    def sum(extractor_or_property: ExtractorExpression[T, E]) -> SumAggregator:
        """
        Return an aggregator that calculates a sum of the numeric values extracted from a set of entries in a Map.

        :param extractor_or_property: the extractor or method/property name to provide values for aggregation
        :return: an aggregator that calculates a sum of the numeric values extracted from a set of entries in a Map.
        """
        return SumAggregator(extractor_or_property)

    @staticmethod
    def average(extractor_or_property: ExtractorExpression[T, E]) -> AverageAggregator:
        """
        Return an aggregator that calculates an average of the numeric values extracted from a set of entries in a Map.

        :param extractor_or_property: the extractor or method/property name to provide values for aggregation
        :return: an aggregator that calculates an average of the numeric values extracted from a
                 set of entries in a Map.
        """
        return AverageAggregator(extractor_or_property)

    @staticmethod
    def distinct(extractor_or_property: ExtractorExpression[T, E]) -> DistinctValuesAggregator[R]:
        """
        Return an aggregator that calculates the set of distinct values from the entries in a Map.

        :param extractor_or_property: the extractor or method/property name to provide values for aggregation
        :return: an aggregator that calculates the set of distinct values from the entries in a Map.
        """
        return DistinctValuesAggregator(extractor_or_property)

    @staticmethod
    def count() -> CountAggregator:
        """
        Return an aggregator that calculates a number of values in an entry set.

        :return: an aggregator that calculates a number of values in an entry set.
        """
        return CountAggregator()

    @staticmethod
    def top(count: int) -> TopAggregator[Any, Any]:
        """
        Return an aggregator that aggregates the top *N* extracted values into an array.

        :param count: the maximum number of results to include in the aggregation result
        :return: an aggregator that aggregates the top *N* extracted values into an array.
        """
        return TopAggregator(count)

    @staticmethod
    def group_by(
        extractor_or_property: ExtractorExpression[T, E],
        aggregator: EntryAggregator[Any],
        filter: Optional[Filter] = None,
    ) -> GroupAggregator[AggregationResult[G, T]]:
        """
        Return a :func:`coherence.aggregator.GroupAggregator` based on a specified property or method name(s) and an
        :func:`coherence.aggregator.EntryAggregator`.

        :param extractor_or_property: the extractor or method/property name to provide values for aggregation
        :param aggregator: the underlying :func:`coherence.aggregator.EntryAggregator`
        :param filter: an optional :func:`coherence.filter.Filter` object used to filter out results of individual
          group aggregation results
        :return: a :func:`coherence.aggregator.GroupAggregator` based on a specified property or method name(s) and an
          :func:`coherence.aggregator.EntryAggregator`.
        """
        return GroupAggregator(extractor_or_property, aggregator, filter)

    @staticmethod
    def priority(
        aggregator: EntryAggregator[R],
        execution_timeout: Timeout = Timeout.DEFAULT,
        request_timeout: Timeout = Timeout.DEFAULT,
        scheduling_priority: Schedule = Schedule.STANDARD,
    ) -> PriorityAggregator[R]:
        """
        Return a new :func:`coherence.aggregator.PriorityAggregator` to control scheduling priority of an aggregation
        operation.

        :param aggregator: the underlying :func:`coherence.aggregator.EntryAggregator`
        :param execution_timeout: the execution :func:`coherence.aggregator.Timeout`
        :param request_timeout: the request :func:`coherence.aggregator.Timeout`
        :param scheduling_priority: the :func:`coherence.aggregator.Schedule` priority
        :return: a new :func:`coherence.aggregator.PriorityAggregator` to control scheduling priority of an aggregation
         operation.
        """
        return PriorityAggregator(aggregator, execution_timeout, request_timeout, scheduling_priority)

    @staticmethod
    def script(language: str, script_name: str, characteristics: int = 0, *args: Any) -> ScriptAggregator[R]:
        """
        Return an aggregator that is implemented in a script using the specified language.

        :param language: The language with which the script is written in.
        :param script_name: The name of the :func:`coherence.aggregator.EntryAggregator` that needs to be evaluated.
        :param characteristics: Present only for serialization purposes.
        :param args: The arguments to be passed to the script for evaluation
        :return: an aggregator that is implemented in a script using the specified language.
        """
        return ScriptAggregator(language, script_name, characteristics, *args)

    @staticmethod
    def record(query_type: RecordType = RecordType.EXPLAIN) -> QueryRecorder:
        """
        Returns a new :func:`coherence.aggregator.QueryRecorder` aggregator which may be used is used to produce an
        object that contains an estimated or actual cost of the query execution for a given
        :func:`coherence.filter.Filter`.

        :param query_type: the :func:`coherence.aggregator.RecordType`
        :return: a new :func:`coherence.aggregator.QueryRecorder` aggregator which may be used is used to produce an
         object that contains an estimated or actual cost of the query execution for a given
         :func:`coherence.filter.Filter`.
        """
        return QueryRecorder(query_type)

    @staticmethod
    def reduce(extractor_or_property: ExtractorExpression[T, E]) -> ReducerAggregator[ReducerResult[K]]:
        """
        Return an aggregator that will return the extracted value for each entry in the map.

        :param extractor_or_property: the extractor or method/property name to provide values for aggregation
        :return: an aggregator that will return the extracted value for each entry in the map.
        """
        return ReducerAggregator(extractor_or_property)
