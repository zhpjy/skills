import unittest

from jqcli_test_path import ensure_skill_jqcli_path

ensure_skill_jqcli_path()

from jqcli.__main__ import build_parser, dispatch


class JqcliCliTest(unittest.TestCase):
    def test_strategy_get_parser(self):
        args = build_parser().parse_args(["strategy", "get", "--id", "123"])
        self.assertEqual(args.resource, "strategy")
        self.assertEqual(args.action, "get")
        self.assertEqual(args.strategy_id, "123")

    def test_strategy_create_parser(self):
        args = build_parser().parse_args(
            ["strategy", "create", "--name", "demo", "--file", "demo.py", "--folder-id", "122341"]
        )
        self.assertEqual(args.action, "create")
        self.assertEqual(args.name, "demo")
        self.assertEqual(args.file, "demo.py")
        self.assertEqual(args.folder_id, "122341")

    def test_strategy_create_parser_requires_folder_id(self):
        with self.assertRaises(SystemExit):
            build_parser().parse_args(["strategy", "create", "--name", "demo", "--file", "demo.py"])

    def test_strategy_create_parser_supports_folder_id(self):
        args = build_parser().parse_args(
            ["strategy", "create", "--name", "demo", "--file", "demo.py", "--folder-id", "122341"]
        )
        self.assertEqual(args.action, "create")
        self.assertEqual(args.folder_id, "122341")

    def test_strategy_update_code_parser(self):
        args = build_parser().parse_args(["strategy", "update-code", "--id", "123", "--file", "demo.py"])
        self.assertEqual(args.action, "update-code")
        self.assertEqual(args.strategy_id, "123")

    def test_strategy_list_parser_supports_folder_id(self):
        args = build_parser().parse_args(["strategy", "list", "--folder-id", "122341"])
        self.assertEqual(args.resource, "strategy")
        self.assertEqual(args.action, "list")
        self.assertEqual(args.folder_id, "122341")

    def test_strategy_delete_requires_confirm_flag(self):
        args = build_parser().parse_args(["strategy", "delete", "--id", "123", "--confirm-delete"])
        self.assertTrue(args.confirm_delete)

    def test_directory_create_parser(self):
        args = build_parser().parse_args(["directory", "create", "--name", "demo", "--parent-id", "0"])
        self.assertEqual(args.resource, "directory")
        self.assertEqual(args.action, "create")
        self.assertEqual(args.name, "demo")
        self.assertEqual(args.parent_id, "0")

    def test_directory_delete_requires_confirm_flag(self):
        args = build_parser().parse_args(["directory", "delete", "--id", "121931", "--confirm-delete"])
        self.assertEqual(args.action, "delete")
        self.assertEqual(args.directory_id, "121931")
        self.assertTrue(args.confirm_delete)

    def test_backtest_run_parser(self):
        args = build_parser().parse_args(
            [
                "backtest",
                "run",
                "--strategy-id",
                "123",
                "--start-date",
                "2025-01-01",
                "--end-date",
                "2025-01-31",
            ]
        )
        self.assertEqual(args.resource, "backtest")
        self.assertEqual(args.action, "run")
        self.assertEqual(args.strategy_id, "123")
        self.assertEqual(args.capital, "100000")
        self.assertEqual(args.frequency, "day")
        self.assertFalse(args.wait)

    def test_backtest_run_parser_supports_wait(self):
        args = build_parser().parse_args(
            [
                "backtest",
                "run",
                "--strategy-id",
                "123",
                "--start-date",
                "2025-01-01",
                "--end-date",
                "2025-01-31",
                "--wait",
                "--max-polls",
                "8",
                "--poll-interval",
                "0.5",
            ]
        )
        self.assertTrue(args.wait)
        self.assertEqual(args.max_polls, 8)
        self.assertEqual(args.poll_interval, 0.5)

    def test_backtest_compile_parser(self):
        args = build_parser().parse_args(
            [
                "backtest",
                "compile",
                "--strategy-id",
                "123",
            ]
        )
        self.assertEqual(args.resource, "backtest")
        self.assertEqual(args.action, "compile")
        self.assertEqual(args.strategy_id, "123")
        self.assertEqual(args.capital, "100000")
        self.assertEqual(args.frequency, "day")

    def test_backtest_detail_parser(self):
        args = build_parser().parse_args(["backtest", "detail", "--backtest-id", "bt1"])
        self.assertEqual(args.resource, "backtest")
        self.assertEqual(args.action, "detail")
        self.assertEqual(args.backtest_id, "bt1")

    def test_backtest_wait_parser(self):
        args = build_parser().parse_args(["backtest", "wait", "--backtest-id", "bt1", "--max-polls", "9"])
        self.assertEqual(args.resource, "backtest")
        self.assertEqual(args.action, "wait")
        self.assertEqual(args.backtest_id, "bt1")
        self.assertEqual(args.max_polls, 9)

    def test_backtest_logs_parser_supports_offset(self):
        args = build_parser().parse_args(["backtest", "logs", "--backtest-id", "bt1", "--offset", "100"])
        self.assertEqual(args.action, "logs")
        self.assertEqual(args.offset, 100)

    def test_backtest_logs_parser_supports_full(self):
        args = build_parser().parse_args(["backtest", "logs", "--backtest-id", "bt1", "--full"])
        self.assertEqual(args.action, "logs")
        self.assertTrue(args.full)

    def test_factor_list_parser_supports_har_observed_filters(self):
        args = build_parser().parse_args(
            [
                "factor",
                "list",
                "--category-id",
                "0",
                "--universe-type",
                "hs300",
                "--time-range",
                "3y",
                "--commision-fee",
                "8",
                "--skip-paused",
                "0",
            ]
        )
        self.assertEqual(args.resource, "factor")
        self.assertEqual(args.action, "list")
        self.assertEqual(args.category_id, "0")
        self.assertEqual(args.universe_type, "hs300")
        self.assertEqual(args.time_range, "3y")
        self.assertEqual(args.commision_fee, "8")
        self.assertEqual(args.skip_paused, "0")

    def test_factor_list_parser_supports_full(self):
        args = build_parser().parse_args(["factor", "list", "--full"])
        self.assertEqual(args.action, "list")
        self.assertTrue(args.full)

    def test_factor_detail_parser_supports_analysis_filters(self):
        args = build_parser().parse_args(
            [
                "factor",
                "detail",
                "--id",
                "factor-1",
                "--universe-type",
                "zz500",
                "--time-range",
                "1y",
                "--commision-fee",
                "0",
                "--skip-paused",
                "1",
                "--include-series",
            ]
        )
        self.assertEqual(args.resource, "factor")
        self.assertEqual(args.action, "detail")
        self.assertEqual(args.factor_id, "factor-1")
        self.assertEqual(args.universe_type, "zz500")
        self.assertEqual(args.time_range, "1y")
        self.assertEqual(args.commision_fee, "0")
        self.assertEqual(args.skip_paused, "1")
        self.assertTrue(args.include_series)

    def test_factor_detail_parser_supports_full(self):
        args = build_parser().parse_args(["factor", "detail", "--id", "factor-1", "--full"])
        self.assertEqual(args.action, "detail")
        self.assertTrue(args.full)

    def test_factor_series_parser_supports_side_and_turnover_filters(self):
        args = build_parser().parse_args(
            [
                "factor",
                "daily-stats",
                "--id",
                "factor-1",
                "--side",
                "short",
                "--turnover-period",
                "1",
                "--delay",
                "0",
                "--turnover-time",
                "15:0015:00",
            ]
        )
        self.assertEqual(args.action, "daily-stats")
        self.assertEqual(args.factor_id, "factor-1")
        self.assertEqual(args.side, "short")
        self.assertEqual(args.turnover_period, "1")
        self.assertEqual(args.delay, "0")
        self.assertEqual(args.turnover_time, "15:0015:00")

    def test_factor_stocks_parser_supports_full(self):
        args = build_parser().parse_args(["factor", "stocks", "--id", "factor-1", "--full"])
        self.assertEqual(args.action, "stocks")
        self.assertTrue(args.full)

    def test_backtest_run_dispatch_allows_user_specified_dates(self):
        args = build_parser().parse_args(
            [
                "backtest",
                "run",
                "--strategy-id",
                "123",
                "--start-date",
                "2024-01-01",
                "--end-date",
                "2025-01-31",
            ]
        )

        class FakeAuth:
            def __init__(self):
                self.called = False

            def ensure_session(self):
                self.called = True

        class FakeBacktest:
            def run_backtest(self, strategy_id, start_date, end_date, capital, frequency, **kwargs):
                return {
                    "strategy_id": strategy_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "capital": capital,
                    "frequency": frequency,
                    **kwargs,
                }

        auth = FakeAuth()
        payload = dispatch(args, {"auth": auth, "backtest": FakeBacktest()})
        self.assertTrue(payload["ok"])
        self.assertTrue(auth.called)
        self.assertEqual(payload["data"]["start_date"], "2024-01-01")
        self.assertEqual(payload["data"]["end_date"], "2025-01-31")
        self.assertFalse(payload["data"]["wait"])

    def test_backtest_wait_dispatch_uses_wait_service(self):
        args = build_parser().parse_args(["backtest", "wait", "--backtest-id", "bt1", "--max-polls", "3"])

        class FakeAuth:
            def __init__(self):
                self.called = False

            def ensure_session(self):
                self.called = True

        class FakeBacktest:
            def wait_for_backtest(self, backtest_id, max_polls, poll_interval):
                return {
                    "backtest_id": backtest_id,
                    "completed": True,
                    "attempts": max_polls,
                    "poll_interval": poll_interval,
                }

        auth = FakeAuth()
        payload = dispatch(args, {"auth": auth, "backtest": FakeBacktest()})
        self.assertTrue(payload["ok"])
        self.assertTrue(auth.called)
        self.assertEqual(payload["data"]["backtest_id"], "bt1")
        self.assertEqual(payload["data"]["attempts"], 3)

    def test_backtest_compile_dispatch_uses_internal_compile_window(self):
        args = build_parser().parse_args(
            [
                "backtest",
                "compile",
                "--strategy-id",
                "123",
            ]
        )

        class FakeAuth:
            def __init__(self):
                self.called = False

            def ensure_session(self):
                self.called = True

        class FakeBacktest:
            def compile_strategy(self, strategy_id, start_date, end_date, capital, frequency):
                return {
                    "strategy_id": strategy_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "capital": capital,
                    "frequency": frequency,
                }

        auth = FakeAuth()
        payload = dispatch(args, {"auth": auth, "backtest": FakeBacktest()})
        self.assertTrue(payload["ok"])
        self.assertTrue(auth.called)
        self.assertEqual(payload["data"]["start_date"], "2026-04-20")
        self.assertEqual(payload["data"]["end_date"], "2026-04-22")

    def test_dispatch_removes_raw_by_default(self):
        args = build_parser().parse_args(["backtest", "status", "--backtest-id", "bt1"])

        class FakeAuth:
            def ensure_session(self):
                return None

        class FakeBacktest:
            def get_status(self, backtest_id):
                return {
                    "backtest_id": backtest_id,
                    "status": "2",
                    "summary": {"overall_return": 0.12},
                    "raw": {"data": {"status": "2", "overallReturn": 0.12}},
                }

        payload = dispatch(args, {"auth": FakeAuth(), "backtest": FakeBacktest()})
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["status"], "2")
        self.assertNotIn("raw", payload["data"])

    def test_dispatch_preserves_raw_in_full_mode(self):
        args = build_parser().parse_args(["backtest", "stats", "--backtest-id", "bt1", "--full"])

        class FakeAuth:
            def ensure_session(self):
                return None

        class FakeBacktest:
            def get_stats(self, backtest_id, full):
                return {
                    "backtest_id": backtest_id,
                    "summary": {"sharpe": 1.8},
                    "raw": {"data": {"sharpe": 1.8, "series": [1, 2, 3]}},
                }

        payload = dispatch(args, {"auth": FakeAuth(), "backtest": FakeBacktest()})
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["raw"]["data"]["sharpe"], 1.8)


if __name__ == "__main__":
    unittest.main()
