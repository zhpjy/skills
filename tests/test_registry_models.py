import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = REPO_ROOT / "registry" / "sources" / "superpowers.json"
STATE_PATH = REPO_ROOT / "registry" / "state" / "superpowers.json"
BUNDLE_PATH = REPO_ROOT / "bundles" / "superpowers-codex.json"
VENDOR_KEEP_PATH = REPO_ROOT / "vendor" / ".gitkeep"


class RegistryModelTests(unittest.TestCase):
    def test_superpowers_source_config_contains_expected_fields(self) -> None:
        source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))

        self.assertEqual(source["name"], "superpowers")
        self.assertEqual(source["kind"], "git")
        self.assertEqual(source["default_bundle"], "superpowers-codex")
        self.assertEqual(source["vendor_dir"], "vendor/superpowers")
        self.assertEqual(source["state_file"], "registry/state/superpowers.json")
        self.assertEqual(source["upstream"]["branch"], "main")
        self.assertTrue(source["upstream"]["repo_url"].startswith("https://"))
        self.assertEqual(
            source["bundles"],
            ["bundles/superpowers-codex.json"],
        )

    def test_superpowers_state_and_bundle_reference_source_consistently(self) -> None:
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        bundle = json.loads(BUNDLE_PATH.read_text(encoding="utf-8"))

        self.assertEqual(state["source"], "superpowers")
        self.assertEqual(state["status"], "pending")
        self.assertIsNone(state["last_synced_at"])
        self.assertIsNone(state["revision"])

        self.assertEqual(bundle["name"], "superpowers-codex")
        self.assertEqual(bundle["source"], "superpowers")
        self.assertEqual(bundle["install_root"], ".agents/skills")
        self.assertIn("skill-manager", bundle["skills"])
        self.assertIn("brainstorming", bundle["skills"])

    def test_vendor_directory_has_placeholder_file(self) -> None:
        self.assertTrue(VENDOR_KEEP_PATH.exists())


if __name__ == "__main__":
    unittest.main()
