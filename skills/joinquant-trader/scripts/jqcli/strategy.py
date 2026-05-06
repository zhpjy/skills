from __future__ import annotations

import base64
import html
import json
import re
from typing import Any, Callable
from urllib.parse import parse_qs, urlparse


class StrategyService:
    def __init__(self, http_client, token_provider: Callable[[], str | None] = lambda: None):
        self.http_client = http_client
        self.token_provider = token_provider

    def list_strategies(self, folder_id: str = "0") -> list[dict[str, Any]]:
        response = self.http_client.get("/algorithm/index/list", params={"fId": folder_id})
        return parse_strategy_list(response.text)

    def list_directories(self, parent_id: str = "0") -> list[dict[str, Any]]:
        response = self.http_client.get("/algorithm/index/list", params={"fId": parent_id})
        return parse_directory_list(response.text)

    def create_directory(self, *, name: str, parent_id: str = "0") -> dict[str, Any]:
        token = self._list_page_token(parent_id) or self.token_provider() or ""
        response = self.http_client.post_form(
            "/algorithm/index/AddFile",
            {"token": token, "name": name, "ajax": 1},
            params={"pId": parent_id, "ajax": 1},
            headers={"Referer": self._list_referer(parent_id)},
        )
        return {"name": name, "parent_id": parent_id, "raw": _json_or_text(response.text)}

    def delete_directory(self, *, directory_id: str, parent_id: str = "0") -> dict[str, Any]:
        token = self.token_provider() or ""
        response = self.http_client.post_form(
            "/algorithm/index/DelFile",
            {"undefined": "", "ajax": 1, "token": token},
            params={"fId": directory_id, "ajax": 1},
            headers={"Referer": self._list_referer(parent_id)},
        )
        return {"directory_id": directory_id, "parent_id": parent_id, "raw": _json_or_text(response.text)}

    def get_strategy(self, strategy_id: str) -> dict[str, Any]:
        response = self.http_client.get(
            "/algorithm/index/edit",
            params={"algorithmId": strategy_id},
        )
        return parse_strategy_detail(response.text, strategy_id=strategy_id)

    def create_strategy(
        self,
        *,
        name: str,
        code: str,
        start_date: str,
        end_date: str,
        capital: str,
        frequency: str,
        strategy_type: str = "stock",
    ) -> dict[str, Any]:
        response = self.http_client.get(
            "/algorithm/index/new",
            params={"restore": 0, "type": strategy_type, "baseCapital": capital},
        )
        strategy_id = extract_strategy_id_from_new_response(response.url, response.text)
        if not strategy_id:
            return {"strategy_id": None, "raw": response.text, "warnings": ["strategy_id_not_found"]}
        save_result = self.save_strategy(
            strategy_id,
            name=name,
            code=code,
            start_date=start_date,
            end_date=end_date,
            capital=capital,
            frequency=frequency,
        )
        return {"strategy_id": strategy_id, "save": save_result}

    def save_strategy(
        self,
        strategy_id: str,
        *,
        name: str | None = None,
        code: str | None = None,
        start_date: str = "2019-01-01",
        end_date: str = "2019-06-30",
        capital: str = "100000",
        frequency: str = "day",
    ) -> dict[str, Any]:
        strategy = self.get_strategy(strategy_id)
        payload = build_strategy_save_payload(
            strategy,
            name=name or strategy.get("name") or "",
            code=code if code is not None else strategy.get("code") or "",
            start_date=start_date,
            end_date=end_date,
            capital=capital,
            frequency=frequency,
        )
        response = self.http_client.post_form(
            "/algorithm/index/save",
            payload,
            params={"ajax": 1},
            headers={"Referer": self._edit_referer(strategy_id)},
        )
        return {"strategy_id": strategy.get("id") or strategy_id, "raw": _json_or_text(response.text)}

    def rename_strategy(self, strategy_id: str, name: str) -> dict[str, Any]:
        strategy = self.get_strategy(strategy_id)
        token = _metadata_value(strategy, "token") or ""
        response = self.http_client.post_form(
            "/algorithm/index/setName",
            {"algorithmId": strategy.get("id") or strategy_id, "name": name, "ajax": 1, "token": token},
            params={"ajax": 1},
            headers={"Referer": self._edit_referer(strategy_id)},
        )
        return {"strategy_id": strategy.get("id") or strategy_id, "name": name, "raw": _json_or_text(response.text)}

    def delete_strategy(self, strategy_id: str) -> dict[str, Any]:
        strategy = self.get_strategy(strategy_id)
        token = _metadata_value(strategy, "token") or ""
        response = self.http_client.post_form(
            "/algorithm/index/del",
            {"algorithmId": strategy.get("id") or strategy_id, "ajax": 1, "token": token},
            params={"ajax": 1},
            headers={"Referer": f"{self.http_client.base_url}/algorithm/index/list"},
        )
        return {"strategy_id": strategy.get("id") or strategy_id, "raw": _json_or_text(response.text)}

    def _edit_referer(self, strategy_id: str) -> str:
        return f"{self.http_client.base_url}/algorithm/index/edit?algorithmId={strategy_id}"

    def _list_referer(self, folder_id: str = "0") -> str:
        return f"{self.http_client.base_url}/algorithm/index/list?fId={folder_id}"

    def _list_page_token(self, folder_id: str = "0") -> str | None:
        response = self.http_client.get("/algorithm/index/list", params={"fId": folder_id})
        return _extract_token_data(response.text) or _extract_token(response.text)


