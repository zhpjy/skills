import unittest

from jqcli_test_path import ensure_skill_jqcli_path

ensure_skill_jqcli_path()

from jqcli.http import HttpResponse
from jqcli.strategy import (
    StrategyService,
    build_strategy_save_payload,
    extract_strategy_id_from_new_response,
    extract_strategy_id_from_url,
    parse_directory_list,
    parse_strategy_detail,
    parse_strategy_list,
)


class JqcliStrategyTest(unittest.TestCase):
    def test_parse_strategy_list_reads_json_items(self):
        text = '{"data":[{"algorithmId":"123","name":"demo","updateTime":"2026-05-01"}]}'
        result = parse_strategy_list(text)
        self.assertEqual(result[0]["id"], "123")
        self.assertEqual(result[0]["name"], "demo")
        self.assertEqual(result[0]["updated_at"], "2026-05-01")

    def test_parse_strategy_list_reads_html_links(self):
        text = '<a href="/algorithm/index/edit?algorithmId=42ba5ef5cd3e41ac2e3a664188bad0a1">价值策略</a>'
        result = parse_strategy_list(text)
        self.assertEqual(
            result,
            [{"id": "42ba5ef5cd3e41ac2e3a664188bad0a1", "name": "价值策略", "updated_at": None}],
        )

    def test_parse_directory_list_reads_html_links(self):
        text = '<a class="folder" href="/algorithm/index/list?fId=121931">test</a>'
        result = parse_directory_list(text)
        self.assertEqual(result, [{"id": "121931", "name": "test"}])

    def test_directory_create_uses_har_observed_add_file_endpoint(self):
        http = FakeHttpClient(token_html='<script>window.tokenData = { value: "tok" }</script>')
        service = StrategyService(http, token_provider=lambda: "session-token")
        result = service.create_directory(name="test", parent_id="0")
        self.assertEqual(result["parent_id"], "0")
        self.assertEqual(http.posts[0]["path"], "/algorithm/index/AddFile")
        self.assertEqual(http.posts[0]["params"], {"pId": "0", "ajax": 1})
        self.assertEqual(http.posts[0]["data"], {"token": "tok", "name": "test", "ajax": 1})
        self.assertEqual(http.posts[0]["headers"]["Referer"], "https://www.joinquant.com/algorithm/index/list?fId=0")

    def test_directory_delete_uses_har_observed_del_file_endpoint(self):
        http = FakeHttpClient(token_html="")
        service = StrategyService(http, token_provider=lambda: "session-token")
        result = service.delete_directory(directory_id="121931", parent_id="0")
        self.assertEqual(result["directory_id"], "121931")
        self.assertEqual(http.posts[0]["path"], "/algorithm/index/DelFile")
        self.assertEqual(http.posts[0]["params"], {"fId": "121931", "ajax": 1})
        self.assertEqual(http.posts[0]["data"], {"undefined": "", "ajax": 1, "token": "session-token"})
        self.assertEqual(http.posts[0]["headers"]["Referer"], "https://www.joinquant.com/algorithm/index/list?fId=0")

    def test_create_strategy_uses_har_observed_folder_id(self):
        http = FakeHttpClient(
            token_html="",
            new_response=HttpResponse(
                status=302,
                url="https://www.joinquant.com/algorithm/index/edit?algorithmId=abc123&isNew=1&type=stock",
                headers={},
                text="",
            ),
            edit_html="""
            <input name="algorithm[algorithmId]" value="abc123">
            <input name="algorithm[userId]" value="user-1">
            <input name="algorithm[accessControl]" value="0">
            <input name="algorithm[name]" value="旧名字">
            <input name="backtest[type]" value="1">
            <input name="fontpref" value="default">
            <input name="themepref" value="ambiance">
            <input name="backtest[pyVersion]" value="3">
            <script>window.tokenData = { value: "tok-123" }</script>
            <textarea name="algorithm[code]">print(0)</textarea>
            """,
        )
        service = StrategyService(http, token_provider=lambda: "session-token")
        result = service.create_strategy(
            name="新策略",
            code="print(1)",
            start_date="2025-01-01",
            end_date="2025-01-31",
            capital="100000",
            frequency="day",
            folder_id="122341",
        )
        self.assertEqual(result["strategy_id"], "abc123")
        self.assertEqual(http.gets[0]["path"], "/algorithm/index/new")
        self.assertEqual(
            http.gets[0]["params"],
            {"restore": 0, "type": "stock", "baseCapital": "100000", "fId": "122341"},
        )
        self.assertEqual(http.posts[0]["path"], "/algorithm/index/save")
        self.assertEqual(http.posts[0]["data"]["algorithm[name]"], "新策略")

    def test_rename_strategy_uses_har_observed_set_name_endpoint(self):
        http = FakeHttpClient(
            token_html="",
            edit_html="""
            <input name="algorithm[algorithmId]" value="abc123">
            <input name="algorithm[name]" value="旧名字">
            <script>window.tokenData = { value: "tok-123" }</script>
            <textarea name="algorithm[code]">print(0)</textarea>
            """,
        )
        service = StrategyService(http, token_provider=lambda: "session-token")
        result = service.rename_strategy("abc123", "新名字")
        self.assertEqual(result["strategy_id"], "abc123")
        self.assertEqual(http.posts[0]["path"], "/algorithm/index/setName")
        self.assertEqual(
            http.posts[0]["data"],
            {"algorithmId": "abc123", "name": "新名字", "ajax": 1, "token": "tok-123"},
        )
        self.assertEqual(http.posts[0]["params"], {"ajax": 1})
        self.assertEqual(
            http.posts[0]["headers"]["Referer"],
            "https://www.joinquant.com/algorithm/index/edit?algorithmId=abc123",
        )

    def test_parse_strategy_detail_reads_json_code(self):
        text = '{"algorithm":{"algorithmId":"123","name":"demo","code":"print(1)","userId":"9"}}'
        result = parse_strategy_detail(text, strategy_id="123")
        self.assertEqual(result["id"], "123")
        self.assertEqual(result["name"], "demo")
        self.assertEqual(result["code"], "print(1)")
        self.assertEqual(result["metadata"]["userId"], "9")

    def test_parse_strategy_detail_returns_warning_when_code_missing(self):
        result = parse_strategy_detail("<html></html>", strategy_id="123")
        self.assertEqual(result["id"], "123")
        self.assertIsNone(result["code"])
        self.assertIn("code_not_found", result["warnings"])

    def test_parse_strategy_detail_reads_html_form_metadata(self):
        text = """
        <input name="algorithm[algorithmId]" value="abc123">
        <input name="algorithm[userId]" value="user-1">
        <input name="algorithm[accessControl]" value="0">
        <input name="algorithm[name]" value="策略A">
        <input name="fontpref" value="14px">
        <input name="themepref" value="monokai">
        <input name="backtest[pyVersion]" value="3">
        <script>window.tokenData = { name: "token", value: "tok-123" }</script>
        <textarea name="algorithm[code]">print(1)</textarea>
        """
        result = parse_strategy_detail(text, strategy_id="abc123")
        self.assertEqual(result["id"], "abc123")
        self.assertEqual(result["name"], "策略A")
        self.assertEqual(result["code"], "print(1)")
        self.assertEqual(result["metadata"]["userId"], "user-1")
        self.assertEqual(result["metadata"]["accessControl"], "0")
        self.assertEqual(result["metadata"]["fontpref"], "14px")
        self.assertEqual(result["metadata"]["themepref"], "monokai")
        self.assertEqual(result["metadata"]["pyVersion"], "3")
        self.assertEqual(result["metadata"]["token"], "tok-123")

    def test_parse_strategy_detail_does_not_treat_error_code_as_strategy_code(self):
        text = '{"status":"2","code":"20000","msg":"系统繁忙，请稍后重试","reason":""}'
        result = parse_strategy_detail(text, strategy_id="42ba5ef5cd3e41ac2e3a664188bad0a1")
        self.assertEqual(result["id"], "42ba5ef5cd3e41ac2e3a664188bad0a1")
        self.assertIsNone(result["code"])
        self.assertIn("remote_error", result["warnings"])
        self.assertEqual(result["metadata"]["remote_status"], "2")

    def test_extract_strategy_id_from_redirect_url(self):
        url = "https://www.joinquant.com/algorithm/index/edit?algorithmId=abc123&isNew=1&type=stock"
        self.assertEqual(extract_strategy_id_from_url(url), "abc123")

    def test_extract_strategy_id_from_new_response_redirect(self):
        text = '{"redirect":"/algorithm/index/edit?algorithmId=c654&isNew=1","status":"0"}'
        self.assertEqual(extract_strategy_id_from_new_response("https://www.joinquant.com/algorithm/index/new", text), "c654")

    def test_build_strategy_save_payload_uses_base64_code_and_metadata(self):
        strategy = {
            "id": "abc123",
            "name": "old",
            "code": "print(0)",
            "metadata": {
                "userId": "user-1",
                "accessControl": "0",
                "backtestType": "1",
                "fontpref": "default",
                "themepref": "ambiance",
                "pyVersion": "3",
                "token": "tok",
            },
        }
        payload = build_strategy_save_payload(
            strategy,
            name="new-name",
            code="print(1)",
            start_date="2025-01-01",
            end_date="2025-01-31",
            capital="100000",
            frequency="day",
        )
        self.assertEqual(payload["algorithm[algorithmId]"], "abc123")
        self.assertEqual(payload["algorithm[userId]"], "user-1")
        self.assertEqual(payload["algorithm[name]"], "new-name")
        self.assertEqual(payload["algorithm[code]"], "cHJpbnQoMSk=")
        self.assertEqual(payload["backtest[startTime]"], "2025-01-01")
        self.assertEqual(payload["backtest[endTime]"], "2025-01-31")
        self.assertEqual(payload["encrType"], "base64")
        self.assertEqual(payload["token"], "tok")


class FakeHttpClient:
    base_url = "https://www.joinquant.com"

    def __init__(self, token_html: str, new_response: HttpResponse | None = None, edit_html: str | None = None):
        self.token_html = token_html
        self.new_response = new_response
        self.edit_html = edit_html if edit_html is not None else token_html
        self.gets = []
        self.posts = []

    def get(self, path, params=None):
        self.gets.append({"path": path, "params": params})
        if path == "/algorithm/index/new" and self.new_response is not None:
            return self.new_response
        text = self.edit_html if path == "/algorithm/index/edit" else self.token_html
        return HttpResponse(status=200, url=f"{self.base_url}{path}", headers={}, text=text)

    def post_form(self, path, data, params=None, headers=None):
        self.posts.append({"path": path, "data": data, "params": params, "headers": headers or {}})
        return HttpResponse(status=200, url=f"{self.base_url}{path}", headers={}, text="")


if __name__ == "__main__":
    unittest.main()
