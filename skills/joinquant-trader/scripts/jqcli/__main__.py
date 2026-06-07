from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path
from jqcli.auth import AuthError, AuthService, JoinQuantAuthClient
from jqcli.backtest import BacktestService
from jqcli.config import ConfigError, load_config
from jqcli.factor import FactorService
from jqcli.http import JoinQuantHttpClient
from jqcli.output import error_response, print_json, success_response
from jqcli.session import load_session, save_session
from jqcli.strategy import StrategyService


COMPILE_START_DATE = "2026-04-20"
COMPILE_END_DATE = "2026-04-22"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="jqcli")
    subparsers = parser.add_subparsers(dest="resource")

    auth = subparsers.add_parser("auth")
    auth_subparsers = auth.add_subparsers(dest="action")
    auth_subparsers.add_parser("status")
    auth_subparsers.add_parser("login")

    strategy = subparsers.add_parser("strategy")
    strategy_subparsers = strategy.add_subparsers(dest="action")
    strategy_list = strategy_subparsers.add_parser("list")
    strategy_list.add_argument("--folder-id", default="0")
    strategy_get = strategy_subparsers.add_parser("get")
    strategy_get.add_argument("--id", required=True, dest="strategy_id")
    strategy_create = strategy_subparsers.add_parser("create")
    strategy_create.add_argument("--name", required=True)
    _add_code_source_args(strategy_create)
    _add_strategy_backtest_defaults(strategy_create)
    strategy_create.add_argument("--folder-id", required=True)
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
    backtest_compile = backtest_subparsers.add_parser("compile")
    backtest_compile.add_argument("--strategy-id", required=True)
    backtest_compile.add_argument("--capital", default="100000")
    backtest_compile.add_argument("--frequency", default="day")
    for action in ("status", "result", "stats", "risk", "positions", "transactions", "errors", "detail"):
        command = backtest_subparsers.add_parser(action)
        command.add_argument("--backtest-id", required=True)
        if action in {"stats", "risk", "positions", "transactions", "errors"}:
            command.add_argument("--full", action="store_true")
    logs = backtest_subparsers.add_parser("logs")
    logs.add_argument("--backtest-id", required=True)
    logs.add_argument("--offset", type=int, default=0)
    logs.add_argument("--full", action="store_true")

    factor = subparsers.add_parser("factor")
    factor_subparsers = factor.add_subparsers(dest="action")
    factor_subparsers.add_parser("settings")
    factor_subparsers.add_parser("categories")
    factor_list = factor_subparsers.add_parser("list")
    _add_factor_list_args(factor_list)
    factor_list.add_argument("--full", action="store_true")
    factor_info = factor_subparsers.add_parser("info")
    factor_info.add_argument("--id", required=True, dest="factor_id")
    factor_detail = factor_subparsers.add_parser("detail")
    factor_detail.add_argument("--id", required=True, dest="factor_id")
    _add_factor_analysis_args(factor_detail, include_commision=True, include_side=True)
    factor_detail.add_argument("--include-series", action="store_true")
    factor_detail.add_argument("--full", action="store_true")
    factor_performance = factor_subparsers.add_parser("performance")
    factor_performance.add_argument("--id", required=True, dest="factor_id")
    _add_factor_analysis_args(factor_performance, include_commision=True)
    factor_daily = factor_subparsers.add_parser("daily-stats")
    factor_daily.add_argument("--id", required=True, dest="factor_id")
    _add_factor_analysis_args(factor_daily, include_commision=True, include_side=True)
    factor_ic = factor_subparsers.add_parser("ic")
    factor_ic.add_argument("--id", required=True, dest="factor_id")
    _add_factor_analysis_args(factor_ic, include_commision=False)
    factor_turnovers = factor_subparsers.add_parser("turnovers")
    factor_turnovers.add_argument("--id", required=True, dest="factor_id")
    _add_factor_analysis_args(factor_turnovers, include_commision=True, include_side=True)
    factor_stocks = factor_subparsers.add_parser("stocks")
    factor_stocks.add_argument("--id", required=True, dest="factor_id")
    factor_stocks.add_argument("--universe-type", default="zz500")
    factor_stocks.add_argument("--full", action="store_true")
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


