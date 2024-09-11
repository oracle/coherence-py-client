# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

from abc import ABC
from decimal import Decimal
from typing import Any, Generic, List, Optional, TypeVar, Union, cast

from typing_extensions import TypeAlias

from .extractor import (
    CompositeUpdater,
    ExtractorExpression,
    Extractors,
    ManipulatorExpression,
    UniversalExtractor,
    UniversalUpdater,
    UpdaterExpression,
    ValueExtractor,
    ValueManipulator,
    ValueUpdater,
)
from .filter import Filter
from .serialization import mappings, proxy

E = TypeVar("E")
K = TypeVar("K")
R = TypeVar("R")
T = TypeVar("T")
V = TypeVar("V")

Numeric: TypeAlias = Union[int, float, Decimal]


class EntryProcessor(ABC, Generic[R]):
    """
    An invocable agent that operates against the entries within a NamedMap
    """

    def __init__(self) -> None:
        """
        Constructs a new `EntryProcessor`
        """
        super().__init__()

    def and_then(self, processor: EntryProcessor[Any]) -> EntryProcessor[Any]:
        """
        Returns a :class:`coherence.processor.CompositeProcessor` comprised of this and the provided processor.

        :param processor: the next processor
        :return: a :class:`coherence.processor.CompositeProcessor` comprised of this and the provided processor
        """
        return CompositeProcessor(self, processor)

    def when(self, filter: Filter) -> EntryProcessor[R]:
        """
        Returns a :class:`coherence.processor.ConditionalProcessor` comprised of this processor and the provided filter.

        The specified entry processor gets invoked if and only if the filter
        applied to the entry evaluates to `true`; otherwise the
        result of the invocation will return `None`.

        :param filter: the filter :return: Returns a :class:`coherence.processor.ConditionalProcessor` comprised
         of this processor and the provided filter.
        """
        return ConditionalProcessor(filter, self)


@proxy("processor.ExtractorProcessor")
class ExtractorProcessor(EntryProcessor[R]):
    """
    `ExtractorProcessor` is an :class:`coherence.processor.EntryProcessor` implementation that extracts a value from
    an object cached within a NamedMap.

    :Example:
        A common usage pattern is:

        >>> cache.invoke(aPerson,ExtractorProcessor("age"))

    For clustered caches using the ExtractorProcessor could significantly reduce the amount of network traffic.
    """

    def __init__(self, value_extractor: ExtractorExpression[V, R]):
        """
        Construct an `ExtractorProcessor` using the given extractor or method name.

        :param value_extractor: the :class:`coherence.extractor.ValueExtractor` or string expression
                                to use by this filter or the name of the method to
                                invoke via java reflection
        """
        super().__init__()
        if value_extractor is None:
            self.extractor: ValueExtractor[V, R] = Extractors.identity()
        else:
            if isinstance(value_extractor, ValueExtractor):
                self.extractor = value_extractor
            elif isinstance(value_extractor, str):
                self.extractor = Extractors.extract(value_extractor)
            else:
                raise ValueError("value_extractor cannot be any other type")


@proxy("processor.CompositeProcessor")
class CompositeProcessor(EntryProcessor[R]):
    """
    CompositeProcessor represents a collection of entry processors that are invoked sequentially against the same
    MapEntry.
    """

    def __init__(self, *processors: Any):
        """
        Construct a `CompositeProcessor` for the specified array of individual entry processors.

        The result of the `CompositeProcessor` execution is an array of results returned by the individual
        EntryProcessor invocations.

        :param processors: the entry processor array
        """
        super().__init__()
        self.processors: list[EntryProcessor[Any]] = list()
        for p in processors:
            self.processors.append(p)

    def and_then(self, processor: EntryProcessor[Any]) -> CompositeProcessor[R]:
        self.processors.append(processor)
        return self


