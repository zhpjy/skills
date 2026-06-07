import unittest

from jqcli_test_path import ensure_skill_jqcli_path

ensure_skill_jqcli_path()

import jqcli_tool


class JqcliToolWrapperTest(unittest.TestCase):
    def test_agent_mode_defaults_to_enabled(self):
        self.assertTrue(jqcli_tool.is_agent_mode())

    def test_agent_mode_blocks_backtest_status(self):
        self.assertTrue(jqcli_tool._is_forbidden_agent_command(["backtest", "status", "--backtest-id", "bt1"]))

    def test_agent_mode_blocks_backtest_run_without_wait(self):
        self.assertTrue(
            jqcli_tool._is_forbidden_agent_command(
                [
                    "backtest",
                    "run",
                    "--strategy-id",
                    "s1",
                    "--start-date",
                    "2025-01-01",
                    "--end-date",
                    "2025-01-31",
                ]
            )
        )

    def test_agent_mode_allows_backtest_run_with_wait(self):
        self.assertFalse(
            jqcli_tool._is_forbidden_agent_command(
                [
                    "backtest",
                    "run",
                    "--strategy-id",
                    "s1",
                    "--start-date",
                    "2025-01-01",
                    "--end-date",
                    "2025-01-31",
                    "--wait",
                ]
            )
        )

    def test_agent_mode_allows_backtest_wait(self):
        self.assertFalse(jqcli_tool._is_forbidden_agent_command(["backtest", "wait", "--backtest-id", "bt1"]))


if __name__ == "__main__":
    unittest.main()
