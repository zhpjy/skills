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

    def test_backtest_detail_parser(self):
        args = build_parser().parse_args(["backtest", "detail", "--backtest-id", "bt1"])
        self.assertEqual(args.resource, "backtest")
        self.assertEqual(args.action, "detail")
        self.assertEqual(args.backtest_id, "bt1")

    def test_backtest_logs_parser_supports_offset(self):
        args = build_parser().parse_args(["backtest", "logs", "--backtest-id", "bt1", "--offset", "100"])
        self.assertEqual(args.action, "logs")
        self.assertEqual(args.offset, 100)


if __name__ == "__main__":
    unittest.main()
