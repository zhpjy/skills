from __future__ import annotations

import json
import base64
import re
import time
from typing import Any
from urllib.parse import parse_qs, urlparse
from jqcli.output import compact_value, summarize_list


class BacktestService:
    def __init__(self, http_client, strategy_service, token_provider=lambda: None):
        self.http_client = http_client
        self.strategy_service = strategy_service
        self.token_provider = token_provider

    def run_backtest(
        self,
        strategy_id: str,
        start_date: str,
        end_date: str,
        capital: str,
        frequency: str,
    ) -> dict[str, Any]:
        return self._build_backtest(strategy_id, start_date, end_date, capital, frequency)

    def compile_strategy(
        self,
        strategy_id: str,
        start_date: str,
        end_date: str,
        capital: str,
        frequency: str,
        *,
        max_polls: int = 12,
        poll_interval: float = 1.0,
    ) -> dict[str, Any]:
        build_result = self._build_backtest(
            strategy_id,
            start_date,
            end_date,
            capital,
            frequency,
            backtest_type="1",
        )
        backtest_id = build_result.get("backtest_id")
        if not backtest_id:
            return {
                "compiled": False,
                "backtest_id": None,
                "errors": ["compile_backtest_id_not_found"],
                "raw": build_result.get("raw"),
            }

        last_result: dict[str, Any] | None = None
        last_errors: dict[str, Any] | None = None
        for attempt in range(max(1, max_polls)):
            last_errors = self.get_errors(backtest_id, full=True)
            errors = _extract_logs(last_errors.get("raw"))
            error_state = _state_from_raw(last_errors.get("raw"))
            if errors or error_state == "3":
                return {
                    "compiled": False,
                    "backtest_id": backtest_id,
                    "state": error_state,
                    "errors": errors,
                    "attempts": attempt + 1,
                }

            last_result = self.get_result(backtest_id)
            result_state = _state_from_raw(last_result.get("raw")) or last_result.get("status")
            if result_state == "3":
                return {
                    "compiled": False,
                    "backtest_id": backtest_id,
                    "state": result_state,
                    "errors": errors,
                    "attempts": attempt + 1,
                }
            if result_state and result_state != "0":
                return {
                    "compiled": True,
                    "backtest_id": backtest_id,
                    "state": result_state,
                    "attempts": attempt + 1,
                }
            if attempt + 1 < max_polls and poll_interval > 0:
                time.sleep(poll_interval)

        return {
            "compiled": False,
            "backtest_id": backtest_id,
            "state": _state_from_raw(last_result.get("raw")) if last_result else None,
            "errors": _extract_logs(last_errors.get("raw")) if last_errors else [],
            "attempts": max_polls,
            "warnings": ["compile_timeout"],
        }

    def _build_backtest(
        self,
        strategy_id: str,
        start_date: str,
        end_date: str,
        capital: str,
        frequency: str,
        *,
        backtest_type: str = "0",
    ) -> dict[str, Any]:
        strategy = self.strategy_service.get_strategy(strategy_id)
        payload = build_backtest_payload(
            strategy,
            start_date=start_date,
            end_date=end_date,
            capital=capital,
            frequency=frequency,
            backtest_type=backtest_type,
            token=self.token_provider() or _metadata_value(strategy, "token"),
        )
        response = self.http_client.post_form(
            "/algorithm/index/build",
            payload,
            params={"ajax": 1},
            headers={"Referer": self._edit_referer(strategy_id)},
        )
        backtest_id = extract_backtest_id(response.text)
        return {"backtest_id": backtest_id, "raw": _json_or_text(response.text)}

    def get_status(self, backtest_id: str) -> dict[str, Any]:
        response = self.http_client.get(
            "/algorithm/backtest/runTimeInfo",
            params={"backtestId": backtest_id, "token": self.token_provider()},
        )
        parsed = parse_backtest_result(response.text)
        parsed["backtest_id"] = backtest_id
        return parsed

    def get_result(self, backtest_id: str) -> dict[str, Any]:
        response = self._post_backtest(
            "/algorithm/backtest/result",
            backtest_id,
            params={"offset": 0, "userRecordOffset": 0},
        )
        parsed = parse_backtest_result(response.text)
        parsed["backtest_id"] = backtest_id
        return parsed

    def get_stats(self, backtest_id: str, *, full: bool = False, sample_size: int = 5) -> dict[str, Any]:
        payload = self._json_endpoint("/algorithm/backtest/stats", backtest_id)
        if full:
            return payload
        return {
            "backtest_id": backtest_id,
            "summary": compact_value(_data_dict(payload.get("raw")), sample_size=sample_size),
            "full_available": True,
        }

    def get_risk(self, backtest_id: str, *, full: bool = False, sample_size: int = 5) -> dict[str, Any]:
        payload = self._json_endpoint("/algorithm/backtest/risk", backtest_id)
        if full:
            return payload
        return {
            "backtest_id": backtest_id,
            "summary": compact_value(_data_dict(payload.get("raw")), sample_size=sample_size),
            "full_available": True,
        }

    def get_positions(self, backtest_id: str, *, full: bool = False, sample_size: int = 5) -> dict[str, Any]:
        payload = self._json_endpoint("/algorithm/backtest/positionInfo", backtest_id)
        if full:
            return payload
        return _summarize_backtest_items(payload.get("raw"), backtest_id=backtest_id, key="position", sample_size=sample_size)

    def get_transactions(self, backtest_id: str, *, full: bool = False, sample_size: int = 5) -> dict[str, Any]:
        payload = self._json_endpoint("/algorithm/backtest/transactionInfo", backtest_id)
        if full:
            return payload
        return _summarize_backtest_items(
            payload.get("raw"),
            backtest_id=backtest_id,
            key="transaction",
            sample_size=sample_size,
        )

    def get_errors(self, backtest_id: str, *, full: bool = False, sample_size: int = 5) -> dict[str, Any]:
        response = self._post_backtest("/algorithm/backtest/error", backtest_id, params={"offset": 0})
        raw = response.json_or_none()
        payload = {"backtest_id": backtest_id, "raw": raw if raw is not None else response.text}
        if full:
            return payload
        return _summarize_backtest_logs(payload["raw"], backtest_id=backtest_id, sample_size=sample_size)

    def get_logs(self, backtest_id: str, offset: int = 0, *, full: bool = False, sample_size: int = 5) -> dict[str, Any]:
        response = self._post_backtest("/algorithm/backtest/log", backtest_id, params={"offset": offset})
        raw = response.json_or_none()
        logs = _extract_logs(raw)
        payload = {"backtest_id": backtest_id, "logs": logs, "raw": raw if raw is not None else response.text}
        if full:
            return payload
        return _summarize_backtest_logs(payload["raw"], backtest_id=backtest_id, sample_size=sample_size)

    def get_detail(self, backtest_id: str) -> dict[str, Any]:
        status = self.get_status(backtest_id)
        result = self.get_result(backtest_id)
        stats = self.get_stats(backtest_id, full=True)
        positions = self.get_positions(backtest_id, full=True)
        transactions = self.get_transactions(backtest_id, full=True)
        logs = self.get_logs(backtest_id, full=True)
        errors = self.get_errors(backtest_id, full=True)
        return {
            "backtest_id": backtest_id,
            "summary": summarize_backtest_detail(
                status=status,
                result=result,
                stats=stats.get("raw"),
                positions=positions.get("raw"),
                transactions=transactions.get("raw"),
                logs=logs.get("raw"),
                errors=errors.get("raw"),
            ),
            "samples": {
                "first_position": _first_data_item(positions.get("raw"), "position"),
                "first_transaction": _first_data_item(transactions.get("raw"), "transaction"),
                "first_log": _first_data_item(logs.get("raw"), "logArr"),
                "first_error": _first_data_item(errors.get("raw"), "logArr"),
            },
            "raw_commands": {
                "stats": f"jqcli backtest stats --backtest-id {backtest_id}",
                "risk": f"jqcli backtest risk --backtest-id {backtest_id}",
                "positions": f"jqcli backtest positions --backtest-id {backtest_id}",
                "transactions": f"jqcli backtest transactions --backtest-id {backtest_id}",
                "logs": f"jqcli backtest logs --backtest-id {backtest_id}",
                "errors": f"jqcli backtest errors --backtest-id {backtest_id}",
            },
        }

    def _json_endpoint(self, path: str, backtest_id: str) -> dict[str, Any]:
        response = self._post_backtest(path, backtest_id)
        raw = response.json_or_none()
        return {"backtest_id": backtest_id, "raw": raw if raw is not None else response.text}

    def _post_backtest(self, path: str, backtest_id: str, params: dict[str, Any] | None = None):
        merged_params = {"backtestId": backtest_id, "ajax": 1}
        if params:
            merged_params.update(params)
        return self.http_client.post_form(
            path,
            {"undefined": "", "ajax": 1, "token": self.token_provider() or ""},
            params=merged_params,
        )

    def _edit_referer(self, strategy_id: str) -> str:
        return f"{self.http_client.base_url}/algorithm/index/edit?algorithmId={strategy_id}"


