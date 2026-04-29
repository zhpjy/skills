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
        self.assertEqual(source["kind"], "vendor-source")
        self.assertEqual(
            source["upstream"]["repo"],
            "https://github.com/obra/superpowers.git",
        )
        self.assertEqual(source["upstream"]["ref"], "main")
        self.assertEqual(
            source["sync"],
            {
                "mode": "directory",
                "source_path": "skills",
                "target_path": "vendor/superpowers/skills",
            },
        )
        self.assertEqual(
            source["filter"],
            {
                "default_policy": "include-all",
                "blacklist": [".experimental"],
            },
        )
        self.assertEqual(
            source["local"],
            {
                "managed": True,
                "editable": False,
            },
        )

    def test_superpowers_state_matches_vendor_state_shape(self) -> None:
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))

        self.assertEqual(state["name"], "superpowers")
        self.assertEqual(state["kind"], "vendor-state")
        self.assertIsNone(state["last_synced_ref"])
        self.assertIsNone(state["last_synced_at"])
        self.assertEqual(state["last_source_count"], 0)
        self.assertEqual(state["last_synced_count"], 0)

    def test_superpowers_bundle_keeps_minimal_initial_manifest(self) -> None:
        bundle = json.loads(BUNDLE_PATH.read_text(encoding="utf-8"))

        self.assertEqual(bundle["name"], "superpowers-codex")
        self.assertEqual(bundle["kind"], "bundle")
        self.assertEqual(bundle["agent"], "codex")
        self.assertEqual(
            bundle["description"],
            "Superpowers bundle for Codex projects",
        )
        self.assertEqual(
            bundle["skills"],
            [{"source": "local", "path": "skill-manager"}],
        )

    def test_vendor_directory_has_placeholder_file(self) -> None:
        self.assertTrue(VENDOR_KEEP_PATH.exists())


if __name__ == "__main__":
    unittest.main()
