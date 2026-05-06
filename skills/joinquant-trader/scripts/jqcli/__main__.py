from __future__ import annotations

import argparse
import sys
from pathlib import Path
from jqcli.auth import AuthError, AuthService, JoinQuantAuthClient
from jqcli.backtest import BacktestService
from jqcli.config import ConfigError, load_config
from jqcli.http import JoinQuantHttpClient
from jqcli.output import error_response, print_json
from jqcli.session import load_session, save_session
from jqcli.strategy import StrategyService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="jqcli")
    subparsers = parser.add_subparsers(dest="resource")

    auth = subparsers.add_parser("auth")
    auth_subparsers = auth.add_subparsers(dest="action")
    auth_subparsers.add_parser("status")
    auth_subparsers.add_parser("login")

    strategy = subparsers.add_parser("strategy")
    strategy_subparsers = strategy.add_subparsers(dest="action")
    strategy_subparsers.add_parser("list")
    strategy_get = strategy_subparsers.add_parser("get")
    strategy_get.add_argument("--id", required=True, dest="strategy_id")
    strategy_create = strategy_subparsers.add_parser("create")
    strategy_create.add_argument("--name", required=True)
    _add_code_source_args(strategy_create)
    _add_strategy_backtest_defaults(strategy_create)
    strategy_update = strategy_subparsers.add_parser("update-code")
    strategy_update.add_argument("--id", required=True, dest="strategy_id")
    strategy_update.add_argument("--name")
    _add_code_source_args(strategy_update)
    _add_strategy_backtest_defaults(strategy_update)
    strategy_rename = strategy_subparsers.add_parser("rename")
    strategy_rename.add_argument("--id", required=True, dest="strategy_id")
    strategy_rename.add_argument("--name", required=True)
    strategy_delete = strategy_subparsers.add_parser("delete")
    strategy_delete.add_argument("--id", required=True, dest="strategy_id")
    strategy_delete.add_argument("--confirm-delete", action="store_true")

    directory = subparsers.add_parser("directory", aliases=["dir"])
    directory_subparsers = directory.add_subparsers(dest="action")
    directory_list = directory_subparsers.add_parser("list")
    directory_list.add_argument("--parent-id", default="0")
    directory_create = directory_subparsers.add_parser("create")
    directory_create.add_argument("--name", required=True)
    directory_create.add_argument("--parent-id", default="0")
    directory_delete = directory_subparsers.add_parser("delete")
    directory_delete.add_argument("--id", required=True, dest="directory_id")
    directory_delete.add_argument("--parent-id", default="0")
    directory_delete.add_argument("--confirm-delete", action="store_true")

    backtest = subparsers.add_parser("backtest")
    backtest_subparsers = backtest.add_subparsers(dest="action")
    backtest_run = backtest_subparsers.add_parser("run")
    backtest_run.add_argument("--strategy-id", required=True)
    backtest_run.add_argument("--start-date", required=True)
    backtest_run.add_argument("--end-date", required=True)
    backtest_run.add_argument("--capital", default="100000")
    backtest_run.add_argument("--frequency", default="day")
    for action in ("status", "result", "stats", "risk", "positions", "transactions", "errors", "detail"):
        command = backtest_subparsers.add_parser(action)
        command.add_argument("--backtest-id", required=True)
    logs = backtest_subparsers.add_parser("logs")
    logs.add_argument("--backtest-id", required=True)
    logs.add_argument("--offset", type=int, default=0)
    return parser


def _add_code_source_args(parser: argparse.ArgumentParser) -> None:
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file")
    source.add_argument("--stdin", action="store_true")