def build_backtest_payload(
    strategy: dict[str, Any],
    *,
    start_date: str,
    end_date: str,
    capital: str,
    frequency: str,
    token: str | None,
    backtest_type: str = "0",
) -> dict[str, str]:
    metadata = strategy.get("metadata") if isinstance(strategy.get("metadata"), dict) else {}
    return {
        "algorithm[algorithmId]": str(strategy.get("id") or ""),
        "algorithm[userId]": str(metadata.get("userId") or metadata.get("user_id") or ""),
        "algorithm[accessControl]": str(metadata.get("accessControl") or metadata.get("access_control") or "0"),
        "backtest[type]": backtest_type,
        "algorithm[name]": str(strategy.get("name") or ""),
        "fontpref": str(metadata.get("fontpref") or "14px"),
        "themepref": str(metadata.get("themepref") or "default"),
        "algorithm[code]": _encode_code(str(strategy.get("code") or "")),
        "backtest[startTime]": _start_datetime(start_date),
        "backtest[endTime]": _end_datetime(end_date),
        "backtest[baseCapital]": str(capital),
        "backtest[frequency]": frequency,
        "backtest[pyVersion]": str(metadata.get("pyVersion") or metadata.get("py_version") or "3"),
        "encrType": "base64",
        "ajax": "1",
        "token": token or "",
    }


