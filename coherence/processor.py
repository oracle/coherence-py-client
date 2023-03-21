# Copyright (c) 2022 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

from abc import ABC
from typing import Any, TypeVar

from .extractor import (
    ChainedExtractor,
    CompositeUpdater,
    IdentityExtractor,
    UniversalExtractor,
    UniversalUpdater,
    ValueExtractor,
    ValueManipulator,
    ValueUpdater,
)
from .filter import Filter
from .serialization import mappings, proxy

K = TypeVar("K", covariant=True)
V = TypeVar("V", covariant=True)
R = TypeVar("R", covariant=True)


class EntryProcessor(ABC):
    """
    An invocable agent that operates against the entries within a NamedMap
    """

    def __init__(self) -> None:
        """
        Constructs a new `EntryProcessor`
        """
        super().__init__()

    def and_then(self, processor: EntryProcessor) -> EntryProcessor:
        """
        Returns a :func:`coherence.processor.CompositeProcessor` comprised of this and the provided processor.

        :param processor: the next processor
        :return: a :func:`coherence.processor.CompositeProcessor` comprised of this and the provided processor
        """
        return CompositeProcessor(self, processor)

    def when(self, filter: Filter) -> EntryProcessor:
        """
        Returns a :func:`coherence.processor.ConditionalProcessor` comprised of this processor and the provided filter.

        The specified entry processor gets invoked if and only if the filter
        applied to the entry evaluates to `true`; otherwise the
        result of the invocation will return `None`.

        :param filter: the filter :return: Returns a :func:`coherence.processor.ConditionalProcessor` comprised of
         this processor and the provided filter.
        """
        return ConditionalProcessor(filter, self)


@proxy("processor.ExtractorProcessor")
class ExtractorProcessor(EntryProcessor):
    """
    `ExtractorProcessor` is an :func:`coherence.processor.EntryProcessor` implementation that extracts a value from
    an object cached a NamedMap.

    :Example:
        A common usage pattern is:

        >>> cache.invoke(aPerson,ExtractorProcessor("age"))

    For clustered caches using the ExtractorProcessor could significantly reduce the amount of network traffic.
    """

    def __init__(self, value_extractor: ValueExtractor | str):
        """
        Construct an ExtractorProcessor using the given extractor or method name.

        :param value_extractor: the extractor.ValueExtractor to use by this filter or the name of the method to
                          invoke via reflection
        """
        super().__init__()
        if value_extractor is None:
            self.extractor: ValueExtractor = IdentityExtractor()
        else:
            if isinstance(value_extractor, ValueExtractor):
                self.extractor = value_extractor
            elif type(value_extractor) == str:
                if value_extractor.find(".") == -1:
                    self.extractor = UniversalExtractor(value_extractor)
                else:
                    self.extractor = ChainedExtractor(value_extractor)
            else:
                raise ValueError("value_extractor cannot be any other type")

    @classmethod
    def create(cls, method_or_field: ValueExtractor | str) -> ExtractorProcessor:
        """
        Class method to Construct an ExtractorProcessor using the given extractor or method name.

        :param method_or_field: the extractor.ValueExtractor to use by this filter or the name of the method to
                          invoke via reflection
        :return: the constructed ExtractorProcessor
        """
        return cls(method_or_field)


@proxy("processor.CompositeProcessor")
class CompositeProcessor(EntryProcessor):
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
        self.processors: list[EntryProcessor] = list()
        for p in processors:
            self.processors.append(p)

    def and_then(self, processor: EntryProcessor) -> CompositeProcessor:
        self.processors.append(processor)
        return self


