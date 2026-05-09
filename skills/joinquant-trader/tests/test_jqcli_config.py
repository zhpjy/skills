from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from jqcli_test_path import ensure_skill_jqcli_path

ensure_skill_jqcli_path()

from jqcli.config import ConfigError, JoinQuantConfig, load_config, redact_mapping


class JqcliConfigTest(unittest.TestCase):
    def test_load_config_reads_env_file(self):
        with TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text("JOINQUANT_USERNAME=u\nJOINQUANT_PASSWORD=p\n", encoding="utf-8")
            config = load_config(env_path)
        self.assertEqual(config.username, "u")
        self.assertEqual(config.password, "p")
        self.assertEqual(config.base_url, "https://www.joinquant.com")

    def test_load_config_uses_custom_base_url(self):
        with TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text(
                "JOINQUANT_USERNAME=u\nJOINQUANT_PASSWORD=p\nJOINQUANT_BASE_URL=https://example.test\n",
                encoding="utf-8",
            )
            config = load_config(env_path)
        self.assertEqual(config.base_url, "https://example.test")

    def test_load_config_requires_credentials(self):
        with TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text("JOINQUANT_USERNAME=u\n", encoding="utf-8")
            with self.assertRaises(ConfigError):
                load_config(env_path)

    def test_redact_mapping_hides_sensitive_values(self):
        result = redact_mapping({"username": "u", "pwd": "p", "safe": "x", "token": "t"})
        self.assertEqual(result["username"], "<redacted>")
        self.assertEqual(result["pwd"], "<redacted>")
        self.assertEqual(result["token"], "<redacted>")
        self.assertEqual(result["safe"], "x")

    def test_config_defaults_state_dir_under_skill(self):
        config = JoinQuantConfig(username="u", password="p")
        self.assertEqual(config.state_dir.name, ".state")
        self.assertEqual(config.state_dir.parent.name, "joinquant-trader")

    def test_load_config_defaults_to_skill_env(self):
        with TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text("JOINQUANT_USERNAME=u\nJOINQUANT_PASSWORD=p\n", encoding="utf-8")
            with patch("jqcli.config._default_env_path", return_value=env_path), patch.dict("os.environ", {}, clear=True):
                config = load_config()
        self.assertEqual(config.username, "u")

    def test_load_config_can_use_explicit_env_file_variable(self):
        with TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / "jq.env"
            env_path.write_text("JOINQUANT_USERNAME=u\nJOINQUANT_PASSWORD=p\n", encoding="utf-8")
            with patch.dict("os.environ", {"JQCLI_ENV_FILE": str(env_path)}, clear=True):
                config = load_config()
        self.assertEqual(config.username, "u")

    def test_load_config_does_not_fallback_to_joinquant_env(self):
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            legacy_env_path = temp_root / "joinquant" / ".env"
            legacy_env_path.parent.mkdir()
            legacy_env_path.write_text("JOINQUANT_USERNAME=u\nJOINQUANT_PASSWORD=p\n", encoding="utf-8")
            missing_default_env = temp_root / "missing" / ".env"
            with patch("jqcli.config._default_env_path", return_value=missing_default_env), patch.dict("os.environ", {}, clear=True):
                with self.assertRaises(ConfigError):
                    load_config()


if __name__ == "__main__":
    unittest.main()
