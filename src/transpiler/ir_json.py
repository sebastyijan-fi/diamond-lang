"""JSON serialization helpers for Diamond IR with explicit node kinds."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any


def to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        out: dict[str, Any] = {"_kind": value.__class__.__name__}
        for f in fields(value):
            out[f.name] = to_jsonable(getattr(value, f.name))
        return out
    if isinstance(value, list):
        return [to_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: to_jsonable(v) for k, v in value.items()}
    return value
