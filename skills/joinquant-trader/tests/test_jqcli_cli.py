import unittest

from jqcli_test_path import ensure_skill_jqcli_path

ensure_skill_jqcli_path()

from jqcli.__main__ import build_parser


class JqcliCliTest(unittest.TestCase):
    def test_strategy_get_parser(self):
        args = build_parser().parse_args(["strategy", "get", "--id", "123"])
        self.assertEqual(args.resource, "strategy")
        self.assertEqual(args.action, "get")
        self.assertEqual(args.strategy_id, "123")

    def test_strategy_create_parser(self):
        args = build_parser().parse_args(["strategy", "create", "--name", "demo", "--file", "demo.py"])
        self.assertEqual(args.action, "create")
        self.assertEqual(args.name, "demo")
        self.assertEqual(args.file, "demo.py")

    def test_strategy_update_code_parser(self):
        args = build_parser().parse_args(["strategy", "update-code", "--id", "123", "--file", "demo.py"])
        self.assertEqual(args.action, "update-code")
        self.assertEqual(args.strategy_id, "123")

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

    def test_backtest_compile_parser(self):
        args = build_parser().parse_args(
            [
                "backtest",
                "compile",
                "--strategy-id",
                "123",
                "--start-date",
                "2025-01-01",
                "--end-date",
                "2025-01-31",
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

    def test_backtest_logs_parser_supports_offset(self):
        args = build_parser().parse_args(["backtest", "logs", "--backtest-id", "bt1", "--offset", "100"])
        self.assertEqual(args.action, "logs")
        self.assertEqual(args.offset, 100)

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


if __name__ == "__main__":
    unittest.main()