def _add_factor_list_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--category-id", default="0")
    parser.add_argument("--universe-type", default="zz500")
    parser.add_argument("--time-range", default="3y")
    parser.add_argument("--commision-fee", default="0")
    parser.add_argument("--skip-paused", default="1")


def _add_factor_analysis_args(
    parser: argparse.ArgumentParser,
    *,
    include_commision: bool,
    include_side: bool = False,
) -> None:
    parser.add_argument("--universe-type", default="zz500")
    parser.add_argument("--time-range", default="3y")
    if include_commision:
        parser.add_argument("--commision-fee", default="0")
    parser.add_argument("--skip-paused", default="1")
    if include_side:
        parser.add_argument("--side", default="long")
    parser.add_argument("--turnover-period")
    parser.add_argument("--delay")
    parser.add_argument("--turnover-time")


def _parse_cli_date(value: str) -> datetime.date:
    return datetime.datetime.strptime(value, "%Y-%m-%d").date()


def _validate_backtest_dates(start_date: str, end_date: str):
    try:
        parsed_start = _parse_cli_date(start_date)
        parsed_end = _parse_cli_date(end_date)
    except ValueError:
        return error_response(
            "INVALID_DATE_FORMAT",
            "start-date 和 end-date 必须使用 YYYY-MM-DD 格式",
        )

    if parsed_start > parsed_end:
        return error_response(
            "INVALID_DATE_RANGE",
            "start-date 不能晚于 end-date",
        )
    return None


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
        "factor": FactorService(http_client),
    }


