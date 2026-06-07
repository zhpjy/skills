import unittest

from jqcli_test_path import ensure_skill_jqcli_path

ensure_skill_jqcli_path()

from jqcli.output import error_response, sanitize_for_cli, success_response


class JqcliOutputTest(unittest.TestCase):
    def test_success_response_uses_ok_and_data(self):
        payload = success_response({"id": "demo"})
        self.assertEqual(payload, {"ok": True, "data": {"id": "demo"}})

    def test_error_response_uses_stable_shape(self):
        payload = error_response("AUTH_FAILED", "login failed", {"retry": False})
        self.assertEqual(payload["ok"], False)
        self.assertEqual(payload["error"]["code"], "AUTH_FAILED")
        self.assertEqual(payload["error"]["message"], "login failed")
        self.assertEqual(payload["error"]["detail"], {"retry": False})

    def test_success_response_can_remove_raw_recursively(self):
        payload = success_response(
            {"id": "demo", "raw": {"status": "0"}, "nested": {"raw": {"debug": True}, "value": 1}},
            include_raw=False,
        )
        self.assertEqual(payload, {"ok": True, "data": {"id": "demo", "nested": {"value": 1}}})

    def test_sanitize_for_cli_can_preserve_raw_when_requested(self):
        value = {"raw": {"status": "0"}, "items": [{"raw": {"status": "1"}, "id": 1}]}
        self.assertEqual(sanitize_for_cli(value, include_raw=True), value)


if __name__ == "__main__":
    unittest.main()
