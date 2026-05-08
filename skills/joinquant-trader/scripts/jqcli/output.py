from __future__ import annotations

import json
from typing import Any


def success_response(data: Any) -> dict[str, Any]:
    return {"ok": True, "data": data}


def error_response(
    code: str,
    message: str,
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "detail": detail or {},
        },
    }


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def summarize_list(items: Any, *, sample_size: int = 5, item_mapper=None) -> dict[str, Any]:
    if not isinstance(items, list):
        return {"count": 0, "sample": [], "truncated": False}
    sample = items[:sample_size]
    if item_mapper is not None:
        sample = [item_mapper(item) for item in sample]
    return {
        "count": len(items),
        "sample": sample,
        "truncated": len(items) > sample_size,
    }


def compact_value(value: Any, *, sample_size: int = 5, max_depth: int = 2) -> Any:
    if _is_scalar(value):
        return value
    if isinstance(value, list):
        return summarize_list(
            value,
            sample_size=sample_size,
            item_mapper=lambda item: compact_value(item, sample_size=sample_size, max_depth=max_depth - 1),
        )
    if isinstance(value, dict):
        if max_depth <= 0:
            keys = list(value.keys())
            return {"count": len(keys), "keys": keys[:sample_size], "truncated": len(keys) > sample_size}
        return {
            key: compact_value(child, sample_size=sample_size, max_depth=max_depth - 1)
            for key, child in value.items()
        }
    return str(value)


def _is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))