@proxy("processor.ConditionalProcessor")
class ConditionalProcessor(EntryProcessor[V]):
    """
    ConditionalProcessor represents a processor that is invoked conditionally based on the result of an entry
    evaluation.  A `ConditionalProcessor` is returned from the `when()` function, which takes a filter as its argument.
    """

    def __init__(self, filter: Filter, processor: EntryProcessor[V]):
        """
        Construct a ConditionalProcessor for the specified filter and the processor.

        The specified entry processor gets invoked if and only if the filter applied to the cache entry evaluates to
        `true`; otherwise the result of the invocation will return `null`.

        :param filter: the filter
        :param processor: the entry processor
        """
        super().__init__()
        self.filter = filter
        self.processor = processor


@proxy("util.NullEntryProcessor")
class NullProcessor(EntryProcessor[bool]):
    """
    Put entry processor.

    An implementation of an EntryProcessor that does nothing and returns `true` as a result of execution.
    """

    __instance: Any = None

    def __init__(self) -> None:
        """
        Construct a Null EntryProcessor.
        """
        super().__init__()


class PropertyProcessor(EntryProcessor[R]):
    """
    `PropertyProcessor` is a base class for EntryProcessor implementations that depend on a ValueManipulator.
    """

    def __init__(self, manipulator: ManipulatorExpression[T, E], use_is: bool = False):
        """
        Construct a PropertyProcessor for the specified property name.

        This constructor assumes that the corresponding property getter will have a name of ("get" + sName) and the
        corresponding property setter's name will be ("set" + sName).

        :param manipulator: the manipulator or property name
        :param use_is: prefix with `is`
        """
        super().__init__()
        if type(manipulator) is str:
            self.manipulator: ManipulatorExpression[T, E] = PropertyManipulator(manipulator, use_is)
        else:
            self.manipulator = manipulator


@proxy("processor.PropertyManipulator")
class PropertyManipulator(ValueManipulator[V, R]):
    """
    `PropertyManipulator` is a reflection based ValueManipulator implementation based on the JavaBean property name
    conventions.
    """

    def __init__(self, property_name: str, use_is: bool = False):
        """
        Construct a PropertyManipulator for the specified property name.

        This constructor assumes that the corresponding property getter will have a name of either ("get" + sName) or
        ("is" + sName) and the corresponding property setter's name will be ("set" + sName).

        :param property_name: a property name
        :param use_is: if true, the getter method will be prefixed with "is" rather than "get"
        """
        super().__init__()
        self.property_name = property_name
        self.useIsPrefix = use_is

    def get_extractor(self) -> ValueExtractor[V, R]:
        raise NotImplementedError("Method not implemented")

    def get_updator(self) -> ValueUpdater[V, R]:
        raise NotImplementedError("Method not implemented")


@proxy("processor.NumberMultiplier")
class NumberMultiplier(PropertyProcessor[Numeric]):
    """
    NumberMultiplier entry processor.
    """

    def __init__(
        self, name_or_manipulator: ManipulatorExpression[T, E], multiplier: Numeric, post_multiplication: bool = False
    ):
        """
        Construct an NumberMultiplier processor that will multiply a property value by a specified factor,
        returning either the old or the new value as specified.

        :param name_or_manipulator: the ValueManipulator or the property name
        :param multiplier: the Number representing the magnitude and sign of the multiplier
        :param post_multiplication: pass true to return the value as it was before it was multiplied, or pass false
         to return the value as it is after it is multiplied
        """
        if isinstance(name_or_manipulator, str):
            manipulator: ValueManipulator[Any, Numeric] = self.create_custom_manipulator(name_or_manipulator)
            super().__init__(manipulator)
        else:
            super().__init__(name_or_manipulator)
        self.multiplier = multiplier
        self.postMultiplication = post_multiplication

    @staticmethod
    def create_custom_manipulator(name_or_manipulator: str) -> ValueManipulator[V, Numeric]:
        cu: CompositeUpdater[V, Numeric] = CompositeUpdater(
            UniversalExtractor(name_or_manipulator), UniversalUpdater(name_or_manipulator)
        )
        return cu


