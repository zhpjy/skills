from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from jqcli_test_path import ensure_skill_jqcli_path

ensure_skill_jqcli_path()

from jqcli.session import SessionState, load_session, save_session


class JqcliSessionTest(unittest.TestCase):
    def test_load_missing_session_returns_empty_state(self):
        with TemporaryDirectory() as temp_dir:
            state = load_session(Path(temp_dir) / "session.json")
        self.assertEqual(state.cookies, {})
        self.assertIsNone(state.token)

    def test_save_and_load_session(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "session.json"
            save_session(path, SessionState(cookies={"a": "b"}, token="t"))
            loaded = load_session(path)
        self.assertEqual(loaded.cookies, {"a": "b"})
        self.assertEqual(loaded.token, "t")

    def test_save_session_does_not_persist_password(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "session.json"
            save_session(path, SessionState(cookies={"sid": "x"}, token="t"))
            text = path.read_text(encoding="utf-8")
        self.assertNotIn("password", text.lower())
        self.assertNotIn("pwd", text.lower())


if __name__ == "__main__":
    unittest.main()
