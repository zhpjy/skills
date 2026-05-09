from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping


SENSITIVE_KEY_PATTERN = re.compile(
    r"(user|name|pass|pwd|token|cookie|session|csrf|auth|secret|key)",
    re.IGNORECASE,
)


class ConfigError(Exception):
    pass


def _default_state_dir() -> Path:
    return Path(__file__).resolve().parents[2] / ".state"


def _default_env_path() -> Path:
    return Path(__file__).resolve().parents[2] / ".env"


@dataclass(frozen=True)
class JoinQuantConfig:
    username: str
    password: str
    base_url: str = "https://www.joinquant.com"
    state_dir: Path = field(default_factory=_default_state_dir)


def load_config(env_path: Path | None = None) -> JoinQuantConfig:
    resolved_env_path = _resolve_env_path(env_path)
    values = _read_env_file(resolved_env_path)
    username = values.get("JOINQUANT_USERNAME") or os.environ.get("JOINQUANT_USERNAME") or ""
    password = values.get("JOINQUANT_PASSWORD") or os.environ.get("JOINQUANT_PASSWORD") or ""
    base_url = values.get("JOINQUANT_BASE_URL") or os.environ.get("JOINQUANT_BASE_URL") or "https://www.joinquant.com"
    state_dir_value = values.get("JOINQUANT_STATE_DIR") or os.environ.get("JOINQUANT_STATE_DIR")
    state_dir = Path(state_dir_value) if state_dir_value else _default_state_dir()
    if not username or not password:
        raise ConfigError("JOINQUANT_USERNAME and JOINQUANT_PASSWORD are required")
    return JoinQuantConfig(
        username=username,
        password=password,
        base_url=base_url.rstrip("/"),
        state_dir=state_dir,
    )


def redact_mapping(values: Mapping[str, object]) -> dict[str, object]:
    redacted: dict[str, object] = {}
    for key, value in values.items():
        if SENSITIVE_KEY_PATTERN.search(key):
            redacted[key] = "<redacted>"
        else:
            redacted[key] = value
    return redacted


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = _strip_quotes(value.strip())
    return values


def _resolve_env_path(env_path: Path | None) -> Path:
    if env_path is not None:
        return env_path
    explicit = os.environ.get("JQCLI_ENV_FILE")
    if explicit:
        return Path(explicit)
    return _default_env_path()


def _strip_quotes(value: str) -> str:
    quote_chars = (chr(39), chr(34))
    if len(value) >= 2 and value[0] == value[-1] and value[0] in quote_chars:
        return value[1:-1]
    return value
