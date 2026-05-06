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