@proxy("processor.NumberIncrementor")
class NumberIncrementor(PropertyProcessor[Numeric]):
    """
    The :class:`coherence.processor.NumberIncrementor` :class:`coherence.processor.EntryProcessor` is used to increment
    a property value of a numeric type.
    """

    def __init__(
        self, name_or_manipulator: ManipulatorExpression[T, E], increment: Numeric, post_increment: bool = False
    ):
        """
        Construct an :class:`coherence.processor.NumberIncrementor` processor that will increment a property
        value by a specified amount, returning either the old or the new value as specified.

        :param name_or_manipulator: the :class:`coherence.extractor.ValueManipulator` or string expression
        :param increment: the numeric value representing the magnitude and sign of the increment
        :param post_increment: pass `True` to return the value as it was before it was incremented, or pass `False`
         to return the value as it is after it is incremented
        """
        if isinstance(name_or_manipulator, str):
            manipulator: ValueManipulator[Any, Numeric] = self.create_custom_manipulator(name_or_manipulator)
            super().__init__(manipulator)
        else:
            super().__init__(name_or_manipulator)
        self.increment = increment
        self.postInc = post_increment

    @staticmethod
    def create_custom_manipulator(name_or_manipulator: str) -> ValueManipulator[Any, Numeric]:
        cu: CompositeUpdater[Any, Numeric] = CompositeUpdater(
            UniversalExtractor(name_or_manipulator), UniversalUpdater(name_or_manipulator)
        )
        return cu


@proxy("processor.ConditionalPut")
@mappings({"return_": "return"})
class ConditionalPut(EntryProcessor[V]):
    """
    :class:`coherence.processor.ConditionalPut` is an :class:`coherence.processor.EntryProcessor` that performs
    an update operation for an entry that satisfies the specified condition.

    While the :class:`coherence.processor.ConditionalPut` processing could be implemented via direct key-based
    :class:`coherence.client.NamedMap` operations, it is more efficient and enforces concurrency control without
    explicit locking.

    Obviously, using more specific, fine-tuned filters (rather than ones based on the
    :class:`coherence.extractor.IdentityExtractor`) may provide additional flexibility and efficiency allowing
    the put operation to be performed conditionally on values of specific attributes (or even calculations)
    instead of the entire object.
    """

    def __init__(self, filter: Filter, value: V, return_value: bool = True):
        """
        Construct a :class:`coherence.processor.ConditionalPut` that updates an entry with a new value if and only
        if the filter applied to the entry evaluates to `True`.

        :param filter: the :class:`coherence.filter.Filter` to evaluate an entry
        :param value: a value to update an entry with
        :param return_value: specifies whether the processor should return the current value in case it has
         not been updated
        """
        super().__init__()
        self.filter = filter
        self.value = value
        self.return_ = return_value


@proxy("processor.ConditionalPutAll")
class ConditionalPutAll(EntryProcessor[V]):
    """
    `ConditionalPutAll` is an `EntryProcessor` that performs an update operation for multiple entries that satisfy the
    specified condition.

    This allows for concurrent insertion/update of values within the cache.

    :Example:

        For example a concurrent `replaceAll(map)` could be implemented as:

            >>> filter = PresentFilter.INSTANCE
            >>> cache.invokeAll(map.keys(), ConditionalPutAll(filter, map))

        or `putAllIfAbsent` could be done by inverting the filter:

            >>> filter = NotFilter(PresentFilter())


    Obviously, using more specific, fine-tuned filters may provide additional flexibility and efficiency allowing the
    multi-put operations to be performed conditionally on values of specific attributes (or even calculations)
    instead of a simple existence check.
    """

    def __init__(self, filter: Filter, the_map: dict[K, V]):
        """
        Construct a `ConditionalPutAll` processor that updates an entry with a new value if and only if the filter
        applied to the entry evaluates to `True`. The new value is extracted from the specified map based on the
        entry's key.

        :param filter: the filter to evaluate all supplied entries
        :param the_map: a dict of values to update entries with
        """
        super().__init__()
        self.filter = filter
        self.entries = the_map


