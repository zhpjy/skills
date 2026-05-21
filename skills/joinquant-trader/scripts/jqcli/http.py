from __future__ import annotations

import json
from dataclasses import dataclass
from http.cookiejar import Cookie, CookieJar
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener

from jqcli.session import SessionState


class JoinQuantHttpError(Exception):
    pass


@dataclass
class HttpResponse:
    status: int
    url: str
    headers: dict[str, str]
    text: str

    def json_or_none(self) -> Any | None:
        try:
            return json.loads(self.text)
        except json.JSONDecodeError:
            return None


class JoinQuantHttpClient:
    def __init__(self, base_url: str, session: SessionState | None = None):
        self.base_url = base_url.rstrip("/")
        self.cookie_jar = CookieJar()
        self.set_session(session or SessionState())
        self.opener = build_opener(HTTPCookieProcessor(self.cookie_jar))

    def set_session(self, session: SessionState) -> None:
        self.cookie_jar.clear()
        for name, value in session.cookies.items():
            self.cookie_jar.set_cookie(_make_cookie(name, value))

    def get_session(self, token: str | None = None) -> SessionState:
        cookies = {cookie.name: cookie.value for cookie in self.cookie_jar}
        return SessionState(cookies=cookies, token=token)

    def get_cookie_value(self, name: str) -> str | None:
        for cookie in self.cookie_jar:
            if cookie.name == name:
                return cookie.value
        return None

    def get(self, path: str, params: dict[str, object] | None = None) -> HttpResponse:
        url = self._url(path, params)
        request = Request(url, headers=self._headers())
        return self._open(request)

    def post_form(
        self,
        path: str,
        data: dict[str, object],
        params: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
    ) -> HttpResponse:
        body = urlencode(data).encode("utf-8")
        request = Request(
            self._url(path, params),
            data=body,
            headers={
                **self._headers(),
                **(headers or {}),
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            },
            method="POST",
        )
        return self._open(request)

    def _url(self, path: str, params: dict[str, object] | None = None) -> str:
        url = f"{self.base_url}/{path.lstrip('/')}"
        if params:
            url = f"{url}?{urlencode(params)}"
        return url

    def _headers(self) -> dict[str, str]:
        return {
            "User-Agent": "jqcli/0.1",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Origin": self.base_url,
            "X-Requested-With": "XMLHttpRequest",
        }

    def _open(self, request: Request) -> HttpResponse:
        try:
            with self.opener.open(request, timeout=30) as response:
                body = response.read().decode("utf-8", "replace")
                return HttpResponse(
                    status=response.status,
                    url=response.url,
                    headers=dict(response.headers.items()),
                    text=body,
                )
        except HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")
            return HttpResponse(status=exc.code, url=exc.url, headers=dict(exc.headers.items()), text=body)
        except URLError as exc:
            raise JoinQuantHttpError(str(exc)) from exc


def _make_cookie(name: str, value: str) -> Cookie:
    return Cookie(
        version=0,
        name=name,
        value=value,
        port=None,
        port_specified=False,
        domain="www.joinquant.com",
        domain_specified=True,
        domain_initial_dot=False,
        path="/",
        path_specified=True,
        secure=False,
        expires=None,
        discard=True,
        comment=None,
        comment_url=None,
        rest={},
        rfc2109=False,
    )