@proxy("processor.ConditionalProcessor")
class ConditionalProcessor(EntryProcessor):
    """
    ConditionalProcessor represents a processor that is invoked conditionally based on the result of an entry
    evaluation.  A `ConditionalProcessor` is returned from the `when()` function, which takes a filter as its argument.
    """

    def __init__(self, filter: Filter, processor: EntryProcessor):
        """
        Construct a ConditionalProcessor for the specified filter and the processor.

        The specified entry processor gets invoked if and only if the filter applied to the cache entry evaluates to
        `true`; otherwise the result of the invocation will return `null`.

        :param filter: the filter
        :param processor: the the entry processor
        """
        super().__init__()
        self.filter = filter
        self.processor = processor

    @classmethod
    def create(cls, filter: Filter, processor: EntryProcessor) -> ConditionalProcessor:
        """
        The class method to Construct a ConditionalProcessor for the specified filter and the processor.

        :param filter: the filter
        :param processor: the the entry processor
        :return: the constructed ConditionalProcessor
        """
        return cls(filter, processor)


@proxy("util.NullEntryProcessor")
class NullProcessor(EntryProcessor):
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
        if NullProcessor.__instance is None:
            NullProcessor.__instance = self

    @classmethod
    def get_instance(cls) -> Any:
        """
        Returns the singleton instance of Null EntryProcessor

        :return: the singleton instance of Null EntryProcessor
        """
        if NullProcessor.__instance is None:
            NullProcessor()
        return NullProcessor.__instance


class PropertyProcessor(EntryProcessor):
    """
    `PropertyProcessor` is a base class for EntryProcessor implementations that depend on a ValueManipulator.
    """

    def __init__(self, manipulator: ValueManipulator | str, use_is: bool = False):
        """
        Construct a PropertyProcessor for the specified property name.

        This constructor assumes that the corresponding property getter will have a name of ("get" + sName) and the
        corresponding property setter's name will be ("set" + sName).

        :param manipulator: the manipulator or property name
        :param use_is: prefix with `is`
        """
        super().__init__()
        if type(manipulator) is str:
            self.manipulator: ValueManipulator | str = PropertyManipulator(manipulator, use_is)
        else:
            self.manipulator = manipulator


@proxy("processor.PropertyManipulator")
class PropertyManipulator(ValueManipulator):
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

    def get_extractor(self) -> ValueExtractor:
        raise Exception("Method not implemented")

    def get_updator(self) -> ValueUpdater:
        raise Exception("Method not implemented")


@proxy("processor.NumberMultiplier")
class NumberMultiplier(PropertyProcessor):
    """
    NumberMultiplier entry processor.
    """

    def __init__(self, name_or_manipulator: ValueManipulator | str, multiplier: int, post_multiplication: bool = False):
        """
        Construct an NumberMultiplier processor that will multiply a property value by a specified factor,
        returning either the old or the new value as specified.

        :param name_or_manipulator: the ValueManipulator or the property name
        :param multiplier: the Number representing the magnitude and sign of the multiplier
        :param post_multiplication: pass true to return the value as it was before it was multiplied, or pass false
         to return the value as it is after it is multiplied
        """
        if type(name_or_manipulator) == str:
            manipulator = self.create_custom_manipulator(name_or_manipulator)
            super().__init__(manipulator)
        else:
            super().__init__(name_or_manipulator)
        self.multiplier = multiplier
        self.postMultiplication = post_multiplication

    @staticmethod
    def create_custom_manipulator(name_or_manipulator: str) -> ValueManipulator:
        cu = CompositeUpdater(UniversalExtractor(name_or_manipulator), UniversalUpdater(name_or_manipulator))
        return cu


@proxy("processor.NumberIncrementor")
class NumberIncrementor(PropertyProcessor):
    """
    The NumberIncrementor entry processor is used to increment a property value of a numeric type.
    """

    def __init__(self, name_or_manipulator: ValueManipulator | str, increment: int, post_increment: bool = False):
        """
        Construct an NumberIncrementor processor that will increment a property value by a specified amount,
        returning either the old or the new value as specified.

        :param name_or_manipulator: the ValueManipulator or property name
        :param increment: the Number representing the magnitude and sign of the increment
        :param post_increment: pass `true` to return the value as it was before it was incremented, or `pass` false
         to return the value as it is after it is incremented
        """
        if type(name_or_manipulator) == str:
            manipulator = self.create_custom_manipulator(name_or_manipulator)
            super().__init__(manipulator)
        else:
            super().__init__(name_or_manipulator)
        self.increment = increment
        self.postInc = post_increment

    @staticmethod
    def create_custom_manipulator(name_or_manipulator: str) -> ValueManipulator:
        cu = CompositeUpdater(UniversalExtractor(name_or_manipulator), UniversalUpdater(name_or_manipulator))
        return cu