@proxy("processor.ConditionalRemove")
@mappings({"return_value": "return"})
class ConditionalRemove(EntryProcessor[V]):
    """
    `ConditionalRemove` is an `EntryProcessor` that performs n remove operation if the specified condition is satisfied.

    While the `ConditionalRemove` processing could be implemented via direct key-based `NamedMap` operations, it is more
    efficient and enforces concurrency control without explicit locking.
    """

    def __init__(self, filter: Filter, return_value: bool = False):
        """
        Construct a :class:`coherence.processor.ConditionalRemove` processor that removes an
        :class:`coherence.client.NamedMap` entry if and only if the filter applied to the entry evaluates to `True`.

        This processor may optionally return the current value as a result of
        the invocation if it has not been removed (the :class:`coherence.filter.Filter` evaluated to
        `False`).

        :param filter: the filter to evaluate an entry
        :param return_value: specifies whether the processor should return the current value if it has not
         been removed
        """
        super().__init__()
        self.filter = filter
        self.return_value = return_value


@proxy("processor.MethodInvocationProcessor")
class MethodInvocationProcessor(EntryProcessor[R]):
    """
    An :class:`coherence.processor.EntryProcessor` that invokes the specified method on a value of a cache entry
    and optionally updates the entry with a modified value.
    """

    def __init__(self, method_name: str, mutator: bool, *args: Any):
        """
        Construct :class:`coherence.processor.MethodInvoctionProcessor` instance.

        :param method_name: the name of the method to invoke
        :param mutator: the flag specifying whether the method mutates the state of a target object, which implies
         that the entry value should be updated after method invocation
        :param args: the method arguments
        """
        super().__init__()
        self.methodName = method_name
        self.mutator = mutator
        self.args: List[Any] = list(*args)


@proxy("processor.TouchProcessor")
class TouchProcessor(EntryProcessor[None]):
    """
    Touches an entry (if present) in order to trigger interceptor re-evaluation and possibly increment expiry time.
    """

    def __init__(self) -> None:
        """
        Construct a `TouchProcessor`
        """
        super().__init__()


@proxy("processor.ScriptProcessor")
class ScriptProcessor(EntryProcessor[Any]):
    """
    ScriptProcessor wraps a script written in one of the languages supported by Graal VM.
    """

    def __init__(self, name: str, language: str, *args: Any):
        """
        Create a :class:`coherence.processor.ScriptProcessor` that wraps a script written in the specified language
        and identified by the specified name. The specified args will be passed during execution of the script.

        :param name: the name of the :class:`coherence.processor.EntryProcessor` that needs to be executed
        :param language: the language the script is written. Currently, only `js` (for JavaScript) is supported
        :param args: the arguments to be passed to the :class:`coherence.processor.EntryProcessor`
        """
        super().__init__()
        self.name = name
        self.language = language
        self.args: List[Any] = list(*args)


@proxy("processor.PreloadRequest")
class PreloadRequest(EntryProcessor[None]):
    """
    `PreloadRequest` is a simple :class:`coherence.processor.EntryProcessor` that performs
    a get call. No results are reported back to the caller.

    The :class:`coherence.processor.PreloadRequest` process provides a means to "preload" an entry or a collection
    of entries into the cache using the cache loader without incurring the cost of sending the value(s) over the
    network. If the corresponding entry (or entries) already exists in the cache, or if the cache does not have a
    loader, then invoking this :class:`coherence.processor.EntryProcessor` has no effect.
    """

    def __init__(self) -> None:
        """
        Construct a PreloadRequest EntryProcessor.
        """
        super().__init__()


@proxy("processor.UpdaterProcessor")
class UpdaterProcessor(EntryProcessor[bool]):
    """
    `UpdaterProcessor` is an :class:`coherence.processor.EntryProcessor` implementations that updates an attribute
    of an object cached in an InvocableMap.

    While it's possible to update a value via standard Map API, using the updater allows for clustered caches using
    the UpdaterProcessor allows avoiding explicit concurrency control and could significantly reduce the amount of
    network traffic.
    """

    def __init__(self, updater_or_property_name: UpdaterExpression[V, bool], value: V):
        """
        Construct an `UpdaterProcessor` based on the specified ValueUpdater.

        :param updater_or_property_name: a ValueUpdater object or the method name; passing null will simpy replace
         the entry's value with the specified one instead of updating it
        :param value: the value to update the target entry with
        """
        super().__init__()
        if type(updater_or_property_name) == str:  # noqa: E721
            self.updater: ValueUpdater[V, bool]
            if updater_or_property_name.find(".") == -1:
                self.updater = UniversalUpdater(updater_or_property_name)
            else:
                self.updater = CompositeUpdater(updater_or_property_name)
        else:
            self.updater = cast(ValueUpdater[V, bool], updater_or_property_name)
        self.value = value


