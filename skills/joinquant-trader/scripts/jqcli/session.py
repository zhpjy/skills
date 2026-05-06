from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SessionState:
    cookies: dict[str, str] = field(default_factory=dict)
    token: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"cookies": self.cookies, "token": self.token}


def load_session(path: Path) -> SessionState:
    if not path.exists():
        return SessionState()
    data = json.loads(path.read_text(encoding="utf-8"))
    cookies = data.get("cookies") if isinstance(data, dict) else None
    token = data.get("token") if isinstance(data, dict) else None
    return SessionState(
        cookies=cookies if isinstance(cookies, dict) else {},
        token=token if isinstance(token, str) and token else None,
    )


def save_session(path: Path, state: SessionState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
