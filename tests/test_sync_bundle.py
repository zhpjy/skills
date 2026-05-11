import contextlib
import importlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


def load_sync_bundle_module(test_case: unittest.TestCase):
    try:
        return importlib.import_module("tools.sync_bundle")
    except ModuleNotFoundError:
        test_case.fail(
            "missing implementation module 'tools.sync_bundle'; "
            "create tools/sync_bundle.py with resolve_bundle_skill_paths(), "
            "sync_bundle(), and main()"
        )


class SyncBundleTests(unittest.TestCase):
    def test_resolve_bundle_skill_paths_supports_local_and_vendor_sources(self) -> None:
        module = load_sync_bundle_module(self)

        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            (repo_root / "skills" / "skill-manager").mkdir(parents=True)
            (repo_root / "vendor" / "superpowers" / "skills" / "brainstorming").mkdir(
                parents=True
            )

            bundle = {
                "skills": [
                    {"source": "local", "path": "skill-manager"},
                    {"source": "vendor/superpowers", "path": "brainstorming"},
                ]
            }

            resolved = module.resolve_bundle_skill_paths(bundle, repo_root)

            self.assertEqual(
                resolved,
                [
                    ("skill-manager", repo_root / "skills" / "skill-manager"),
                    (
                        "brainstorming",
                        repo_root
                        / "vendor"
                        / "superpowers"
                        / "skills"
                        / "brainstorming",
                    ),
                ],
            )

    def test_sync_bundle_copies_skills_writes_bundle_state_and_repo_info(self) -> None:
        module = load_sync_bundle_module(self)

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            repo_root = workspace / "repo"
            project_root = workspace / "project"
            project_root.mkdir()

            manager_source = repo_root / "skills" / "skill-manager"
            manager_source.mkdir(parents=True)
            (manager_source / "SKILL.md").write_text("# manager\n", encoding="utf-8")

            vendor_skill_source = (
                repo_root
                / "vendor"
                / "superpowers"
                / "skills"
                / "brainstorming"
            )
            vendor_skill_source.mkdir(parents=True)
            (vendor_skill_source / "SKILL.md").write_text(
                "# brainstorming\n",
                encoding="utf-8",
            )

            bundle_path = repo_root / "bundles" / "superpowers-codex.json"
            bundle_path.parent.mkdir(parents=True)
            bundle_path.write_text(
                json.dumps(
                    {
                        "name": "superpowers-codex",
                        "agent": "codex",
                        "skills": [
                            {"source": "local", "path": "skill-manager"},
                            {
                                "source": "vendor/superpowers",
                                "path": "brainstorming",
                            },
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            installed_dir = module.sync_bundle(
                bundle_name="superpowers-codex",
                project_root=project_root,
                repo_root=repo_root,
                repo_url="git@github.com:zhpjy/skills.git",
            )

            self.assertEqual(installed_dir, project_root / ".agents" / "skills")
            self.assertEqual(
                (
                    project_root
                    / ".agents"
                    / "skills"
                    / "skill-manager"
                    / "SKILL.md"
                ).read_text(encoding="utf-8"),
                "# manager\n",
            )
            self.assertEqual(
                (
                    project_root
                    / ".agents"
                    / "skills"
                    / "brainstorming"
                    / "SKILL.md"
                ).read_text(encoding="utf-8"),
                "# brainstorming\n",
            )

            bundle_state = json.loads(
                (
                    project_root
                    / ".agents"
                    / "bundles"
                    / "superpowers-codex.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(bundle_state["bundle"], "superpowers-codex")
            self.assertEqual(bundle_state["agent"], "codex")
            self.assertEqual(bundle_state["repo_url"], "git@github.com:zhpjy/skills.git")
            self.assertEqual(bundle_state["skills"], ["skill-manager", "brainstorming"])

            repo_info = json.loads(
                (
                    project_root
                    / ".agents"
                    / "skills"
                    / "skill-manager"
                    / "repo-info.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(
                repo_info,
                {
                    "repo_url": "git@github.com:zhpjy/skills.git",
                },
            )

            local_state = json.loads(
                (
                    project_root
                    / ".agents"
                    / ".local"
                    / "skill-manager.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(
                local_state,
                {
                    "repo_root": str(repo_root),
                },
            )

    def test_main_returns_exit_code_1_when_bundle_sync_fails(self) -> None:
        module = load_sync_bundle_module(self)

        stderr = io.StringIO()
        with mock.patch.object(
            module,
            "sync_bundle",
            side_effect=RuntimeError("bundle sync failed"),
        ):
            with contextlib.redirect_stderr(stderr):
                exit_code = module.main(["--bundle", "superpowers-codex"])

        self.assertEqual(exit_code, 1)
        self.assertIn("bundle sync failed", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