def _add_strategy_backtest_defaults(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--start-date", default="2019-01-01")
    parser.add_argument("--end-date", default="2019-06-30")
    parser.add_argument("--capital", default="100000")
    parser.add_argument("--frequency", default="day")
    parser.add_argument("--type", default="stock", dest="strategy_type")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.resource is None:
        parser.print_help()
        return 0
    try:
        context = build_context()
        payload = dispatch(args, context)
        print_json(payload)
        return 0 if payload.get("ok") else 1
    except ConfigError as exc:
        print_json(error_response("CONFIG_MISSING", str(exc)))
        return 1
    except AuthError as exc:
        print_json(error_response("AUTH_FAILED", str(exc)))
        return 1
    except Exception as exc:
        print_json(error_response("UNEXPECTED_ERROR", str(exc)))
        return 1


def build_context():
    config = load_config()
    http_client = JoinQuantHttpClient(config.base_url)
    auth_client = JoinQuantAuthClient(http_client)
    session_path = config.state_dir / "session.json"
    auth_service = AuthService(
        config=config,
        client=auth_client,
        load_state=lambda: load_session(session_path),
        save_state=lambda state: save_session(session_path, state),
    )
    token_provider = lambda: load_session(session_path).token
    strategy_service = StrategyService(http_client, token_provider=token_provider)
    return {
        "config": config,
        "auth": auth_service,
        "strategy": strategy_service,
        "backtest": BacktestService(http_client, strategy_service, token_provider=token_provider),
    }


def dispatch(args, context):
    from jqcli.output import success_response

    if args.resource == "auth" and args.action == "status":
        state = context["auth"].ensure_session()
        return success_response({"authenticated": bool(state.cookies), "token_present": bool(state.token)})
    if args.resource == "auth" and args.action == "login":
        state = context["auth"].ensure_session()
        return success_response({"authenticated": bool(state.cookies), "token_present": bool(state.token)})
    if args.resource == "strategy":
        context["auth"].ensure_session()
        if args.action == "list":
            return success_response({"strategies": context["strategy"].list_strategies()})
        if args.action == "get":
            return success_response(context["strategy"].get_strategy(args.strategy_id))
        if args.action == "create":
            return success_response(
                context["strategy"].create_strategy(
                    name=args.name,
                    code=read_code_source(args),
                    start_date=args.start_date,
                    end_date=args.end_date,
                    capital=args.capital,
                    frequency=args.frequency,
                    strategy_type=args.strategy_type,
                )
            )
        if args.action == "update-code":
            return success_response(
                context["strategy"].save_strategy(
                    args.strategy_id,
                    name=args.name,
                    code=read_code_source(args),
                    start_date=args.start_date,
                    end_date=args.end_date,
                    capital=args.capital,
                    frequency=args.frequency,
                )
            )
        if args.action == "rename":
            return success_response(context["strategy"].rename_strategy(args.strategy_id, args.name))
        if args.action == "delete":
            if not args.confirm_delete:
                return error_response("CONFIRMATION_REQUIRED", "Pass --confirm-delete to delete a strategy")
            return success_response(context["strategy"].delete_strategy(args.strategy_id))
    if args.resource in {"directory", "dir"}:
        context["auth"].ensure_session()
        if args.action == "list":
            return success_response({"directories": context["strategy"].list_directories(args.parent_id)})
        if args.action == "create":
            return success_response(context["strategy"].create_directory(name=args.name, parent_id=args.parent_id))
        if args.action == "delete":
            if not args.confirm_delete:
                return error_response("CONFIRMATION_REQUIRED", "Pass --confirm-delete to delete a directory")
            return success_response(context["strategy"].delete_directory(directory_id=args.directory_id, parent_id=args.parent_id))
    if args.resource == "backtest":
        context["auth"].ensure_session()
        if args.action == "run":
            return success_response(
                context["backtest"].run_backtest(
                    args.strategy_id,
                    args.start_date,
                    args.end_date,
                    args.capital,
                    args.frequency,
                )
            )
        if args.action == "status":
            return success_response(context["backtest"].get_status(args.backtest_id))
        if args.action == "result":
            return success_response(context["backtest"].get_result(args.backtest_id))
        if args.action == "stats":
            return success_response(context["backtest"].get_stats(args.backtest_id))
        if args.action == "risk":
            return success_response(context["backtest"].get_risk(args.backtest_id))
        if args.action == "positions":
            return success_response(context["backtest"].get_positions(args.backtest_id))
        if args.action == "transactions":
            return success_response(context["backtest"].get_transactions(args.backtest_id))
        if args.action == "errors":
            return success_response(context["backtest"].get_errors(args.backtest_id))
        if args.action == "logs":
            return success_response(context["backtest"].get_logs(args.backtest_id, offset=args.offset))
        if args.action == "detail":
            return success_response(context["backtest"].get_detail(args.backtest_id))
    return error_response("COMMAND_UNSUPPORTED", "Command is not implemented yet")


def read_code_source(args) -> str:
    if getattr(args, "stdin", False):
        return sys.stdin.read()
    return Path(args.file).read_text(encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
