import unittest

from jqcli_test_path import ensure_skill_jqcli_path

ensure_skill_jqcli_path()

from jqcli.output import error_response, success_response


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


if __name__ == "__main__":
    unittest.main()