@proxy("processor.ConditionalPut")
@mappings({"return_": "return"})
class ConditionalPut(EntryProcessor):
    """
    `ConditionalPut` is an EntryProcessor that performs an update operation for an entry that satisfies the specified
    condition.

    While the `ConditionalPut` processing could be implemented via direct key-based NamedMap operations, it is more
    efficient and enforces concurrency control without explicit locking.

    Obviously, using more specific, fine-tuned filters (rather than ones based on the IdentityExtractor) may provide
    additional flexibility and efficiency allowing the put operation to be performed conditionally on values of
    specific attributes (or even calculations) instead of the entire object.
    """

    def __init__(self, filter: Filter, value: V, return_value: bool = True):
        """
        Construct a ConditionalPut that updates an entry with a new value if and only if the filter applied to the
        entry evaluates to true. The result of the invocation does not return any result.

        :param filter: the filter to evaluate an entry
        :param value: a value to update an entry with
        :param return_value: specifies whether or not the processor should return the current value in case it has
         not been updated
        """
        super().__init__()
        self.filter = filter
        self.value = value
        self.return_ = return_value


@proxy("processor.ConditionalPutAll")
class ConditionalPutAll(EntryProcessor):
    """
    ConditionalPutAll is an EntryProcessor that performs an update operation for multiple entries that satisfy the
    specified condition.

    This allows for concurrent insertion/update of values within the cache.

    :Example:

        For example a concurrent `replaceAll(map)` could be implemented as:

            >>> filter = PresentFilter.INSTANCE
            >>> cache.invokeAll(map.keys(), ConditionalPutAll(filter, map))

        or `putAllIfAbsent` could be done by inverting the filter:

            >>> filter = NotFilter(PresentFilter.INSTANCE)


    Obviously, using more specific, fine-tuned filters may provide additional flexibility and efficiency allowing the
    multi-put operations to be performed conditionally on values of specific attributes (or even calculations)
    instead of a simple existence check.
    """

    def __init__(self, filter: Filter, the_map: dict[K, V]):
        """
        Construct a ConditionalPutAll processor that updates an entry with a new value if and only if the filter
        applied to the entry evaluates to true. The new value is extracted from the specified map based on the
        entry's key.

        :param filter: the filter to evaluate all supplied entries
        :param the_map: a map of values to update entries with
        """
        super().__init__()
        self.filter = filter
        self.entries = the_map


@proxy("processor.ConditionalRemove")
@mappings({"return_": "return"})
class ConditionalRemove(EntryProcessor):
    """
    ConditionalRemove is an EntryProcessor that performs an remove operation if the specified condition is satisfied.

    While the ConditionalRemove processing could be implemented via direct key-based NamedMap operations, it is more
    efficient and enforces concurrency control without explicit locking.
    """

    def __init__(self, filter: Filter, return_value: bool = True):
        """
        Construct a ConditionalRemove processor that removes an NamedMap entry if and only if the filter applied to
        the entry evaluates to `true`. The result of the invocation does not return any result.

        :param filter: the filter to evaluate an entry
        :param return_value: specifies whether or not the processor should return the current value if it has not
         been removed
        """
        super().__init__()
        self.filter = filter
        self.return_ = return_value