def parse_strategy_list(text: str) -> list[dict[str, Any]]:
    parsed = _json_or_none(text)
    if parsed is not None:
        return _parse_strategy_list_json(parsed)
    return _parse_strategy_list_html(text)


def parse_directory_list(text: str) -> list[dict[str, Any]]:
    parsed = _json_or_none(text)
    if parsed is not None:
        return _parse_directory_list_json(parsed)
    return _parse_directory_list_html(text)


def parse_strategy_detail(text: str, strategy_id: str) -> dict[str, Any]:
    parsed = _json_or_none(text)
    if parsed is not None:
        detail = _parse_strategy_detail_json(parsed, strategy_id)
    else:
        detail = _parse_strategy_detail_html(text, strategy_id)
    if detail.get("code") is None:
        detail.setdefault("warnings", []).append("code_not_found")
    return detail


def extract_strategy_id_from_url(url: str) -> str | None:
    query = parse_qs(urlparse(url).query)
    values = query.get("algorithmId")
    return values[0] if values else None


def extract_strategy_id_from_new_response(url: str, text: str) -> str | None:
    direct = extract_strategy_id_from_url(url)
    if direct:
        return direct
    parsed = _json_or_none(text)
    if isinstance(parsed, dict) and isinstance(parsed.get("redirect"), str):
        return extract_strategy_id_from_url(parsed["redirect"])
    return None


def build_strategy_save_payload(
    strategy: dict[str, Any],
    *,
    name: str,
    code: str,
    start_date: str,
    end_date: str,
    capital: str,
    frequency: str,
) -> dict[str, str]:
    metadata = strategy.get("metadata") if isinstance(strategy.get("metadata"), dict) else {}
    return {
        "algorithm[algorithmId]": str(strategy.get("id") or ""),
        "algorithm[userId]": str(metadata.get("userId") or ""),
        "algorithm[accessControl]": str(metadata.get("accessControl") or "0"),
        "backtest[type]": str(metadata.get("backtestType") or "1"),
        "algorithm[name]": name,
        "fontpref": str(metadata.get("fontpref") or "default"),
        "themepref": str(metadata.get("themepref") or "ambiance"),
        "algorithm[code]": base64.b64encode(code.encode("utf-8")).decode("ascii"),
        "backtest[startTime]": start_date,
        "backtest[endTime]": end_date,
        "backtest[baseCapital]": str(capital),
        "backtest[frequency]": frequency,
        "backtest[pyVersion]": str(metadata.get("pyVersion") or "3"),
        "encrType": "base64",
        "ajax": "1",
        "token": str(metadata.get("token") or ""),
    }


