# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

import collections
import json
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Callable, Dict, Final, Optional, Type, TypeVar, cast

import jsonpickle

T = TypeVar("T", covariant=True)

_BIG_DEC_ALIAS: Final[str] = "math.BigDec"
_BIG_INT_ALIAS: Final[str] = "math.BigInt"

_META_CLASS: Final[str] = "@class"
_META_VERSION: Final[str] = "@version"
_META_ENUM: Final[str] = "enum"
_META_ORDERED: Final[str] = "@ordered"

_JSON_KEY = "key"
_JSON_VALUE = "value"
_JSON_ENTRIES = "entries"

_JSON_PICKLE_OBJ = "py/object"

MAGIC_BYTE: Final[bytes] = b"\x15"

_type_to_alias: Final[Dict[Type[Any], str]] = {}
"""A mapping of proxied Python types to their alias."""

_alias_to_type: Final[Dict[str, Type[Any]]] = {}
"""A mapping of aliases to their proxied Python type."""

_attribute_mappings: Final[Dict[Type[Any], Dict[str, str]]] = {}
"""A mapping of object attributes that require a different name when serialized/deserialized."""

_attribute_mappings_rev: Final[Dict[Type[Any], Dict[str, str]]] = {}
"""The same mapping as _attribute_mappings, but in reverse for deserialization."""


class Serializer(ABC):
    @abstractmethod
    def serialize(self, obj: object) -> bytes:
        """documentation"""

    @abstractmethod
    def deserialize(self, value: bytes) -> T:  # type: ignore
        """documentation"""

    @property
    def format(self) -> str:
        return self._ser_format

    def __init__(self, ser_format: str):
        self._ser_format = ser_format

    def __str__(self) -> str:
        return f"Serializer(format={self.format})"


class JSONSerializer(Serializer):
    SER_FORMAT = "json"

    def __init__(self) -> None:
        super().__init__(JSONSerializer.SER_FORMAT)
        self._pickler = JavaProxyPickler()
        self._unpickler = JavaProxyUnpickler()

    def _to_json_from_object(self, obj: object) -> str:
        jsn = jsonpickle.encode(obj, context=self._pickler)
        return jsn

    def serialize(self, obj: object) -> bytes:
        jsn: str = self._to_json_from_object(obj)
        b: bytes = MAGIC_BYTE + jsn.encode()
        return b

    def _to_object_from_json(self, json_str: str) -> T:  # type: ignore
        o = jsonpickle.decode(json_str, context=self._unpickler)
        return o

    def deserialize(self, value: bytes) -> T:  # type: ignore
        if isinstance(value, bytes):
            s = value.decode()
            if value.__len__() == 0:  # empty string
                return cast(T, None)
            else:
                if ord(s[0]) == ord(MAGIC_BYTE):
                    r: T = self._to_object_from_json(s[1:])
                    return r
                else:
                    raise ValueError("Invalid JSON serialization format")
        else:
            return cast(T, value)

    def flatten_to_dict(self, o: object) -> dict[Any, Any]:
        jsn = self._to_json_from_object(o)
        d = json.loads(jsn)
        return d

    def restore_to_object(self, the_dict: dict[Any, Any]) -> T:  # type: ignore
        jsn = json.dumps(the_dict)
        o: T = self._to_object_from_json(jsn)
        return o


class SerializerRegistry:
    _singleton: SerializerRegistry

    def __init__(self) -> None:
        self.serializers: dict[str, Serializer] = {JSONSerializer.SER_FORMAT: JSONSerializer()}

    def __new__(cls) -> SerializerRegistry:
        if not hasattr(cls, "_singleton"):
            cls._singleton = super(SerializerRegistry, cls).__new__(cls)
        return cls._singleton

    @staticmethod
    def instance() -> SerializerRegistry:
        return SerializerRegistry()._singleton

    @staticmethod
    def serializer(ser_format: str) -> Serializer:
        s = SerializerRegistry.instance().serializers[ser_format]
        if s is not None:
            return s
        else:
            raise ValueError("No serializer registered for format: " + ser_format)


class JavaProxyPickler(jsonpickle.Pickler):
    MAX_NUMERIC: Final[int] = (2**63) - 1
    MIN_NUMERIC: Final[int] = (-(2**63)) - 1

    def __init__(self) -> None:
        super().__init__(make_refs=False)

    def _flatten(self, obj: Any) -> dict[str, str] | None | dict[str, Any] | Decimal:
        if isinstance(obj, int):
            if obj > self.MAX_NUMERIC or obj < self.MIN_NUMERIC:
                return {_META_CLASS: _BIG_INT_ALIAS, "value": str(obj)}

        if isinstance(obj, set):
            return super()._flatten(list(obj))

        return super()._flatten(obj)

    def _getstate(self, obj: Any, data: Any) -> Any:
        state = self._flatten(obj)

        if state is not None:
            data.update(state)

        return data

    def _flatten_obj(self, obj: Any) -> dict[str, str | dict[str, list[dict[str, Any]]]] | None:
        result = super()._flatten_obj(obj)
        object_type = type(obj)
        alias: Optional[str] = _alias_for(object_type)
        if alias is not None:
            marker = result.get(_JSON_PICKLE_OBJ, None)
            if marker is not None:
                actual: dict[str, Any] = {}
                actual[_META_CLASS] = alias
                for key, value in result.items():
                    # ignore jsonpickle specific content as well as protected keys
                    if key == _JSON_PICKLE_OBJ or str(key).startswith("_"):
                        continue

                    # store the original key/value pair as logic below may change them
                    key_ = key
                    value_ = value

                    # check for any attributes that need a different key name when serialized to JSON
                    mappings_ = _attribute_mappings.get(object_type, None)
                    if mappings_ is not None:
                        mapping = mappings_.get(key, None)
                        if mapping is not None:
                            key_ = mapping

                    # if the value being serialized is a dict, serialize it as a list of key/value pairs
                    if (
                        isinstance(value_, dict)
                        and _META_CLASS not in value_
                        and _META_VERSION not in value_
                        and _META_ENUM not in value_
                    ):
                        entries = []
                        for key_inner, value_inner in value.items():
                            entries.append({_JSON_KEY: key_inner, _JSON_VALUE: value_inner})

                        padding: dict[str, Any] = {}
                        padding["entries"] = entries
                        value_ = padding

                    actual[key_] = value_

                result = actual

        return result