@proxy("processor.MethodInvocationProcessor")
class MethodInvocationProcessor(EntryProcessor):
    """
    An entry processor that invokes the specified method on a value of a cache entry and optionally updates the entry
    with a modified value.
    """

    def __init__(self, method_name: str, mutator: bool, *args: Any):
        """
        Construct MethodInvocationProcessor instance.

        :param method_name: the name of the method to invoke
        :param mutator: the flag specifying whether the method mutates the state of a target object, which implies
         that the entry value should be updated after method invocation
        :param args: the method arguments
        """
        super().__init__()
        self.methodName = method_name
        self.mutator = mutator
        self.args = list()
        for arg in args:
            self.args.append(arg)

    @classmethod
    def create(cls, method_name: str, mutator: bool, *args: Any) -> MethodInvocationProcessor:
        """
        Class method to Construct MethodInvocationProcessor instance.

        :param method_name: the name of the method to invoke
        :param mutator: the flag specifying whether the method mutates the state of a target object, which implies
         that the entry value should be updated after method invocation
        :param args: the method arguments
        :return: an instance of MethodInvocationProcessor
        """
        return cls(method_name, mutator, *args)


@proxy("processor.TouchProcessor")
class TouchProcessor(EntryProcessor):
    """
    Touches an entry (if present) in order to trigger interceptor re-evaluation and possibly increment expiry time.
    """

    def __init__(self) -> None:
        """
        Construct a `TouchProcessor`
        """
        super().__init__()

    @classmethod
    def create(cls) -> TouchProcessor:
        """
        Class method to construct a `TouchProcessor`

        :return: an instance of `TouchProcessor`
        """
        return cls()


@proxy("processor.ScriptProcessor")
class ScriptProcessor(EntryProcessor):
    """
    ScriptProcessor wraps a script written in one of the languages supported by Graal VM.
    """

    def __init__(self, name: str, language: str, *args: Any):
        """
        Create a :func:`coherence.processor.ScriptProcessor` that wraps a script written in the specified language
        and identified by the specified name. The specified args will be passed during execution of the script.

        :param name: the name of the :func:`coherence.processor.EntryProcessor` that needs to be executed
        :param language: the language the script is written. Currently, only `js` (for JavaScript) is supported
        :param args: the arguments to be passed to the :func:`coherence.processor.EntryProcessor`
        """
        super().__init__()
        self.name = name
        self.language = language
        self.args = list()
        for arg in args:
            self.args.append(arg)

    @classmethod
    def create(cls, name: str, language: str, *args: Any) -> ScriptProcessor:
        """
        Class method to create an instance of :func:`coherence.processor.ScriptProcessor`

        :param name: the name of the :func:`coherence.processor.EntryProcessor` that needs to be executed
        :param language: the language the script is written. Currently, only `js` (for JavaScript) is supported
        :param args: the arguments to be passed to the :func:`coherence.processor.EntryProcessor`
        :return:
        """
        return cls(name, language, *args)


@proxy("processor.PreloadRequest")
class PreloadRequest(EntryProcessor):
    """
    PreloadRequest is a simple EntryProcessor that performs a get call. No results are reported back to the caller.

    The PreloadRequest process provides a means to "pre-load" an entry or a collection of entries into the cache
    using the cache loader without incurring the cost of sending the value(s) over the network. If the corresponding
    entry (or entries) already exists in the cache, or if the cache does not have a loader, then invoking this
    EntryProcessor has no effect.
    """

    def __init__(self) -> None:
        """
        Construct a PreloadRequest EntryProcessor.
        """
        super().__init__()

    @classmethod
    def create(cls) -> PreloadRequest:
        """
        Class method to create an instance of PreloadRequest EntryProcessor

        :return: an instance of PreloadRequest EntryProcessor
        """
        return cls()