def _parse_strategy_list_json(parsed: Any) -> list[dict[str, Any]]:
    items = _find_first_list(parsed)
    result = []
    for item in items:
        if not isinstance(item, dict):
            continue
        strategy_id = _first_value(item, "algorithmId", "id", "strategyId")
        if strategy_id is None:
            continue
        result.append(
            {
                "id": str(strategy_id),
                "name": _first_value(item, "name", "algorithmName", "title"),
                "updated_at": _first_value(item, "updateTime", "updated_at", "modifyTime"),
            }
        )
    return result


def _parse_strategy_list_html(text: str) -> list[dict[str, Any]]:
    result = []
    seen = set()
    pattern = re.compile(
        r'<a[^>]+href=["\'][^"\']*algorithmId=([A-Za-z0-9_.:-]+)[^"\']*["\'][^>]*>(.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )
    for match in pattern.finditer(text):
        strategy_id = match.group(1)
        if strategy_id in seen:
            continue
        seen.add(strategy_id)
        name = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", match.group(2))).strip()
        result.append({"id": strategy_id, "name": html.unescape(name), "updated_at": None})
    return result


def _parse_directory_list_json(parsed: Any) -> list[dict[str, Any]]:
    items = _find_first_list(parsed)
    result = []
    for item in items:
        if not isinstance(item, dict):
            continue
        directory_id = _first_value(item, "fId", "fileId", "folderId", "id")
        if directory_id is None:
            continue
        result.append({"id": str(directory_id), "name": _first_value(item, "name", "fileName", "folderName", "title")})
    return result


def _parse_directory_list_html(text: str) -> list[dict[str, Any]]:
    result = []
    seen = set()
    pattern = re.compile(
        r'<a[^>]+href=["\'][^"\']*algorithm/index/list\?fId=([A-Za-z0-9_.:-]+)[^"\']*["\'][^>]*>(.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )
    for match in pattern.finditer(text):
        directory_id = match.group(1)
        if directory_id in seen:
            continue
        seen.add(directory_id)
        name = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", match.group(2))).strip()
        result.append({"id": directory_id, "name": html.unescape(name)})
    return result


def _parse_strategy_detail_json(parsed: Any, strategy_id: str) -> dict[str, Any]:
    if _is_remote_error(parsed):
        return {
            "id": strategy_id,
            "name": None,
            "code": None,
            "metadata": {
                "remote_status": parsed.get("status"),
                "remote_code": parsed.get("code"),
                "remote_message": parsed.get("msg") or parsed.get("message"),
                "remote_reason": parsed.get("reason"),
            },
            "warnings": ["remote_error"],
        }
    algorithm = _find_algorithm_dict(parsed) or {}
    metadata = {key: value for key, value in algorithm.items() if key != "code"}
    return {
        "id": str(_first_value(algorithm, "algorithmId", "id", default=strategy_id)),
        "name": _first_value(algorithm, "name", "algorithmName", "title"),
        "code": _first_value(algorithm, "code", "algorithmCode"),
        "metadata": metadata,
        "warnings": [],
    }


def _parse_strategy_detail_html(text: str, strategy_id: str) -> dict[str, Any]:
    code = _extract_html_code(text)
    form_values = _extract_form_values(text)
    name = _extract_html_name(text) or form_values.get("algorithm[name]")
    metadata = _metadata_from_form_values(form_values)
    token = _extract_token_data(text)
    if token:
        metadata["token"] = token
    return {
        "id": form_values.get("algorithm[algorithmId]") or strategy_id,
        "name": name,
        "code": code,
        "metadata": metadata,
        "warnings": [],
    }


def _extract_html_code(text: str) -> str | None:
    for pattern in (
        r'name=["\']algorithm\[code\]["\'][^>]*>(.*?)</textarea>',
        r'id=["\']code["\'][^>]*>(.*?)</textarea>',
        r'"code"\s*:\s*"((?:\\.|[^"])*)"',
    ):
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            value = match.group(1)
            try:
                return json.loads(f'"{value}"') if "\\" in value else html.unescape(value)
            except json.JSONDecodeError:
                return html.unescape(value)
    return None


def _extract_html_name(text: str) -> str | None:
    match = re.search(r'name=["\']algorithm\[name\]["\'][^>]*value=["\']([^"\']+)', text)
    return html.unescape(match.group(1)) if match else None


def _extract_form_values(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    input_pattern = re.compile(r'<input\b([^>]*)>', re.IGNORECASE | re.DOTALL)
    for match in input_pattern.finditer(text):
        attrs = _parse_attrs(match.group(1))
        name = attrs.get("name")
        if name:
            values[name] = attrs.get("value", "")
    textarea_pattern = re.compile(
        r'<textarea\b([^>]*)>(.*?)</textarea>',
        re.IGNORECASE | re.DOTALL,
    )
    for match in textarea_pattern.finditer(text):
        attrs = _parse_attrs(match.group(1))
        name = attrs.get("name")
        if name:
            values[name] = html.unescape(match.group(2))
    return values


def _parse_attrs(text: str) -> dict[str, str]:
    attrs = {}
    for match in re.finditer(r'([A-Za-z0-9_:\[\]-]+)=["\']([^"\']*)["\']', text):
        attrs[match.group(1)] = html.unescape(match.group(2))
    return attrs


def _metadata_from_form_values(values: dict[str, str]) -> dict[str, str]:
    mapping = {
        "algorithm[userId]": "userId",
        "algorithm[accessControl]": "accessControl",
        "backtest[type]": "backtestType",
        "fontpref": "fontpref",
        "themepref": "themepref",
        "backtest[pyVersion]": "pyVersion",
        "encrType": "encrType",
    }
    return {target: values[source] for source, target in mapping.items() if source in values}


def _extract_token_data(text: str) -> str | None:
    match = re.search(
        r"window\.tokenData\s*=\s*\{.*?value\s*:\s*[\"']([^\"']+)[\"']",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    return match.group(1) if match else None


def _extract_token(text: str) -> str | None:
    for pattern in (
        r'["\']token["\']\s*:\s*["\']([^"\']+)["\']',
        r'token=([A-Za-z0-9_.:-]+)',
        r'name=["\']token["\'][^>]+value=["\']([^"\']+)["\']',
    ):
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1)
    return None


def _json_or_none(text: str) -> Any | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _find_first_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("data", "list", "items", "rows"):
            child = value.get(key)
            if isinstance(child, list):
                return child
            if isinstance(child, dict):
                found = _find_first_list(child)
                if found:
                    return found
        for child in value.values():
            found = _find_first_list(child)
            if found:
                return found
    return []


def _find_algorithm_dict(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        algorithm = value.get("algorithm")
        if isinstance(algorithm, dict):
            return algorithm
        if any(key in value for key in ("algorithmId", "algorithmCode")) or (
            "code" in value and ("name" in value or "algorithmName" in value)
        ):
            return value
        for child in value.values():
            found = _find_algorithm_dict(child)
            if found is not None:
                return found
    if isinstance(value, list):
        for child in value:
            found = _find_algorithm_dict(child)
            if found is not None:
                return found
    return None


def _first_value(mapping: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value is not None:
            return value
    return default


def _is_remote_error(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    if "msg" not in value and "message" not in value:
        return False
    status = str(value.get("status") or "")
    code = str(value.get("code") or "")
    return status not in {"", "0", "1", "true", "success"} or bool(code and "algorithm" not in value)


def _metadata_value(strategy: dict[str, Any], key: str) -> Any:
    metadata = strategy.get("metadata") if isinstance(strategy.get("metadata"), dict) else {}
    return metadata.get(key)


def _json_or_text(text: str) -> Any:
    parsed = _json_or_none(text)
    return parsed if parsed is not None else text
