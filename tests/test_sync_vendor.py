import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]


class SyncVendorTests(unittest.TestCase):
    def test_load_source_config_reads_named_registry_entry(self) -> None:
        from tools.sync_vendor import load_source_config

        source = load_source_config(REPO_ROOT, "superpowers")

        self.assertEqual(source["name"], "superpowers")
        self.assertEqual(source["kind"], "vendor-source")
        self.assertEqual(source["sync"]["target_path"], "vendor/superpowers/skills")

    def test_collect_sync_candidates_filters_blacklist_and_requires_skill_file(self) -> None:
        from tools.sync_vendor import collect_sync_candidates

        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir)
            allowed = source_root / "allowed"
            blacklisted = source_root / ".experimental"
            missing_skill = source_root / "missing-skill"
            not_a_dir = source_root / "README.md"

            allowed.mkdir()
            blacklisted.mkdir()
            missing_skill.mkdir()
            (allowed / "SKILL.md").write_text("allowed\n", encoding="utf-8")
            (blacklisted / "SKILL.md").write_text("blocked\n", encoding="utf-8")
            not_a_dir.write_text("note\n", encoding="utf-8")

            candidates = collect_sync_candidates(source_root, {".experimental"})

            self.assertEqual(candidates, [allowed])

    def test_sync_vendor_source_clones_overwrites_target_and_writes_state(self) -> None:
        from tools.sync_vendor import sync_vendor_source

        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            (repo_root / "registry" / "sources").mkdir(parents=True)
            (repo_root / "registry" / "state").mkdir(parents=True)
            target_root = repo_root / "vendor" / "vendor-source" / "skills"
            target_root.mkdir(parents=True)
            stale_dir = target_root / "stale"
            stale_dir.mkdir()
            (stale_dir / "SKILL.md").write_text("stale\n", encoding="utf-8")

            upstream_worktree = repo_root / "upstream-worktree"
            upstream_worktree.mkdir()
            subprocess.run(
                ["git", "init", "-b", "main"],
                cwd=upstream_worktree,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=upstream_worktree,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=upstream_worktree,
                check=True,
            )
            source_root = upstream_worktree / "skills"
            (source_root / "alpha").mkdir(parents=True)
            (source_root / "beta").mkdir(parents=True)
            (source_root / ".experimental").mkdir(parents=True)
            (source_root / "alpha" / "SKILL.md").write_text("alpha\n", encoding="utf-8")
            (source_root / "beta" / "SKILL.md").write_text("beta\n", encoding="utf-8")
            (source_root / ".experimental" / "SKILL.md").write_text("blocked\n", encoding="utf-8")
            (source_root / "notes").mkdir(parents=True)
            (source_root / "notes" / "README.md").write_text("not a skill\n", encoding="utf-8")
            subprocess.run(
                ["git", "add", "."],
                cwd=upstream_worktree,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["git", "commit", "-m", "seed vendor repo"],
                cwd=upstream_worktree,
                check=True,
                capture_output=True,
                text=True,
            )
            resolved_ref = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=upstream_worktree,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()

            source_config = {
                "name": "vendor-source",
                "kind": "vendor-source",
                "upstream": {
                    "repo": str(upstream_worktree),
                    "ref": "main",
                },
                "sync": {
                    "mode": "directory",
                    "source_path": "skills",
                    "target_path": "vendor/vendor-source/skills",
                },
                "filter": {
                    "default_policy": "include-all",
                    "blacklist": [".experimental"],
                },
                "local": {
                    "managed": True,
                    "editable": False,
                },
            }
            (repo_root / "registry" / "sources" / "vendor-source.json").write_text(
                json.dumps(source_config, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            state = sync_vendor_source(repo_root, "vendor-source")

            self.assertEqual(state["last_synced_ref"], resolved_ref)
            self.assertIsInstance(state["last_synced_at"], str)
            self.assertEqual(state["last_source_count"], 4)
            self.assertEqual(state["last_synced_count"], 2)
            self.assertEqual(
                (target_root / "alpha" / "SKILL.md").read_text(encoding="utf-8"),
                "alpha\n",
            )
            self.assertEqual(
                (target_root / "beta" / "SKILL.md").read_text(encoding="utf-8"),
                "beta\n",
            )
            self.assertFalse((target_root / ".experimental").exists())
            self.assertFalse((target_root / "stale").exists())

            persisted_state = json.loads(
                (repo_root / "registry" / "state" / "vendor-source.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(persisted_state["name"], "vendor-source")
            self.assertEqual(persisted_state["kind"], "vendor-state")
            self.assertEqual(persisted_state["last_synced_ref"], resolved_ref)
            self.assertEqual(persisted_state["last_source_count"], 4)
            self.assertEqual(persisted_state["last_synced_count"], 2)

    def test_sync_vendor_source_rejects_target_path_outside_vendor_tree(self) -> None:
        from tools.sync_vendor import sync_vendor_source

        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            (repo_root / "registry" / "sources").mkdir(parents=True)
            (repo_root / "registry" / "state").mkdir(parents=True)

            source_config = {
                "name": "vendor-source",
                "kind": "vendor-source",
                "upstream": {
                    "repo": "https://example.invalid/repo.git",
                    "ref": "main",
                },
                "sync": {
                    "mode": "directory",
                    "source_path": "skills",
                    "target_path": ".agents/skills/escape",
                },
                "filter": {
                    "default_policy": "include-all",
                    "blacklist": [],
                },
                "local": {
                    "managed": True,
                    "editable": False,
                },
            }
            (repo_root / "registry" / "sources" / "vendor-source.json").write_text(
                json.dumps(source_config, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError,
                "sync.target_path must be a relative path under vendor/",
            ):
                sync_vendor_source(repo_root, "vendor-source")

    @mock.patch("tools.sync_vendor.sync_vendor_source")
    def test_main_syncs_single_source(self, sync_vendor_source_mock: mock.Mock) -> None:
        from tools.sync_vendor import main

        exit_code = main(["--source", "superpowers"])

        self.assertEqual(exit_code, 0)
        sync_vendor_source_mock.assert_called_once_with(REPO_ROOT, "superpowers")

    @mock.patch("tools.sync_vendor.iter_source_names", return_value=["superpowers", "vendor-source"])
    @mock.patch("tools.sync_vendor.sync_vendor_source")
    def test_main_syncs_all_sources(
        self,
        sync_vendor_source_mock: mock.Mock,
        iter_source_names_mock: mock.Mock,
    ) -> None:
        from tools.sync_vendor import main

        exit_code = main(["--all"])

        self.assertEqual(exit_code, 0)
        iter_source_names_mock.assert_called_once_with(REPO_ROOT)
        self.assertEqual(
            sync_vendor_source_mock.call_args_list,
            [
                mock.call(REPO_ROOT, "superpowers"),
                mock.call(REPO_ROOT, "vendor-source"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
