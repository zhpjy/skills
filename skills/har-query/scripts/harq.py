from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence
from urllib.parse import parse_qsl, urlparse


STATIC_EXTENSIONS = {
    ".js",
    ".css",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".map",
    ".webp",
    ".avif",
}

SKIP_PATTERNS = (
    r"/websocket",
    r"\.hot-update\.",
    r"__webpack",
    r"/sockjs-node",
    r"favicon\.ico",
)

ID_PATTERNS = (
    (re.compile(r"/[0-9a-f]{32}(?=/|$)", re.IGNORECASE), "/{ID}"),
    (
        re.compile(
            r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(?=/|$)",
            re.IGNORECASE,
        ),
        "/{UUID}",
    ),
    (re.compile(r"(?i)(ticket|token|session)[_-]?[A-Za-z0-9]{12,}"), r"\1_{TOKEN}"),
)


@dataclass(slots=True)
class HarRecord:
    har_name: str
    index: int
    started_at: str
    method: str
    url: str
    path: str
    normalized_path: str
    query: dict[str, str]
    request_headers: dict[str, str]
    response_headers: dict[str, str]
    request_body: str
    response_body: str
    request_json: Any
    response_json: Any
    status: int
    resource_type: str

    @property
    def entry_id(self) -> str:
        return f"{self.har_name}:{self.index}"


def is_static_resource(url: str, resource_type: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path.lower()
    leaf = path.split("/")[-1]
    ext = f".{leaf.rsplit('.', 1)[-1]}" if "." in leaf else ""
    if ext in STATIC_EXTENSIONS:
        return True
    if resource_type in {"stylesheet", "script", "image", "font", "media"}:
        return True
    return any(re.search(pattern, url) for pattern in SKIP_PATTERNS)


def normalize_path(path: str) -> str:
    normalized = path
    for pattern, replacement in ID_PATTERNS:
        normalized = pattern.sub(replacement, normalized)
    return normalized


def _headers_to_dict(items: Sequence[dict[str, Any]] | None) -> dict[str, str]:
    headers: dict[str, str] = {}
    for item in items or []:
        name = item.get("name")
        value = item.get("value")
        if isinstance(name, str) and isinstance(value, str):
            headers[name] = value
    return headers


def _query_to_dict(url: str, query_items: Sequence[dict[str, Any]] | None) -> dict[str, str]:
    if query_items:
        result: dict[str, str] = {}
        for item in query_items:
            name = item.get("name")
            value = item.get("value", "")
            if isinstance(name, str):
                result[name] = "" if value is None else str(value)
        return result
    return dict(parse_qsl(urlparse(url).query, keep_blank_values=True))


def _parse_json_maybe(raw: str) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _body_text(payload: dict[str, Any] | None) -> str:
    if not payload:
        return ""
    text = payload.get("text")
    return text if isinstance(text, str) else ""


def load_har_entries(
    har_paths: Sequence[str | Path],
    *,
    include_static: bool = False,
    include_websocket: bool = False,
) -> list[HarRecord]:
    records: list[HarRecord] = []
    for har_path in har_paths:
        path = Path(har_path)
        har = json.loads(path.read_text(encoding="utf-8"))
        entries = har.get("log", {}).get("entries", [])
        for index, entry in enumerate(entries, start=1):
            request = entry.get("request", {})
            response = entry.get("response", {})
            url = str(request.get("url", ""))
            resource_type = str(entry.get("_resourceType", ""))
            if not include_websocket and resource_type == "websocket":
                continue
            if not include_static and is_static_resource(url, resource_type):
                continue
            parsed = urlparse(url)
            request_body = _body_text(request.get("postData"))
            response_body = _body_text(response.get("content"))
            records.append(
                HarRecord(
                    har_name=path.name,
                    index=index,
                    started_at=str(entry.get("startedDateTime", "")),
                    method=str(request.get("method", "")),
                    url=url,
                    path=parsed.path,
                    normalized_path=normalize_path(parsed.path),
                    query=_query_to_dict(url, request.get("queryString")),
                    request_headers=_headers_to_dict(request.get("headers")),
                    response_headers=_headers_to_dict(response.get("headers")),
                    request_body=request_body,
                    response_body=response_body,
                    request_json=_parse_json_maybe(request_body),
                    response_json=_parse_json_maybe(response_body),
                    status=int(response.get("status", 0) or 0),
                    resource_type=resource_type,
                )
            )
    return records


def aggregate_endpoints(records: Sequence[HarRecord]) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, str], dict[str, Any]] = {}
    for record in records:
        key = (record.method, record.normalized_path)
        bucket = buckets.setdefault(
            key,
            {
                "method": record.method,
                "normalized_path": record.normalized_path,
                "count": 0,
                "paths": set(),
                "statuses": set(),
                "har_names": set(),
            },
        )
        bucket["count"] += 1
        bucket["paths"].add(record.path)
        bucket["statuses"].add(record.status)
        bucket["har_names"].add(record.har_name)
    rows = []
    for bucket in buckets.values():
        rows.append(
            {
                "method": bucket["method"],
                "normalized_path": bucket["normalized_path"],
                "count": bucket["count"],
                "paths": sorted(bucket["paths"]),
                "statuses": sorted(bucket["statuses"]),
                "har_names": sorted(bucket["har_names"]),
            }
        )
    rows.sort(key=lambda row: (-row["count"], row["method"], row["normalized_path"]))
    return rows


