# Portfolio excerpt, adapted.
"""Dataclass (de)serialization that keeps field order stable and coerces nested types on the way back.

Field order is preserved so serialized output produces clean Git diffs. Coercion
walks the runtime type hints to rebuild nested dataclasses, enums, and containers,
since a plain dict round-trip would otherwise hand back raw dicts and strings.
Stdlib only.
"""

from __future__ import annotations

import dataclasses
import enum
import types
import typing
from typing import Any, cast, get_args, get_origin, get_type_hints

_NONE_TYPE = type(None)


def _is_dataclass_type(tp: Any) -> bool:
    return isinstance(tp, type) and dataclasses.is_dataclass(tp)


def _unwrap_optional(tp: Any) -> tuple[Any, bool]:
    """Return (inner, was_optional) for Optional[T] / T | None, else (tp, False)."""
    origin = get_origin(tp)
    if origin is typing.Union or origin is types.UnionType:
        args = [a for a in get_args(tp) if a is not _NONE_TYPE]
        optional = _NONE_TYPE in get_args(tp)
        # only collapse single-arg unions; a real multi-type union we can't coerce, leave as-is
        if len(args) == 1:
            return args[0], optional
        return tp, optional
    return tp, False


def to_jsonable(value: Any) -> Any:
    """Return value reduced to JSON/YAML-safe primitives, recursing through dataclasses and containers."""
    if isinstance(value, Serializable):
        return value.to_dict()
    # bare dataclass without the mixin; exclude the class object itself
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: to_jsonable(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, dict):
        return {k: to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        # tuples become lists; JSON has no tuple and _from_value puts them back on the way in
        return [to_jsonable(v) for v in value]
    return value


def _from_value(tp: Any, value: Any) -> Any:
    """Coerce value to tp using runtime hints, handling None, enums, dataclasses, and generic containers."""
    if value is None:
        return None

    inner, _optional = _unwrap_optional(tp)
    origin = get_origin(inner)

    if _is_dataclass_type(inner) and isinstance(value, dict):
        if issubclass(inner, Serializable):
            return inner.from_dict(value)
        return _generic_from_dict(inner, value)

    if isinstance(inner, type) and issubclass(inner, enum.Enum):
        if isinstance(value, inner):
            return value
        return inner(value)

    if origin in (list, tuple):
        (elem_tp,) = get_args(inner) or (Any,)
        seq = [_from_value(elem_tp, v) for v in value]
        return tuple(seq) if origin is tuple else seq
    if origin is dict:
        args = get_args(inner)
        # coerce values only; dict keys come back from JSON as strings already
        val_tp = args[1] if len(args) == 2 else Any
        return {k: _from_value(val_tp, v) for k, v in value.items()}

    return value


def _generic_from_dict(cls: type, data: dict[str, Any]) -> Any:
    # fallback for dataclasses that don't inherit Serializable
    hints = get_type_hints(cls)
    kwargs: dict[str, Any] = {}
    field_names = {f.name for f in dataclasses.fields(cls)}
    for name in field_names:
        if name in data:
            kwargs[name] = _from_value(hints.get(name, Any), data[name])
    return cls(**kwargs)


class Serializable:
    """Mixin giving a dataclass dict round-trips with deterministic field order."""

    def to_dict(self) -> dict[str, Any]:
        """Return fields in declaration order with values reduced to primitives."""
        assert dataclasses.is_dataclass(self), "Serializable must wrap a dataclass"
        out: dict[str, Any] = {}
        for f in dataclasses.fields(self):
            out[f.name] = to_jsonable(getattr(self, f.name))
        return out

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> Any:
        """Rebuild an instance from a dict, coercing fields to their annotated types. Unknown keys are dropped."""
        if data is None:
            data = {}
        if not isinstance(data, dict):
            raise TypeError(f"{cls.__name__}.from_dict expected a mapping, got {type(data)!r}")
        hints = get_type_hints(cls)
        kwargs: dict[str, Any] = {}
        for f in dataclasses.fields(cast(Any, cls)):
            if f.name in data:
                kwargs[f.name] = _from_value(hints.get(f.name, Any), data[f.name])
        return cls(**kwargs)


__all__ = ["Serializable", "to_jsonable"]
