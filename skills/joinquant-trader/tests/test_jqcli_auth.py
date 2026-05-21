import unittest

from jqcli_test_path import ensure_skill_jqcli_path

ensure_skill_jqcli_path()

from jqcli.auth import AuthError, AuthService, JoinQuantAuthClient, _truthy_login_value
from jqcli.config import JoinQuantConfig
from jqcli.http import HttpResponse
from jqcli.session import SessionState


class FakeClient:
    def __init__(self, login_result=False):
        self.calls = []
        self.session = SessionState()
        self.login_result = login_result

    def set_session(self, session):
        self.session = session

    def is_login(self):
        self.calls.append("is_login")
        return self.login_result

    def login(self, username, password):
        self.calls.append(("login", username, password))
        self.session = SessionState(cookies={"sid": "x"}, token="t")
        return self.session


class JqcliAuthTest(unittest.TestCase):
    def test_truthy_login_value_supports_nested_har_payload(self):
        payload = {
            "data": {"isLogin": 1},
            "status": "0",
            "code": "00000",
        }
        self.assertTrue(_truthy_login_value(payload))

    def test_auth_client_is_login_supports_nested_har_payload(self):
        class FakeHttpClient:
            def set_session(self, session):
                self.session = session

            def get(self, path, params=None):
                self.last_request = {"path": path, "params": params}
                return HttpResponse(
                    status=200,
                    url=f"https://www.joinquant.com{path}",
                    headers={},
                    text='{"data":{"isLogin":1},"status":"0","code":"00000","msg":""}',
                )

        client = JoinQuantAuthClient(FakeHttpClient())
        client.set_session(SessionState(cookies={"sid": "x"}, token="cached-token"))
        self.assertTrue(client.is_login())

    def test_auth_client_login_verifies_success_and_captures_token_cookie(self):
        class FakeHttpClient:
            def __init__(self):
                self.requests = []

            @property
            def base_url(self):
                return "https://www.joinquant.com"

            def set_session(self, session):
                self.session = session

            def get(self, path, params=None):
                self.requests.append(("GET", path, params))
                text = ""
                if path == "/user/index/isLogin":
                    text = '{"data":{"isLogin":1},"status":"0","code":"00000","msg":""}'
                return HttpResponse(status=200, url=f"{self.base_url}{path}", headers={}, text=text)

            def post_form(self, path, data, params=None, headers=None):
                self.requests.append(("POST", path, data, params, headers))
                return HttpResponse(status=200, url=f"{self.base_url}{path}", headers={}, text="")

            def get_cookie_value(self, name):
                return "token-from-cookie" if name == "token" else None

            def get_session(self, token=None):
                return SessionState(cookies={"PHPSESSID": "sid", "uid": "u"}, token=token)

        client = JoinQuantAuthClient(FakeHttpClient())
        state = client.login("u", "p")
        self.assertEqual(state.token, "token-from-cookie")
        self.assertEqual(state.cookies["PHPSESSID"], "sid")

    def test_auth_client_login_raises_when_server_returns_error_payload(self):
        class FakeHttpClient:
            @property
            def base_url(self):
                return "https://www.joinquant.com"

            def set_session(self, session):
                self.session = session

            def get(self, path, params=None):
                text = ""
                if path == "/user/index/isLogin":
                    text = '{"data":{"isLogin":0},"status":"0","code":"00000","msg":""}'
                return HttpResponse(status=200, url=f"{self.base_url}{path}", headers={}, text=text)

            def post_form(self, path, data, params=None, headers=None):
                return HttpResponse(
                    status=200,
                    url=f"{self.base_url}{path}",
                    headers={},
                    text='{"data":null,"status":"1","code":105,"msg":"登录次数过多"}',
                )

            def get_cookie_value(self, name):
                return None

            def get_session(self, token=None):
                return SessionState(cookies={"PHPSESSID": "sid", "uid": "u"}, token=token)

        client = JoinQuantAuthClient(FakeHttpClient())
        with self.assertRaisesRegex(AuthError, "登录次数过多"):
            client.login("u", "p")

    def test_ensure_session_logs_in_when_session_invalid(self):
        config = JoinQuantConfig(username="u", password="p")
        client = FakeClient(login_result=False)
        saved = []
        service = AuthService(
            config=config,
            client=client,
            load_state=lambda: SessionState(),
            save_state=saved.append,
        )
        state = service.ensure_session()
        self.assertEqual(state.token, "t")
        self.assertEqual(client.calls, ["is_login", ("login", "u", "p")])
        self.assertEqual(saved[0].cookies, {"sid": "x"})

    def test_ensure_session_reuses_valid_session(self):
        config = JoinQuantConfig(username="u", password="p")
        client = FakeClient(login_result=True)
        service = AuthService(
            config=config,
            client=client,
            load_state=lambda: SessionState(cookies={"sid": "old"}, token="old-token"),
            save_state=lambda state: None,
        )
        state = service.ensure_session()
        self.assertEqual(state.cookies, {"sid": "old"})
        self.assertEqual(client.calls, ["is_login"])


if __name__ == "__main__":
    unittest.main()