def dispatch(args, context):
    if args.resource == "auth" and args.action == "status":
        state = context["auth"].ensure_session()
        return _success(args, {"authenticated": bool(state.cookies), "token_present": bool(state.token)})
    if args.resource == "auth" and args.action == "login":
        state = context["auth"].ensure_session()
        return _success(args, {"authenticated": bool(state.cookies), "token_present": bool(state.token)})
    if args.resource == "strategy":
        context["auth"].ensure_session()
        if args.action == "list":
            return _success(args, {"strategies": context["strategy"].list_strategies(args.folder_id)})
        if args.action == "get":
            return _success(args, context["strategy"].get_strategy(args.strategy_id))
        if args.action == "create":
            return _success(
                args,
                context["strategy"].create_strategy(
                    name=args.name,
                    code=read_code_source(args),
                    start_date=args.start_date,
                    end_date=args.end_date,
                    capital=args.capital,
                    frequency=args.frequency,
                    strategy_type=args.strategy_type,
                    folder_id=args.folder_id,
                )
            )
        if args.action == "update-code":
            return _success(
                args,
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
            return _success(args, context["strategy"].rename_strategy(args.strategy_id, args.name))
        if args.action == "delete":
            if not args.confirm_delete:
                return error_response("CONFIRMATION_REQUIRED", "Pass --confirm-delete to delete a strategy")
            return _success(args, context["strategy"].delete_strategy(args.strategy_id))
    if args.resource in {"directory", "dir"}:
        context["auth"].ensure_session()
        if args.action == "list":
            return _success(args, {"directories": context["strategy"].list_directories(args.parent_id)})
        if args.action == "create":
            return _success(args, context["strategy"].create_directory(name=args.name, parent_id=args.parent_id))
        if args.action == "delete":
            if not args.confirm_delete:
                return error_response("CONFIRMATION_REQUIRED", "Pass --confirm-delete to delete a directory")
            return _success(
                args,
                context["strategy"].delete_directory(directory_id=args.directory_id, parent_id=args.parent_id),
            )
    if args.resource == "backtest":
        if args.action == "run":
            validation_error = _validate_backtest_dates(args.start_date, args.end_date)
            if validation_error is not None:
                return validation_error
        context["auth"].ensure_session()
        if args.action == "run":
            return _success(
                args,
                context["backtest"].run_backtest(
                    args.strategy_id,
                    args.start_date,
                    args.end_date,
                    args.capital,
                    args.frequency,
                )
            )
        if args.action == "compile":
            return _success(
                args,
                context["backtest"].compile_strategy(
                    args.strategy_id,
                    COMPILE_START_DATE,
                    COMPILE_END_DATE,
                    args.capital,
                    args.frequency,
                )
            )
        if args.action == "status":
            return _success(args, context["backtest"].get_status(args.backtest_id))
        if args.action == "result":
            return _success(args, context["backtest"].get_result(args.backtest_id))
        if args.action == "stats":
            return _success(args, context["backtest"].get_stats(args.backtest_id, full=args.full))
        if args.action == "risk":
            return _success(args, context["backtest"].get_risk(args.backtest_id, full=args.full))
        if args.action == "positions":
            return _success(args, context["backtest"].get_positions(args.backtest_id, full=args.full))
        if args.action == "transactions":
            return _success(args, context["backtest"].get_transactions(args.backtest_id, full=args.full))
        if args.action == "errors":
            return _success(args, context["backtest"].get_errors(args.backtest_id, full=args.full))
        if args.action == "logs":
            return _success(args, context["backtest"].get_logs(args.backtest_id, offset=args.offset, full=args.full))
        if args.action == "detail":
            return _success(args, context["backtest"].get_detail(args.backtest_id))
    if args.resource == "factor":
        context["auth"].ensure_session()
        if args.action == "settings":
            return _success(args, context["factor"].get_settings())
        if args.action == "categories":
            return _success(args, context["factor"].list_categories())
        if args.action == "list":
            return _success(
                args,
                context["factor"].list_factors(
                    category_id=args.category_id,
                    universe_type=args.universe_type,
                    time_range=args.time_range,
                    commision_fee=args.commision_fee,
                    skip_paused=args.skip_paused,
                    full=args.full,
                )
            )
        if args.action == "info":
            return _success(args, context["factor"].get_info(args.factor_id))
        if args.action == "performance":
            return _success(
                args,
                context["factor"].get_performance(
                    factor_id=args.factor_id,
                    universe_type=args.universe_type,
                    time_range=args.time_range,
                    commision_fee=args.commision_fee,
                    skip_paused=args.skip_paused,
                    turnover_period=args.turnover_period,
                    delay=args.delay,
                    turnover_time=args.turnover_time,
                )
            )
        if args.action == "daily-stats":
            return _success(
                args,
                context["factor"].get_daily_stats(
                    factor_id=args.factor_id,
                    side=args.side,
                    universe_type=args.universe_type,
                    time_range=args.time_range,
                    commision_fee=args.commision_fee,
                    skip_paused=args.skip_paused,
                    turnover_period=args.turnover_period,
                    delay=args.delay,
                    turnover_time=args.turnover_time,
                )
            )
        if args.action == "ic":
            return _success(
                args,
                context["factor"].get_ic(
                    factor_id=args.factor_id,
                    universe_type=args.universe_type,
                    time_range=args.time_range,
                    skip_paused=args.skip_paused,
                    turnover_period=args.turnover_period,
                    delay=args.delay,
                    turnover_time=args.turnover_time,
                )
            )
        if args.action == "turnovers":
            return _success(
                args,
                context["factor"].get_turnovers(
                    factor_id=args.factor_id,
                    side=args.side,
                    universe_type=args.universe_type,
                    time_range=args.time_range,
                    commision_fee=args.commision_fee,
                    skip_paused=args.skip_paused,
                    turnover_period=args.turnover_period,
                    delay=args.delay,
                    turnover_time=args.turnover_time,
                )
            )
        if args.action == "stocks":
            return _success(
                args,
                context["factor"].get_stock_list(
                    factor_id=args.factor_id,
                    universe_type=args.universe_type,
                    full=args.full,
                )
            )
        if args.action == "detail":
            return _success(
                args,
                context["factor"].get_detail(
                    factor_id=args.factor_id,
                    universe_type=args.universe_type,
                    time_range=args.time_range,
                    commision_fee=args.commision_fee,
                    skip_paused=args.skip_paused,
                    side=args.side,
                    turnover_period=args.turnover_period,
                    delay=args.delay,
                    turnover_time=args.turnover_time,
                    include_series=args.include_series,
                    full=args.full,
                )
            )
    return error_response("COMMAND_UNSUPPORTED", "Command is not implemented yet")


def _success(args, data):
    return success_response(data, include_raw=bool(getattr(args, "full", False)))


def read_code_source(args) -> str:
    if getattr(args, "stdin", False):
        return sys.stdin.read()
    return Path(args.file).read_text(encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