@proxy("processor.UpdaterProcessor")
class UpdaterProcessor(EntryProcessor):
    """
    UpdaterProcessor is an EntryProcessor implementations that updates an attribute of an object cached in an
    InvocableMap.

    While it's possible to update a value via standard Map API, using the updater allows for clustered caches using
    the UpdaterProcessor allows avoiding explicit concurrency control and could significantly reduce the amount of
    network traffic.
    """

    def __init__(self, updater_or_property_name: ValueUpdater | str, value: V):
        """
        Construct an `UpdaterProcessor` based on the specified ValueUpdater.

        :param updater_or_property_name: a ValueUpdater object or the method name; passing null will simpy replace
         the entry's value with the specified one instead of updating it
        :param value: the value to update the target entry with
        """
        super().__init__()
        if type(updater_or_property_name) == str:
            if updater_or_property_name.find(".") == -1:
                self.updater: ValueUpdater | str = UniversalUpdater(updater_or_property_name)
            else:
                self.updater = CompositeUpdater(updater_or_property_name)
        else:
            self.updater = updater_or_property_name
        self.value = value

    @classmethod
    def create(cls, updater_or_property_name: ValueUpdater | str, value: Any) -> UpdaterProcessor:
        """
        Class method to construct an `UpdaterProcessor` based on the specified ValueUpdater.

        :param updater_or_property_name: a ValueUpdater object or the method name; passing null will simpy replace
         the entry's value with the specified one instead of updating it
        :param value: the value to update the target entry with
        :return: an instance of an `UpdaterProcessor`
        """
        return cls(updater_or_property_name, value)


@proxy("processor.VersionedPut")
@mappings({"return_": "return"})
class VersionedPut(EntryProcessor):
    """
    `VersionedPut` is an :func:`coherence.processor.EntryProcessor` that assumes that entry values are versioned (see
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
        :param allow_insert: specifies whether or not an insert should be allowed (no currently existing value)
        :param return_current: specifies whether or not the processor should return the current value in case it has
         not been updated
        """
        super().__init__()
        self.value = value
        self.allowInsert = allow_insert
        self.return_ = return_current

    @classmethod
    def create(cls, value: Any, allow_insert: bool = False, return_current: bool = False) -> VersionedPut:
        """
        Class method to construct a `VersionedPut`

        :param value: a value to update an entry with
        :param allow_insert: specifies whether or not an insert should be allowed (no currently existing value)
        :param return_current: specifies whether or not the processor should return the current value in case it has
         not been updated
        :return: an instance of `VersionedPut`
        """
        return cls(value, allow_insert, return_current)


@proxy("processor.VersionedPutAll")
@mappings({"return_": "return"})
class VersionedPutAll(EntryProcessor):
    """
    `VersionedPutAll` is an :func:`coherence.processor.EntryProcessor` that assumes that entry values are versioned (
    see Coherence Versionable interface for details) and performs an update/insert operation only for entries whose
    versions match to versions of the corresponding current values. In case of the match, the `VersionedPutAll` will
    increment the version indicator before each value is updated.
    """

    def __init__(self, the_map: dict[K, V], allow_insert: bool = False, return_current: bool = False):
        """
        Construct a VersionedPutAll processor that updates an entry with a new value if and only if the version of
        the new value matches to the version of the current entry's value (which must exist). This processor
        optionally returns a map of entries that have not been updated (the versions did not match).

        :param the_map: a map of values to update entries with
        :param allow_insert: specifies whether or not an insert should be allowed (no currently existing value)
        :param return_current: specifies whether or not the processor should return the current value in case it has
         not been updated
        """
        super().__init__()
        self.entries = the_map
        self.allowInsert = allow_insert
        self.return_ = return_current

    @classmethod
    def create(cls, the_map: dict[K, V], allow_insert: bool = False, return_current: bool = False) -> VersionedPutAll:
        """
        Class method to construct a VersionedPutAll processor

        :param the_map: a map of values to update entries with
        :param allow_insert: specifies whether or not an insert should be allowed (no currently existing value)
        :param return_current: specifies whether or not the processor should return the current value in case it has
        :return: an instance of VersionedPutAll processor
        """
        return cls(the_map, allow_insert, return_current)


def extract(method_or_field: str) -> EntryProcessor:
    return ExtractorProcessor(method_or_field)
