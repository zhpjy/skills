import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]


class SyncVendorTests(unittest.TestCase):
    def test_write_state_creates_parent_directory(self) -> None:
        from tools.sync_vendor import write_state

        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)

            state_path = write_state(
                repo_root,
                "vendor-source",
                {
                    "last_synced_ref": "abc123",
                    "last_synced_at": "2026-04-29T00:00:00+00:00",
                    "last_source_count": 1,
                    "last_synced_count": 1,
                },
            )

            self.assertEqual(
                json.loads(state_path.read_text(encoding="utf-8")),
                {
                    "name": "vendor-source",
                    "kind": "vendor-state",
                    "last_synced_ref": "abc123",
                    "last_synced_at": "2026-04-29T00:00:00+00:00",
                    "last_source_count": 1,
                    "last_synced_count": 1,
                },
            )

    def test_load_source_config_reads_named_registry_entry(self) -> None:
        from tools.sync_vendor import load_source_config

        source = load_source_config(REPO_ROOT, "superpowers")

        self.assertEqual(source["name"], "superpowers")
        self.assertEqual(source["kind"], "vendor-source")
        self.assertEqual(source["sync"]["target_path"], "vendor/superpowers/skills")

    def test_load_source_config_rejects_nested_source_name(self) -> None:
        from tools.sync_vendor import load_source_config

        with self.assertRaisesRegex(
            ValueError,
            "source_name must be a single file name",
        ):
            load_source_config(REPO_ROOT, "../escape")

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

    def test_collect_sync_candidates_skips_symlink_directories(self) -> None:
        from tools.sync_vendor import collect_sync_candidates

        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir)
            allowed = source_root / "allowed"
            linked = source_root / "linked"

            allowed.mkdir()
            (allowed / "SKILL.md").write_text("allowed\n", encoding="utf-8")
            try:
                linked.symlink_to(allowed, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlink unsupported: {exc}")

            candidates = collect_sync_candidates(source_root, set())

            self.assertEqual(candidates, [allowed])

    def test_collect_sync_candidates_skips_skill_directories_with_nested_symlinks(self) -> None:
        from tools.sync_vendor import collect_sync_candidates

        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir)
            allowed = source_root / "allowed"
            linked = source_root / "linked"
            outside = source_root / "outside.txt"

            allowed.mkdir()
            linked.mkdir()
            (allowed / "SKILL.md").write_text("allowed\n", encoding="utf-8")
            (linked / "SKILL.md").write_text("linked\n", encoding="utf-8")
            outside.write_text("outside\n", encoding="utf-8")
            try:
                (linked / "secret.txt").symlink_to(outside)
            except OSError as exc:
                self.skipTest(f"symlink unsupported: {exc}")

            candidates = collect_sync_candidates(source_root, set())

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

    def test_sync_vendor_source_skips_symlink_entries_from_upstream(self) -> None:
        from tools.sync_vendor import sync_vendor_source

        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            (repo_root / "registry" / "sources").mkdir(parents=True)
            (repo_root / "registry" / "state").mkdir(parents=True)
            target_root = repo_root / "vendor" / "vendor-source" / "skills"

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
            outside_skill = upstream_worktree / "outside-skill"
            (source_root / "alpha").mkdir(parents=True)
            outside_skill.mkdir(parents=True)
            (source_root / "alpha" / "SKILL.md").write_text("alpha\n", encoding="utf-8")
            (outside_skill / "SKILL.md").write_text("outside\n", encoding="utf-8")
            linked = source_root / "linked-outside"
            try:
                linked.symlink_to(Path("..") / "outside-skill", target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlink unsupported: {exc}")
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

            state = sync_vendor_source(repo_root, "vendor-source")

            self.assertEqual(state["last_source_count"], 1)
            self.assertEqual(state["last_synced_count"], 1)
            self.assertTrue((target_root / "alpha" / "SKILL.md").is_file())
            self.assertFalse((target_root / "linked-outside").exists())

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

    def test_resolve_vendor_target_path_rejects_symlink_escape(self) -> None:
        from tools.sync_vendor import resolve_vendor_target_path

        with tempfile.TemporaryDirectory() as temp_dir, tempfile.TemporaryDirectory() as outside_dir:
            repo_root = Path(temp_dir)
            targets = [
                Path(outside_dir),
                repo_root / "registry",
            ]

            for symlink_target in targets:
                with self.subTest(symlink_target=str(symlink_target)):
                    if (repo_root / "vendor").exists() or (repo_root / "vendor").is_symlink():
                        (repo_root / "vendor").unlink()
                    if symlink_target == repo_root / "registry":
                        symlink_target.mkdir(exist_ok=True)
                    try:
                        (repo_root / "vendor").symlink_to(symlink_target, target_is_directory=True)
                    except OSError as exc:
                        self.skipTest(f"symlink unsupported: {exc}")

                    with self.assertRaisesRegex(
                        ValueError,
                        "sync.target_path must stay within the repository vendor/ tree",
                    ):
                        resolve_vendor_target_path(repo_root, "vendor/vendor-source/skills")

    def test_sync_vendor_source_rejects_target_path_vendor_root_or_equivalent(self) -> None:
        from tools.sync_vendor import sync_vendor_source

        for target_path in ("vendor", "vendor/vendor-source/.."):
            with self.subTest(target_path=target_path):
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
                            "target_path": target_path,
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
                        "sync.target_path must include a vendor source directory",
                    ):
                        sync_vendor_source(repo_root, "vendor-source")

    def test_sync_vendor_source_rejects_source_path_outside_clone_tree(self) -> None:
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
                    "source_path": "../skills",
                    "target_path": "vendor/vendor-source/skills",
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
                "sync.source_path must be a relative path within the cloned repository",
            ):
                sync_vendor_source(repo_root, "vendor-source")

    def test_sync_vendor_source_rejects_source_path_symlink_outside_clone_tree(self) -> None:
        from tools.sync_vendor import sync_vendor_source

        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            (repo_root / "registry" / "sources").mkdir(parents=True)
            (repo_root / "registry" / "state").mkdir(parents=True)

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

            outside_dir = repo_root / "external-source"
            outside_dir.mkdir()
            (outside_dir / "alpha").mkdir()
            (outside_dir / "alpha" / "SKILL.md").write_text("alpha\n", encoding="utf-8")
            try:
                (upstream_worktree / "skills").symlink_to(outside_dir, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlink unsupported: {exc}")

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
                "sync.source_path must resolve to a directory within the cloned repository",
            ):
                sync_vendor_source(repo_root, "vendor-source")

    def test_sync_vendor_source_rejects_unsupported_sync_mode(self) -> None:
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
                    "mode": "file",
                    "source_path": "skills",
                    "target_path": "vendor/vendor-source/skills",
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
                "sync.mode must be 'directory'",
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
