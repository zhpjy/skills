from __future__ import annotations


class JqcliError(Exception):
    code = "ERROR"

    def __init__(self, message: str, detail: dict | None = None):
        super().__init__(message)
        self.message = message
        self.detail = detail or {}


class RemoteError(JqcliError):
    code = "HTTP_ERROR"


class ParseError(JqcliError):
    code = "PARSE_ERROR"