def _metadata_value(strategy: dict[str, Any], key: str) -> Any:
    metadata = strategy.get("metadata") if isinstance(strategy.get("metadata"), dict) else {}
    return metadata.get(key)


def _encode_code(code: str) -> str:
    return base64.b64encode(code.encode("utf-8")).decode("ascii")


def _start_datetime(value: str) -> str:
    return value if ":" in value else f"{value} 00:00:00"


def _end_datetime(value: str) -> str:
    return value if ":" in value else f"{value} 23:59:59"


def extract_backtest_id(text: str) -> str | None:
    parsed = _json_or_none(text)
    if parsed is not None:
        found = _find_backtest_id(parsed)
        if found:
            return found
    match = re.search(r"backtestId=([A-Za-z0-9_.:-]+)", text)
    if match:
        return match.group(1)
    return None


def parse_backtest_result(text: str) -> dict[str, Any]:
    parsed = _json_or_none(text)
    if parsed is not None:
        status = _runtime_status_from_raw(parsed)
        return {"status": status, "summary": summarize_backtest_result(parsed), "raw": parsed}
    return {"status": None, "raw": text}


def summarize_backtest_result(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    data = raw.get("data") if isinstance(raw.get("data"), dict) else raw
    result = data.get("result") if isinstance(data.get("result"), dict) else {}
    return {
        "state": data.get("state"),
        "count": result.get("count"),
        "overall_return": _last_series_value(result, "overallReturn"),
        "benchmark_return": _last_series_value(result, "benchmark"),
    }


def summarize_backtest_detail(
    *,
    status: dict[str, Any],
    result: dict[str, Any],
    stats: dict[str, Any],
    positions: dict[str, Any],
    transactions: dict[str, Any],
    logs: dict[str, Any],
    errors: dict[str, Any],
) -> dict[str, Any]:
    status_data = _data_dict(status.get("raw"))
    result_summary = result.get("summary") if isinstance(result.get("summary"), dict) else {}
    stats_data = _data_dict(stats)
    runtime_state = result_summary.get("state") or _runtime_status_from_raw(status.get("raw"))
    latest_overall_return = result_summary.get("overall_return")
    latest_benchmark_return = result_summary.get("benchmark_return")
    is_running = runtime_state == "1"
    warnings: list[str] = []
    if is_running:
        warnings.append("backtest_still_running_partial_metrics")
    return {
        "state": runtime_state,
        "need_seconds": status_data.get("needSeconds"),
        "count": result_summary.get("count"),
        "is_final": not is_running,
        "latest_overall_return": latest_overall_return,
        "latest_benchmark_return": latest_benchmark_return,
        "overall_return": None if is_running else latest_overall_return,
        "benchmark_return": None if is_running else latest_benchmark_return,
        "algorithm_return": stats_data.get("algorithm_return"),
        "annual_algo_return": stats_data.get("annual_algo_return"),
        "benchmark_stats_return": stats_data.get("benchmark_return"),
        "sharpe": stats_data.get("sharpe"),
        "sortino": stats_data.get("sortino"),
        "alpha": stats_data.get("alpha"),
        "beta": stats_data.get("beta"),
        "max_drawdown": stats_data.get("max_drawdown"),
        "win_ratio": stats_data.get("win_ratio"),
        "profit_loss_ratio": stats_data.get("profit_loss_ratio"),
        "position_count": len(_data_dict(positions).get("position") or []),
        "transaction_count": len(_data_dict(transactions).get("transaction") or []),
        "log_count": len(_data_dict(logs).get("logArr") or []),
        "error_count": len(_data_dict(errors).get("logArr") or []),
        "warnings": warnings,
    }


def _last_series_value(result: dict[str, Any], key: str) -> Any:
    series = result.get(key)
    if not isinstance(series, dict):
        return None
    values = series.get("value")
    if not isinstance(values, list) or not values:
        return None
    return values[-1]


def _find_backtest_id(value: Any) -> str | None:
    if isinstance(value, dict):
        for key in ("backtestId", "backtest_id", "id"):
            current = value.get(key)
            if current is not None:
                return str(current)
        for key in ("url", "href", "redirect"):
            current = value.get(key)
            if isinstance(current, str):
                parsed = urlparse(current)
                query = parse_qs(parsed.query)
                if query.get("backtestId"):
                    return query["backtestId"][0]
        for child in value.values():
            found = _find_backtest_id(child)
            if found:
                return found
    if isinstance(value, list):
        for child in value:
            found = _find_backtest_id(child)
            if found:
                return found
    return None


def _first_nested_value(value: Any, *keys: str) -> Any:
    if isinstance(value, dict):
        for key in keys:
            if key in value:
                return value[key]
        for child in value.values():
            found = _first_nested_value(child, *keys)
            if found is not None:
                return found
    if isinstance(value, list):
        for child in value:
            found = _first_nested_value(child, *keys)
            if found is not None:
                return found
    return None


def _extract_logs(value: Any) -> list[Any]:
    if isinstance(value, dict):
        for key in ("logArr", "logs", "log", "error", "userRecord", "records"):
            if key in value:
                current = value[key]
                return current if isinstance(current, list) else [current]
        for child in value.values():
            if isinstance(child, (dict, list)):
                logs = _extract_logs(child)
                if logs:
                    return logs
    if isinstance(value, list):
        for child in value:
            if isinstance(child, (dict, list)):
                logs = _extract_logs(child)
                if logs:
                    return logs
    return []


def _state_from_raw(value: Any) -> str | None:
    data = _data_dict(value)
    state = data.get("state") or data.get("status")
    return str(state) if state is not None else None


def _runtime_status_from_raw(value: Any) -> str | None:
    data = _data_dict(value)
    for key in ("status", "state", "phase"):
        current = data.get(key)
        if current is not None:
            return str(current)
    nested = _first_nested_value(value, "state", "phase", "status")
    return str(nested) if nested is not None else None


def _data_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict) and isinstance(value.get("data"), dict):
        return value["data"]
    return value if isinstance(value, dict) else {}


def _first_data_item(value: Any, key: str) -> Any:
    items = _data_dict(value).get(key)
    if isinstance(items, list) and items:
        return items[0]
    return None


def _json_or_none(text: str) -> Any | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _json_or_text(text: str) -> Any:
    parsed = _json_or_none(text)
    return parsed if parsed is not None else text


def _summarize_backtest_logs(raw: Any, *, backtest_id: str, sample_size: int) -> dict[str, Any]:
    data = _data_dict(raw)
    summary = summarize_list(_extract_logs(raw), sample_size=sample_size)
    payload = {
        "backtest_id": backtest_id,
        "count": summary["count"],
        "sample": summary["sample"],
        "truncated": summary["truncated"],
        "full_available": True,
    }
    if "offset" in data:
        payload["offset"] = data.get("offset")
    if "max" in data:
        payload["max"] = data.get("max")
    return payload


def _summarize_backtest_items(raw: Any, *, backtest_id: str, key: str, sample_size: int) -> dict[str, Any]:
    summary = summarize_list(_data_dict(raw).get(key), sample_size=sample_size)
    return {
        "backtest_id": backtest_id,
        "count": summary["count"],
        "sample": summary["sample"],
        "truncated": summary["truncated"],
        "full_available": True,
    }
