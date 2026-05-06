from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Protocol

from jqcli.config import JoinQuantConfig
from jqcli.session import SessionState


class AuthError(Exception):
    pass


class AuthClient(Protocol):
    def set_session(self, session: SessionState) -> None:
        ...

    def is_login(self) -> bool:
        ...

    def login(self, username: str, password: str) -> SessionState:
        ...


@dataclass
class AuthService:
    config: JoinQuantConfig
    client: AuthClient
    load_state: Callable[[], SessionState]
    save_state: Callable[[SessionState], None]

    def ensure_session(self) -> SessionState:
        state = self.load_state()
        self.client.set_session(state)
        if self.client.is_login():
            return state
        logged_in = self.client.login(self.config.username, self.config.password)
        if not logged_in.cookies:
            raise AuthError("Login failed or requires manual verification")
        self.save_state(logged_in)
        return logged_in


class JoinQuantAuthClient:
    def __init__(self, http_client):
        self.http_client = http_client
        self._token: str | None = None

    def set_session(self, session: SessionState) -> None:
        self._token = session.token
        self.http_client.set_session(session)

    def is_login(self) -> bool:
        params = {"token": self._token} if self._token else None
        response = self.http_client.get("/user/index/isLogin", params=params)
        if response.status >= 400:
            return False
        data = response.json_or_none()
        if isinstance(data, dict):
            return _truthy_login_value(data)
        text = response.text.strip().lower()
        return text in {"true", "1", "ok"} or '"islogin":true' in text.replace(" ", "")

    def login(self, username: str, password: str) -> SessionState:
        response = self.http_client.post_form(
            "/user/login/doLoginByText",
            {"username": username, "pwd": password},
        )
        if response.status >= 400:
            raise AuthError(f"Login HTTP status {response.status}")
        token = _extract_token(response.text)
        state = self.http_client.get_session(token=token)
        if not state.cookies:
            raise AuthError("Login failed or requires manual verification")
        return state


def _truthy_login_value(data: dict) -> bool:
    for key in ("isLogin", "is_login", "login", "loggedIn", "status", "success"):
        value = data.get(key)
        if value is True or value == 1:
            return True
        if isinstance(value, str) and value.lower() in {"true", "1", "ok", "success"}:
            return True
    return False


def _extract_token(text: str) -> str | None:
    for pattern in (
        r'"token"\s*:\s*"([^"]+)"',
        r"'token'\s*:\s*'([^']+)'",
        r"token=([A-Za-z0-9_.:-]+)",
    ):
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None
