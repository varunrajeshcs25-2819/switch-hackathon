"""Helpers for turning loosely-typed model output into validated values."""

from enum import Enum
from typing import Any, List, Type, TypeVar

E = TypeVar("E", bound=Enum)


def coerce_enum(enum_cls: Type[E], value: Any, default: E) -> E:
    if isinstance(value, enum_cls):
        return value
    text = str(value or "").strip().lower().replace(" ", "_").replace("-", "_")
    for member in enum_cls:
        if member.value == text or member.name.lower() == text:
            return member
    return default


def as_str_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, (list, tuple)):
        return [str(v).strip() for v in value if str(v).strip()]
    return [str(value)]


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return default


def as_str(value: Any) -> str:
    return "" if value is None else str(value).strip()
