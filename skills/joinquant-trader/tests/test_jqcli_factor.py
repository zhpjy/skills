import unittest

from jqcli_test_path import ensure_skill_jqcli_path

ensure_skill_jqcli_path()

from jqcli.factor import FactorService
from jqcli.http import HttpResponse


class JqcliFactorTest(unittest.TestCase):
    def test_list_factors_uses_har_observed_get_list_endpoint(self):
        http = FakeHttpClient(
            {
                "/factorlib/index/getList": {
                    "status": "0",
                    "code": "20000",
                    "msg": "",
                    "data": [
                        {"factor_id": "f1", "name": "PSY", "annual_ex_return_1q": "0.11"},
                        {"factor_id": "f2", "name": "RSI", "annual_ex_return_1q": "0.09"},
                    ],
                }
            }
        )
        service = FactorService(http)
        result = service.list_factors(
            category_id="0",
            universe_type="hs300",
            time_range="3y",
            commision_fee="8",
            skip_paused="0",
        )
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["filters"]["universe_type"], "hs300")
        self.assertEqual(result["sample"][0]["factor_id"], "f1")
        self.assertEqual(result["sample"][0]["annual_ex_return_1q"], "0.11")
        self.assertTrue(result["full_available"])
        self.assertEqual(
            http.gets[0],
            (
                "/factorlib/index/getList",
                {
                    "categoryId": "0",
                    "universeType": "hs300",
                    "timeRange": "3y",
                    "commisionFee": "8",
                    "skipPaused": "0",
                },
            ),
        )

    def test_list_factors_can_return_full_payload_when_requested(self):
        http = FakeHttpClient(
            {
                "/factorlib/index/getList": {
                    "status": "0",
                    "data": [{"factor_id": "f1", "name": "PSY", "extra": "kept"}],
                }
            }
        )
        service = FactorService(http)
        result = service.list_factors(full=True)
        self.assertEqual(result["factors"][0]["extra"], "kept")
        self.assertEqual(result["count"], 1)

    def test_get_detail_combines_lightweight_payloads_by_default(self):
        http = FakeHttpClient(
            {
                "/factorlib/index/getInfo": {"status": "0", "data": {"id": "inner", "name": "PSY"}},
                "/factorlib/index/getPerformance": {"status": "0", "data": {"annual_return_1q": "0.1"}},
                "/factorlib/index/getFactorStockList": {
                    "status": "0",
                    "data": {
                        "smallest": [{"code": "000001.XSHE"}],
                        "largest": [{"code": "600000.XSHG"}, {"code": "600519.XSHG"}],
                        "updateDate": "2026年05月06日",
                    },
                },
            }
        )
        service = FactorService(http)
        result = service.get_detail(
            factor_id="f1",
            universe_type="hs300",
            time_range="3y",
            commision_fee="8",
            skip_paused="0",
            side="long",
        )
        self.assertEqual(result["id"], "f1")
        self.assertEqual(result["info"]["name"], "PSY")
        self.assertEqual(result["performance"]["annual_return_1q"], "0.1")
        self.assertNotIn("daily_stats", result)
        self.assertNotIn("ic", result)
        self.assertNotIn("turnovers", result)
        self.assertEqual(result["stock_list"]["update_date"], "2026年05月06日")
        self.assertEqual(result["stock_list"]["largest"]["count"], 2)
        self.assertEqual(result["stock_list"]["largest"]["sample"][0]["code"], "600000.XSHG")
        self.assertEqual(http.gets[0], ("/factorlib/index/getInfo", {"id": "f1", "isFactorShare": "0"}))

    def test_get_detail_can_include_large_series_when_requested(self):
        http = FakeHttpClient(
            {
                "/factorlib/index/getInfo": {"status": "0", "data": {"id": "inner", "name": "PSY"}},
                "/factorlib/index/getPerformance": {"status": "0", "data": {"annual_return_1q": "0.1"}},
                "/factorlib/index/getDailyStats": {"status": "0", "data": [[["date", "return"]]]},
                "/factorlib/index/getIC": {"status": "0", "data": {"IC": [[1], [2]]}},
                "/factorlib/index/getTurnovers": {"status": "0", "data": {"turnover": [[1], [2]]}},
                "/factorlib/index/getFactorStockList": {
                    "status": "0",
                    "data": {"smallest": [], "largest": [], "updateDate": "2026年05月06日"},
                },
            }
        )
        service = FactorService(http)
        result = service.get_detail(
            factor_id="f1",
            universe_type="hs300",
            time_range="3y",
            commision_fee="8",
            skip_paused="0",
            side="long",
            include_series=True,
        )
        self.assertEqual(result["daily_stats"], [[["date", "return"]]])
        self.assertEqual(result["ic"], {"IC": [[1], [2]]})
        self.assertEqual(result["turnovers"], {"turnover": [[1], [2]]})

    def test_get_detail_can_return_full_stock_lists_when_requested(self):
        http = FakeHttpClient(
            {
                "/factorlib/index/getInfo": {"status": "0", "data": {"id": "inner", "name": "PSY"}},
                "/factorlib/index/getPerformance": {"status": "0", "data": {"annual_return_1q": "0.1"}},
                "/factorlib/index/getFactorStockList": {
                    "status": "0",
                    "data": {
                        "smallest": [{"code": "000001.XSHE"}],
                        "largest": [{"code": "600000.XSHG"}],
                        "updateDate": "2026年05月06日",
                    },
                },
            }
        )
        service = FactorService(http)
        result = service.get_detail(
            factor_id="f1",
            universe_type="hs300",
            time_range="3y",
            commision_fee="8",
            skip_paused="0",
            full=True,
        )
        self.assertEqual(result["stock_list"]["updateDate"], "2026年05月06日")
        self.assertEqual(result["stock_list"]["largest"][0]["code"], "600000.XSHG")

    def test_get_performance_omits_empty_optional_turnover_filters(self):
        http = FakeHttpClient({"/factorlib/index/getPerformance": {"status": "0", "data": {"x": "y"}}})
        service = FactorService(http)
        result = service.get_performance(
            factor_id="f1",
            universe_type="hs300",
            time_range="3y",
            commision_fee="8",
            skip_paused="0",
        )
        self.assertEqual(result, {"x": "y"})
        self.assertEqual(
            http.gets[0],
            (
                "/factorlib/index/getPerformance",
                {
                    "id": "f1",
                    "universeType": "hs300",
                    "timeRange": "3y",
                    "commisionFee": "8",
                    "skipPaused": "0",
                    "isFactorShare": "0",
                },
            ),
        )

    def test_get_stock_list_is_compact_by_default(self):
        http = FakeHttpClient(
            {
                "/factorlib/index/getFactorStockList": {
                    "status": "0",
                    "data": {
                        "smallest": [{"code": "000001.XSHE"}, {"code": "000002.XSHE"}],
                        "largest": [{"code": "600000.XSHG"}],
                        "updateDate": "2026年05月06日",
                    },
                }
            }
        )
        service = FactorService(http)
        result = service.get_stock_list(factor_id="f1", universe_type="hs300")
        self.assertEqual(result["largest"]["count"], 1)
        self.assertEqual(result["smallest"]["count"], 2)
        self.assertTrue(result["full_available"])

    def test_get_stock_list_can_return_full_payload_when_requested(self):
        http = FakeHttpClient(
            {
                "/factorlib/index/getFactorStockList": {
                    "status": "0",
                    "data": {"smallest": [{"code": "000001.XSHE"}], "largest": [], "updateDate": "2026年05月06日"},
                }
            }
        )
        service = FactorService(http)
        result = service.get_stock_list(factor_id="f1", universe_type="hs300", full=True)
        self.assertEqual(result["updateDate"], "2026年05月06日")
        self.assertEqual(result["smallest"][0]["code"], "000001.XSHE")


class FakeHttpClient:
    base_url = "https://www.joinquant.com"

    def __init__(self, payloads):
        self.payloads = payloads
        self.gets = []

    def get(self, path, params=None):
        self.gets.append((path, params or {}))
        return HttpResponse(status=200, url=f"{self.base_url}{path}", headers={}, text=self._text(path))

    def _text(self, path):
        import json

        return json.dumps(self.payloads[path], ensure_ascii=False)


if __name__ == "__main__":
    unittest.main()