@proxy("processor.VersionedPut")
@mappings({"return_current": "return"})
class VersionedPut(EntryProcessor[V]):
    """
    `VersionedPut` is an :class:`coherence.processor.EntryProcessor` that assumes that entry values are versioned (see
    Coherence Versionable interface for details) and performs an update/insert operation if and only if the version
    of the specified value matches the version of the corresponding value. `VersionedPutAll` will increment the
    version indicator before each value is updated.
    """

    def __init__(self, value: V, allow_insert: bool = False, return_current: bool = False):
        """
        Construct a `VersionedPut` that updates an entry with a new value if and only if the version of the new value
        matches to the version of the current entry's value. This processor optionally returns the current value as a
        result of the invocation if it has not been updated (the versions did not match).

        :param value: a value to update an entry with
        :param allow_insert: specifies whether an insert should be allowed (no currently existing value)
        :param return_current: specifies whether the processor should return the current value in case it has
         not been updated
        """
        super().__init__()
        self.value = value
        self.allowInsert = allow_insert
        self.return_current = return_current


@proxy("processor.VersionedPutAll")
@mappings({"return_current": "return"})
class VersionedPutAll(EntryProcessor[V]):
    """
    `VersionedPutAll` is an :class:`coherence.processor.EntryProcessor` that assumes that entry values are versioned (
    see Coherence Versionable interface for details) and performs an update/insert operation only for entries whose
    versions match to versions of the corresponding current values. In case of the match, the `VersionedPutAll` will
    increment the version indicator before each value is updated.
    """

    def __init__(self, values: dict[K, V], allow_insert: bool = False, return_current: bool = False):
        """
        Construct a VersionedPutAll processor that updates an entry with a new value if and only if the version of
        the new value matches to the version of the current entry's value (which must exist). This processor
        optionally returns a map of entries that have not been updated (the versions did not match).

        :param values: a `dict` of values to update entries with
        :param allow_insert: specifies whether an insert should be allowed (no currently existing value)
        :param return_current: specifies whether the processor should return the current value in case it has
         not been updated
        """
        super().__init__()
        self.entries = values
        self.allowInsert = allow_insert
        self.return_current = return_current


