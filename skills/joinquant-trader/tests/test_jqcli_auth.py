import unittest

from jqcli_test_path import ensure_skill_jqcli_path

ensure_skill_jqcli_path()

from jqcli.auth import AuthService
from jqcli.config import JoinQuantConfig
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