def find_records(records: Sequence[HarRecord], *, keyword: str, field: str = "both") -> list[HarRecord]:
    needle = keyword.lower()
    matched: list[HarRecord] = []
    for record in records:
        haystacks: list[str] = []
        if field in {"both", "request"}:
            haystacks.extend(
                [
                    record.url,
                    record.path,
                    json.dumps(record.query, ensure_ascii=False),
                    record.request_body,
                ]
            )
        if field in {"both", "response"}:
            haystacks.append(record.response_body)
        if any(needle in item.lower() for item in haystacks if item):
            matched.append(record)
    return matched


def _walk_fields(value: Any, prefix: str, stats: dict[str, dict[str, Any]]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            next_prefix = f"{prefix}.{key}" if prefix else key
            stats[next_prefix]["count"] += 1
            stats[next_prefix]["types"].add(
                "object" if isinstance(item, dict) else "array" if isinstance(item, list) else type(item).__name__
            )
            _walk_fields(item, next_prefix, stats)
        return
    if isinstance(value, list):
        list_prefix = f"{prefix}[]"
        stats[list_prefix]["count"] += 1
        stats[list_prefix]["types"].add("array")
        for item in value:
            _walk_fields(item, list_prefix, stats)
    return


def extract_field_stats(
    records: Sequence[HarRecord],
    *,
    normalized_path: str,
    side: str = "response",
) -> dict[str, dict[str, Any]]:
    stats: dict[str, dict[str, Any]] = defaultdict(lambda: {"count": 0, "types": set()})
    for record in records:
        if record.normalized_path != normalized_path:
            continue
        payload = record.request_json if side == "request" else record.response_json
        if payload is None:
            continue
        _walk_fields(payload, "", stats)
    result: dict[str, dict[str, Any]] = {}
    for key, value in stats.items():
        result[key] = {"count": value["count"], "types": sorted(value["types"])}
    return dict(sorted(result.items()))


def trace_records(
    records: Sequence[HarRecord],
    *,
    entry_id: str | None = None,
    keyword: str | None = None,
    window: int = 2,
) -> list[dict[str, Any]]:
    target: HarRecord | None = None
    if entry_id:
        target = next((record for record in records if record.entry_id == entry_id), None)
    elif keyword:
        matched = find_records(records, keyword=keyword, field="both")
        target = matched[0] if matched else None
    if target is None:
        return []
    same_har = [record for record in records if record.har_name == target.har_name]
    pos = next(i for i, record in enumerate(same_har) if record.entry_id == target.entry_id)
    start = max(0, pos - window)
    end = min(len(same_har), pos + window + 1)
    return [
        {
            "entry_id": record.entry_id,
            "method": record.method,
            "status": record.status,
            "path": record.path,
            "normalized_path": record.normalized_path,
        }
        for record in same_har[start:end]
    ]


def resolve_har_paths(inputs: Sequence[str], *, use_all: bool) -> list[Path]:
    if use_all or not inputs:
        return sorted(Path("har").glob("*.json"))
    return [Path(item) for item in inputs]


def _render_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def _truncate(raw: str, limit: int = 600) -> str:
    if len(raw) <= limit:
        return raw
    return f"{raw[:limit]}..."


def handle_list(args: argparse.Namespace) -> int:
    records = load_har_entries(
        resolve_har_paths(args.har, use_all=args.all),
        include_static=args.include_static,
        include_websocket=args.include_websocket,
    )
    if args.group_by == "entry":
        for record in records:
            print(
                f"{record.entry_id} {record.method:<6} {record.status:<3} "
                f"{record.normalized_path}"
            )
        return 0
    print(_render_json(aggregate_endpoints(records)))
    return 0


def handle_find(args: argparse.Namespace) -> int:
    records = load_har_entries(
        resolve_har_paths(args.har, use_all=args.all),
        include_static=args.include_static,
        include_websocket=args.include_websocket,
    )
    matched = find_records(records, keyword=args.keyword, field=args.field)
    summary = [
        {
            "entry_id": record.entry_id,
            "method": record.method,
            "status": record.status,
            "path": record.path,
            "normalized_path": record.normalized_path,
            "request_body": _truncate(record.request_body),
            "response_body": _truncate(record.response_body),
        }
        for record in matched
    ]
    print(_render_json(summary))
    return 0


def _select_records(
    records: Sequence[HarRecord],
    *,
    path: str | None = None,
    normalized_path: str | None = None,
) -> list[HarRecord]:
    selected = list(records)
    if path:
        selected = [record for record in selected if record.path == path]
    if normalized_path:
        selected = [record for record in selected if record.normalized_path == normalized_path]
    return selected


def handle_sample(args: argparse.Namespace) -> int:
    records = load_har_entries(
        resolve_har_paths(args.har, use_all=args.all),
        include_static=args.include_static,
        include_websocket=args.include_websocket,
    )
    selected = _select_records(records, path=args.path, normalized_path=args.normalized_path)
    if not selected:
        raise SystemExit("未找到匹配的接口样例")
    record = selected[0]
    print(
        _render_json(
            {
                "entry_id": record.entry_id,
                "method": record.method,
                "status": record.status,
                "path": record.path,
                "normalized_path": record.normalized_path,
                "query": record.query,
                "request_body": record.request_json if record.request_json is not None else record.request_body,
                "response_body": record.response_json if record.response_json is not None else record.response_body,
            }
        )
    )
    return 0


def handle_fields(args: argparse.Namespace) -> int:
    records = load_har_entries(
        resolve_har_paths(args.har, use_all=args.all),
        include_static=args.include_static,
        include_websocket=args.include_websocket,
    )
    normalized_path = args.normalized_path
    if not normalized_path and args.path:
        normalized_path = normalize_path(args.path)
    if not normalized_path:
        raise SystemExit("fields 需要 --path 或 --normalized-path")
    print(_render_json(extract_field_stats(records, normalized_path=normalized_path, side=args.side)))
    return 0


def handle_show(args: argparse.Namespace) -> int:
    records = load_har_entries(
        resolve_har_paths(args.har, use_all=args.all),
        include_static=args.include_static,
        include_websocket=args.include_websocket,
    )
    target = next((record for record in records if record.entry_id == args.entry_id), None)
    if target is None:
        raise SystemExit(f"未找到 entry: {args.entry_id}")
    window = []
    if args.around:
        same_har = [record for record in records if record.har_name == target.har_name]
        pos = next(i for i, record in enumerate(same_har) if record.entry_id == target.entry_id)
        start = max(0, pos - args.around)
        end = min(len(same_har), pos + args.around + 1)
        window = [
            {
                "entry_id": record.entry_id,
                "method": record.method,
                "status": record.status,
                "path": record.path,
            }
            for record in same_har[start:end]
        ]
    print(
        _render_json(
            {
                "entry_id": target.entry_id,
                "har_name": target.har_name,
                "started_at": target.started_at,
                "method": target.method,
                "url": target.url,
                "path": target.path,
                "normalized_path": target.normalized_path,
                "status": target.status,
                "query": target.query,
                "request_headers": target.request_headers,
                "response_headers": target.response_headers,
                "request_body": target.request_json if target.request_json is not None else target.request_body,
                "response_body": target.response_json if target.response_json is not None else target.response_body,
                "around": window,
            }
        )
    )
    return 0


def handle_trace(args: argparse.Namespace) -> int:
    records = load_har_entries(
        resolve_har_paths(args.har, use_all=args.all),
        include_static=args.include_static,
        include_websocket=args.include_websocket,
    )
    trace = trace_records(records, entry_id=args.entry_id, keyword=args.keyword, window=args.window)
    if not trace:
        raise SystemExit("未找到可追踪的请求")
    print(_render_json(trace))
    return 0


def handle_diff(args: argparse.Namespace) -> int:
    base_records = load_har_entries([args.base])
    target_records = load_har_entries([args.target])
    base_keys = {(record.method, record.normalized_path) for record in base_records}
    target_keys = {(record.method, record.normalized_path) for record in target_records}
    added = [
        {"method": method, "normalized_path": path}
        for method, path in sorted(target_keys - base_keys)
    ]
    removed = [
        {"method": method, "normalized_path": path}
        for method, path in sorted(base_keys - target_keys)
    ]
    payload = {
        "added": added,
        "removed": removed,
        "shared_count": len(base_keys & target_keys),
    }
    print(_render_json(payload))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="harq", description="Query HAR files without loading the full capture into context")
    parser.add_argument("--har", action="append", default=[], help="Specific HAR file to query")
    parser.add_argument("--all", action="store_true", help="Query all har/*.json files")
    parser.add_argument("--include-static", action="store_true", help="Include static assets")
    parser.add_argument("--include-websocket", action="store_true", help="Include websocket records")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List requests or grouped endpoints")
    list_parser.add_argument("--group-by", choices=["endpoint", "entry"], default="endpoint")
    list_parser.set_defaults(handler=handle_list)

    find_parser = subparsers.add_parser("find", help="Search request or response content")
    find_parser.add_argument("keyword")
    find_parser.add_argument("--field", choices=["request", "response", "both"], default="both")
    find_parser.set_defaults(handler=handle_find)

    sample_parser = subparsers.add_parser("sample", help="Show one representative request/response")
    sample_group = sample_parser.add_mutually_exclusive_group(required=True)
    sample_group.add_argument("--path")
    sample_group.add_argument("--normalized-path")
    sample_parser.set_defaults(handler=handle_sample)

    fields_parser = subparsers.add_parser("fields", help="Extract JSON field tree stats")
    fields_group = fields_parser.add_mutually_exclusive_group(required=True)
    fields_group.add_argument("--path")
    fields_group.add_argument("--normalized-path")
    fields_parser.add_argument("--side", choices=["request", "response"], default="response")
    fields_parser.set_defaults(handler=handle_fields)

    show_parser = subparsers.add_parser("show", help="Show one full entry")
    show_parser.add_argument("entry_id", help="Entry id in format <har_name>:<index>")
    show_parser.add_argument("--around", type=int, default=0, help="Include nearby entries from same HAR")
    show_parser.set_defaults(handler=handle_show)

    trace_parser = subparsers.add_parser("trace", help="Show nearby calls around a matched request")
    trace_group = trace_parser.add_mutually_exclusive_group(required=True)
    trace_group.add_argument("--entry-id")
    trace_group.add_argument("--keyword")
    trace_parser.add_argument("--window", type=int, default=2)
    trace_parser.set_defaults(handler=handle_trace)

    diff_parser = subparsers.add_parser("diff", help="Compare normalized endpoints between two HAR files")
    diff_parser.add_argument("--base", required=True)
    diff_parser.add_argument("--target", required=True)
    diff_parser.set_defaults(handler=handle_diff)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