class Processors:
    """
    The `Processors` class provides a set of static methods for creating standard Coherence
    :class:`coherence.processor.EntryProcessor`'s.
    """

    def __init__(self) -> None:
        """
        Raises `NotImplementedError` if called.
        """
        raise NotImplementedError()

    @staticmethod
    def conditional_put(filter: Filter, value: V, return_value: bool = False) -> EntryProcessor[V]:
        """
        Construct a :class:`coherence.processor.ConditionalPut` that updates an entry with a new value if and only
        if the :class:`coherence.filter.Filter` applied to the entry evaluates to `True`.

         :param filter: the :class:`coherence.filter.Filter` to evaluate an entry
         :param value: a value to update an entry with
         :param return_value: specifies whether the processor should return the current value in case it
                has not been updated
         :return: a processor that updates an entry with a new value if and only if the filter applied
                  to the entry evaluates to `True`.
        """
        return ConditionalPut(filter, value, return_value)

    @staticmethod
    def conditional_put_all(filter: Filter, values: dict[K, V]) -> EntryProcessor[V]:
        """
        Construct a :class:`coherence.processor.ConditionalRemove` processor that updates an entry with a new value if
        and only if the :class:`coherence.filter.Filter` applied to the entry evaluates to `True`. The new value is
        extracted from the specified map based on the entry's key.

        :param filter: the :class:`coherence.filter.Filter` to evaluate all supplied entries
        :param values: a `dict` of values to update entries with
        :return: a processor that updates one or more entries with the provided values if and only if the
                 filter applied to the entry evaluates to `True`
        """
        return ConditionalPutAll(filter, values)

    @staticmethod
    def conditional_remove(filter: Filter, return_value: bool = False) -> EntryProcessor[V]:
        """
        Constructs a :class:`coherence.processor.ConditionalRemove` processor that removes an
        :class:`coherence.client.NamedMap` entry if and only if the :class:`coherence.filter.Filter`
        applied to the entry evaluates to `True`.

        This processor may optionally return the current value as a result of
        the invocation if it has not been removed (the :class:`coherence.filter.Filter` evaluated to
        `False`).

        :param filter: the :class:`coherence.filter.Filter` to evaluate an entry
        :param return_value: specifies whether the processor should return the current value if it has not
         been removed
        """
        return ConditionalRemove(filter, return_value)

    @staticmethod
    def extract(extractor: Optional[ExtractorExpression[T, E]] = None) -> EntryProcessor[E]:
        """
        Construct an :class:`coherence.processor.ExtractorProcessor` using the given
        :class:`coherence.extractor.ValueExtractor` or string expression to extract a value from an object cached
        within a :class:`coherence.client.NamedMap`.

        For clustered caches using the :class:`coherence.processor.ExtractorProcessor` could significantly reduce
        the amount of network traffic.

        :param extractor: the :class:`coherence.extractor.ValueExtractor` or string expression to use by this
                          processor or the name of the method to invoke via java reflection.  If `None`, an
                          :class:`coherence.extractor.IdentityExtractor` will be used.
        """
        ext: ExtractorExpression[T, E] = extractor if extractor is not None else Extractors.identity()
        return ExtractorProcessor(ext)

    @staticmethod
    def increment(
        name_or_manipulator: ManipulatorExpression[T, E], increment: Numeric, post_increment: bool = False
    ) -> EntryProcessor[Numeric]:
        """
        Construct an :class:`coherence.processor.NumberIncrementor` processor that will increment a property
        value by a specified amount, returning either the old or the new value as specified.

        :param name_or_manipulator: the :class:`coherence.extractor.ValueManipulator` or string expression
        :param increment: the numeric value representing the magnitude and sign of the increment
        :param post_increment: pass `True` to return the value as it was before it was incremented, or pass `False`
         to return the value as it is after it is incremented
        :return:
        """
        return NumberIncrementor(name_or_manipulator, increment, post_increment)

    @staticmethod
    def invoke_accessor(method_name: str, *args: Any) -> EntryProcessor[R]:
        """
        Constructs a :class:`coherence.processor.MethodInvocationProcessor` that invokes the specified method on
         a value of a cache entry.

        :param method_name: the name of the method to invoke
        :param args: the method arguments
        :return: a :class:`coherence.processor.MethodInvocationProcessor` that invokes the specified method on
                 a value of a cache entry and optionally updates the entry with a modified value
        """
        return MethodInvocationProcessor(method_name, False, args)

    @staticmethod
    def invoke_mutator(method_name: str, *args: Any) -> EntryProcessor[R]:
        """
        Constructs a :class:`coherence.processor.MethodInvocationProcessor` that invokes the specified method on
        a value of a cache entry updating the entry with a modified value.

        :param method_name: the name of the method to invoke
        :param args: the method arguments
        :return: a :class:`coherence.processor.MethodInvocationProcessor` that invokes the specified method on
                 a value of a cache entry and optionally updates the entry with a modified value
        """
        return MethodInvocationProcessor(method_name, True, args)

    @staticmethod
    def multiply(
        name_or_manipulator: ManipulatorExpression[T, E], multiplier: Numeric, post_multiplication: bool = False
    ) -> EntryProcessor[Numeric]:
        """
        Construct an NumberMultiplier processor that will multiply a property value by a specified factor,
        returning either the old or the new value as specified.

        :param name_or_manipulator: the ValueManipulator or the property name
        :param multiplier: the Number representing the magnitude and sign of the multiplier
        :param post_multiplication: pass `True` to return the value as it was before it was multiplied, or pass `False`
         to return the value as it is after it is multiplied
        """
        return NumberMultiplier(name_or_manipulator, multiplier, post_multiplication)

    @staticmethod
    def nop() -> EntryProcessor[bool]:
        """
        Construct an :class:`coherence.processor.EntryProcessor` that does nothing and returns `True`
        as a result of execution
        :return: an :class:`coherence.processor.EntryProcessor` that does nothing and returns `True`
        as a result of execution
        """
        return NullProcessor()

    @staticmethod
    def preload() -> EntryProcessor[None]:
        """
        :class:`coherence.processor.PreloadRequest` is a simple :class:`coherence.processor.EntryProcessor` that
        performs a get call. No results are reported back to the caller.

        The :class:`coherence.processor.PreloadRequest` process provides a means to "preload" an entry or a
        collection of entries into the cache using the cache loader without incurring the cost of sending the
        value(s) over the network. If the corresponding entry (or entries) already exists in the cache,
        or if the cache does not have a loader, then invoking this :class:`coherence.processor.PreloadRequest`
        has no effect.
        :return:
        """
        return PreloadRequest()

    @staticmethod
    def script(name: str, language: str, *args: Any) -> EntryProcessor[Any]:
        """
        Create a :class:`coherence.processor.ScriptProcessor` that wraps a script written in the specified language
        and identified by the specified name. The specified args will be passed during execution of the script.

        :param name: the name of the :class:`coherence.processor.EntryProcessor` that needs to be executed
        :param language: the language the script is written. Currently, only `js` (for JavaScript) is supported
        :param args: the arguments to be passed to the :class:`coherence.processor.EntryProcessor`
        """
        return ScriptProcessor(name, language, args)

    @staticmethod
    def touch() -> EntryProcessor[None]:
        """
        Creates an :class:`coherence.processor.EntryProcessor` that touches an entry (if present) in order to
        trigger interceptor re-evaluation and possibly increment expiry time.
        :return:
        """
        return TouchProcessor()

    @staticmethod
    def update(updater_or_property_name: UpdaterExpression[V, bool], value: V) -> EntryProcessor[bool]:
        """
        Construct an :class:`coherence.processor.UpdaterProcessor` based on the specified `ValueUpdater`.

        While it's possible to update a value via standard Map API, using the updater allows for clustered caches using
        the `UpdaterProcessor` allows avoiding explicit concurrency control and could significantly reduce the amount of
        network traffic.

        :param updater_or_property_name: a ValueUpdater object or the method name; passing null will simpy replace
         the entry's value with the specified one instead of updating it
        :param value: the value to update the target entry with
        """
        return UpdaterProcessor(updater_or_property_name, value)

    @staticmethod
    def versioned_put(value: V, allow_insert: bool = False, return_current: bool = False) -> EntryProcessor[V]:
        """
        Construct a :class:`coherence.processor.VersionedPut` that updates an entry with a new value if and only
        if the version of the new value matches to the version of the current entry's value. This processor optionally
        returns the current value as a result of the invocation if it has not been updated (the versions did not match).

        :param value: a value to update an entry with
        :param allow_insert: specifies whether an insert should be allowed (no currently existing value)
        :param return_current: specifies whether the processor should return the current value in case it has
         not been updated
        """
        return VersionedPut(value, allow_insert, return_current)

    @staticmethod
    def versioned_put_all(
        values: dict[K, V], allow_insert: bool = False, return_current: bool = False
    ) -> EntryProcessor[V]:
        """
        Construct a :class:`coherence.processor.VersionedPut` processor that updates an entry with a new value if
        and only if the version of the new value matches to the version of the current entry's value
        (which must exist). This processor optionally returns a map of entries that have not been updated
        (the versions did not match).

        :param values: a `dict` of values to update entries with
        :param allow_insert: specifies whether an insert should be allowed (no currently existing value)
        :param return_current: specifies whether the processor should return the current value in case it has
         not been updated
        """
        return VersionedPutAll(values, allow_insert, return_current)
