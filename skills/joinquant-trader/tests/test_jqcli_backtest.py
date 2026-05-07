import unittest
import base64

from jqcli_test_path import ensure_skill_jqcli_path

ensure_skill_jqcli_path()

from jqcli.backtest import (
    BacktestService,
    build_backtest_payload,
    extract_backtest_id,
    parse_backtest_result,
    summarize_backtest_detail,
    summarize_backtest_result,
)


class JqcliBacktestTest(unittest.TestCase):
    def test_build_backtest_payload_uses_har_observed_fields(self):
        strategy = {
            "id": "123",
            "name": "demo",
            "code": "print(1)",
            "metadata": {"userId": "9", "accessControl": "0"},
        }
        payload = build_backtest_payload(
            strategy,
            start_date="2025-01-01",
            end_date="2025-01-31",
            capital="100000",
            frequency="day",
            token="t",
        )
        self.assertEqual(payload["algorithm[algorithmId]"], "123")
        self.assertEqual(payload["algorithm[userId]"], "9")
        self.assertEqual(payload["algorithm[code]"], base64.b64encode("print(1)".encode()).decode())
        self.assertEqual(payload["backtest[startTime]"], "2025-01-01 00:00:00")
        self.assertEqual(payload["backtest[endTime]"], "2025-01-31 23:59:59")
        self.assertEqual(payload["backtest[baseCapital]"], "100000")
        self.assertEqual(payload["backtest[frequency]"], "day")
        self.assertEqual(payload["backtest[type]"], "0")
        self.assertEqual(payload["encrType"], "base64")
        self.assertEqual(payload["token"], "t")

    def test_build_backtest_payload_can_use_compile_type(self):
        strategy = {"id": "123", "name": "demo", "code": "print(1)", "metadata": {"userId": "9"}}
        payload = build_backtest_payload(
            strategy,
            start_date="2025-01-01",
            end_date="2025-01-31",
            capital="100000",
            frequency="day",
            token="t",
            backtest_type="1",
        )
        self.assertEqual(payload["backtest[type]"], "1")

    def test_extract_backtest_id_supports_common_json_shapes(self):
        self.assertEqual(extract_backtest_id('{"backtestId":"b1"}'), "b1")
        self.assertEqual(extract_backtest_id('{"data":{"id":"b2"}}'), "b2")
        self.assertEqual(extract_backtest_id('{"data":{"backtestId":"b4"}}'), "b4")
        self.assertEqual(extract_backtest_id('{"url":"/algorithm/backtest/detail?backtestId=b3"}'), "b3")

    def test_parse_backtest_result_preserves_json_payload(self):
        result = parse_backtest_result('{"status":"done","returns":0.1}')
        self.assertEqual(result["status"], "done")
        self.assertEqual(result["raw"]["returns"], 0.1)

    def test_summarize_backtest_result_extracts_last_returns(self):
        raw = {
            "data": {
                "state": "2",
                "result": {
                    "benchmark": {"value": [1.0, 2.5]},
                    "overallReturn": {"value": [0.0, 3.5]},
                    "count": 2,
                },
            }
        }
        summary = summarize_backtest_result(raw)
        self.assertEqual(summary["state"], "2")
        self.assertEqual(summary["count"], 2)
        self.assertEqual(summary["overall_return"], 3.5)
        self.assertEqual(summary["benchmark_return"], 2.5)

    def test_summarize_backtest_detail_combines_useful_counts_and_metrics(self):
        detail = summarize_backtest_detail(
            status={"raw": {"data": {"status": "2", "needSeconds": 17.2}}},
            result={"summary": {"overall_return": 88.04, "benchmark_return": 22.17, "count": 320}},
            stats={"data": {"sharpe": 1.8, "max_drawdown": 0.19, "alpha": 0.45}},
            positions={"data": {"position": [{"stock": "A"}, {"stock": "B"}]}},
            transactions={"data": {"transaction": [{"stock": "A"}]}},
            logs={"data": {"logArr": ["log1", "log2"]}},
            errors={"data": {"logArr": []}},
        )
        self.assertEqual(detail["state"], "2")
        self.assertEqual(detail["need_seconds"], 17.2)
        self.assertEqual(detail["overall_return"], 88.04)
        self.assertEqual(detail["benchmark_return"], 22.17)
        self.assertEqual(detail["sharpe"], 1.8)
        self.assertEqual(detail["max_drawdown"], 0.19)
        self.assertEqual(detail["position_count"], 2)
        self.assertEqual(detail["transaction_count"], 1)
        self.assertEqual(detail["log_count"], 2)
        self.assertEqual(detail["error_count"], 0)

    def test_backtest_logs_uses_log_endpoint(self):
        class FakeHttpClient:
            base_url = "https://www.joinquant.com"

            def __init__(self):
                self.calls = []

            def post_form(self, path, data, params=None, headers=None):
                self.calls.append((path, data, params))

                class Response:
                    text = '{"data":{"logArr":["ok"],"offset":1,"max":true},"status":"0"}'

                    def json_or_none(self):
                        return {"data": {"logArr": ["ok"], "offset": 1, "max": True}, "status": "0"}

                return Response()

        service = BacktestService(FakeHttpClient(), strategy_service=None, token_provider=lambda: "t")
        logs = service.get_logs("bt1")
        self.assertEqual(logs["logs"], ["ok"])
        self.assertEqual(service.http_client.calls[0][0], "/algorithm/backtest/log")
        self.assertEqual(service.http_client.calls[0][2]["offset"], 0)

    def test_compile_strategy_uses_build_type_one_and_reports_errors(self):
        class FakeStrategyService:
            def get_strategy(self, strategy_id):
                return {
                    "id": strategy_id,
                    "name": "demo",
                    "code": "from __future__ import annotations",
                    "metadata": {"userId": "9", "accessControl": "0"},
                }

        class FakeHttpClient:
            base_url = "https://www.joinquant.com"

            def __init__(self):
                self.posts = []

            def post_form(self, path, data, params=None, headers=None):
                self.posts.append((path, data, params))

                class Response:
                    def __init__(self, text):
                        self.text = text

                    def json_or_none(self):
                        import json

                        return json.loads(self.text)

                if path == "/algorithm/index/build":
                    return Response('{"status":"0","data":{"backtestId":"bt-compile"}}')
                if path == "/algorithm/backtest/error":
                    return Response('{"status":"0","data":{"state":"3","logArr":["SyntaxError: bad syntax"]}}')
                if path == "/algorithm/backtest/result":
                    return Response('{"status":"0","data":{"state":"3"}}')
                return Response("{}")

        http = FakeHttpClient()
        service = BacktestService(http, FakeStrategyService(), token_provider=lambda: "t")
        result = service.compile_strategy("s1", "2025-01-01", "2025-01-31", "100000", "day", max_polls=1)
        self.assertFalse(result["compiled"])
        self.assertEqual(result["backtest_id"], "bt-compile")
        self.assertEqual(result["errors"], ["SyntaxError: bad syntax"])
        self.assertEqual(http.posts[0][0], "/algorithm/index/build")
        self.assertEqual(http.posts[0][1]["backtest[type]"], "1")

    def test_run_backtest_does_not_build_when_compile_fails(self):
        class FakeBacktestService(BacktestService):
            def __init__(self):
                self.build_calls = 0
                self.strategy_service = None
                self.http_client = None
                self.token_provider = lambda: "t"

            def compile_strategy(self, *args, **kwargs):
                return {"compiled": False, "backtest_id": "compile-1", "errors": ["SyntaxError"]}

            def _build_backtest(self, *args, **kwargs):
                self.build_calls += 1
                return {"backtest_id": "bt"}

        service = FakeBacktestService()
        result = service.run_backtest("s1", "2025-01-01", "2025-01-31", "100000", "day")
        self.assertIsNone(result["backtest_id"])
        self.assertEqual(result["compile"]["errors"], ["SyntaxError"])
        self.assertEqual(service.build_calls, 0)


if __name__ == "__main__":
    unittest.main()