@jsonpickle.handlers.register(Decimal)
class DecimalHandler(jsonpickle.handlers.BaseHandler):
    def flatten(self, obj: object, data: dict[str, Any]) -> dict[str, Any]:
        return {_META_CLASS: _BIG_DEC_ALIAS, _JSON_VALUE: str(obj)}

    def restore(self, obj: dict[str, Any]) -> Decimal:
        return Decimal(obj[_JSON_VALUE])


@jsonpickle.handlers.register(int)
class LargeIntHandler(jsonpickle.handlers.BaseHandler):
    def flatten(self, obj: object, data: dict[str, Any]) -> dict[str, Any]:
        return {_META_CLASS: _BIG_INT_ALIAS, _JSON_VALUE: str(obj)}

    def restore(self, obj: dict[str, Any]) -> int:
        return int(obj[_JSON_VALUE])


class JavaProxyUnpickler(jsonpickle.Unpickler):
    # noinspection PyUnresolvedReferences
    def _restore(self, obj: Any) -> Any:
        if isinstance(obj, dict):
            metadata: Any = obj.get(_META_CLASS, None)
            if metadata is not None:
                type_: Optional[Type[Any]] = _type_for(metadata)
                actual: dict[Any, Any] = {}
                if type_ is None:
                    if "map" in metadata.lower():
                        for entry in obj[_JSON_ENTRIES]:
                            actual[entry[_JSON_KEY]] = entry[_JSON_VALUE]
                    else:
                        return obj
                else:
                    type_name = jsonpickle.util.importable_name(type_)
                    actual[_JSON_PICKLE_OBJ] = type_name
                    rev_map = _attribute_mappings_rev.get(type_name, None)
                    for key, value in obj.items():
                        if key == _META_CLASS:
                            continue

                        key_ = rev_map.get(key, None) if rev_map is not None else None
                        actual[key_ if key_ is not None else key] = value

                return super().restore(actual, reset=False)

            # When "@Ordered" set to true which converts to OrderedDict()
            metadata = obj.get(_META_ORDERED, False)
            if metadata is True:
                o = collections.OrderedDict()
                entries = obj.get(_JSON_ENTRIES, None)
                if entries is not None:
                    for entry in obj[_JSON_ENTRIES]:
                        o[entry[_JSON_KEY]] = entry[_JSON_VALUE]
                return o

            #  When there is no "@Ordered" set. Only "entries" list exists
            if len(obj) == 1:
                entries = obj.get(_JSON_ENTRIES, None)
                if entries is not None:
                    actual = {}
                    for entry in obj[_JSON_ENTRIES]:
                        actual[entry[_JSON_KEY]] = entry[_JSON_VALUE]
                    return super().restore(actual, reset=False)

        return super()._restore(obj)


def _alias_for(handled_type: Type[Any]) -> Optional[str]:
    """
    Return the alias, if any, for the specified type.

    :param handled_type: the type to check
    :return: the alias for the type or `None`
    """
    return _type_to_alias.get(handled_type, None)


def _type_for(alias: str) -> Optional[Type[Any]]:
    """
    Return the type, if any, for the specified alias.

    :param alias: the alias to check
    :return: the type for the alias or `None`
    """
    return _alias_to_type.get(alias, None)


def _register(handled_type: Type[Any], alias: str) -> None:
    """
    Registers the specified type and alias.

    :param handled_type: the type
    :param alias: the alias for the type
    """
    _type_to_alias[handled_type] = alias
    _alias_to_type[alias] = handled_type


def _deregister(handled_type: Type[Any], alias: str) -> None:
    """
    De-registers the specified type and alias.

    :param handled_type: the type
    :param alias: the alias for the type
    """
    del _type_to_alias[handled_type]
    del _alias_to_type[alias]


def mappings(attributes: Dict[str, str]) -> Callable[[Type[Any]], Type[Any]]:
    # noinspection PyUnresolvedReferences
    def _do_register(type_: Type[Any]) -> Type[Any]:
        _attribute_mappings[type_] = attributes
        _attribute_mappings_rev[jsonpickle.util.importable_name(type_)] = {y: x for x, y in attributes.items()}

        return type_

    return _do_register


def proxy(alias: str) -> Callable[[Type[Any]], Type[Any]]:
    """A class-level decorator to mark a particular type as having a Java equivalent type known
    to Coherence.  This decorator accepts a string argument denoting the alias the known type.
    """

    def _do_register(type_: Type[Any]) -> Type[Any]:
        """
        Registers the type and its alias with the JSON serializer.  This information
        will be used when serializing/deserializing these types.

        :param type_: the Python type that has a corresponding Java type known to Coherence by the provided alias
        :return: `proxy_cls` as it was passed
        """
        _register(type_, alias)

        return type_

    return _do_register


_register(Decimal, _BIG_DEC_ALIAS)
_register(int, _BIG_INT_ALIAS)
