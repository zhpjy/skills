import contextlib
import importlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


def load_push_skill_module(test_case: unittest.TestCase):
    try:
        return importlib.import_module("tools.push_skill")
    except ModuleNotFoundError:
        test_case.fail(
            "missing implementation module 'tools.push_skill'; "
            "create tools/push_skill.py with push_skill() and main()"
        )


class PushSkillTests(unittest.TestCase):
    def create_remote_repo(self, root: Path, skill_body: str) -> tuple[Path, Path]:
        module = load_push_skill_module(self)

        remote_dir = root / "remote.git"
        seed_dir = root / "seed"

        module.run_git(["init", "--bare", str(remote_dir)], cwd=root)
        seed_dir.mkdir()
        module.run_git(["init"], cwd=seed_dir)
        module.run_git(["config", "user.name", "Test User"], cwd=seed_dir)
        module.run_git(["config", "user.email", "test@example.com"], cwd=seed_dir)

        (seed_dir / ".gitignore").write_text(
            "\n".join(
                [
                    ".env",
                    ".session",
                    "__pycache__/",
                    "node_modules/",
                    "*.class",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        skill_dir = seed_dir / "skills" / "demo-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(skill_body, encoding="utf-8")

        module.run_git(["add", "."], cwd=seed_dir)
        module.run_git(["commit", "-m", "Initial commit"], cwd=seed_dir)
        module.run_git(["remote", "add", "origin", str(remote_dir)], cwd=seed_dir)
        module.run_git(["push", "-u", "origin", "HEAD"], cwd=seed_dir)

        return remote_dir, seed_dir

    def clone_remote_skill(self, root: Path, remote_dir: Path) -> Path:
        module = load_push_skill_module(self)

        checkout_dir = root / "checkout"
        module.run_git(["clone", str(remote_dir), str(checkout_dir)], cwd=root)
        return checkout_dir / "skills" / "demo-skill"

    def test_push_skill_skips_ignored_only_changes(self) -> None:
        module = load_push_skill_module(self)

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            remote_dir, seed_dir = self.create_remote_repo(root, "# demo\n")

            source_dir = root / "source-skill"
            source_dir.mkdir()
            (source_dir / "SKILL.md").write_text("# demo\n", encoding="utf-8")
            (source_dir / ".env").write_text("SECRET=1\n", encoding="utf-8")
            (source_dir / ".session").write_text("token\n", encoding="utf-8")

            stdout = io.StringIO()
            with mock.patch.object(module, "get_repo_root", return_value=seed_dir):
                with mock.patch.object(module, "get_origin_url", return_value=str(remote_dir)):
                    with mock.patch.object(module, "sync_local_skill_manager"):
                        with mock.patch.dict(
                            os.environ,
                            {
                                "GIT_AUTHOR_NAME": "Test User",
                                "GIT_AUTHOR_EMAIL": "test@example.com",
                                "GIT_COMMITTER_NAME": "Test User",
                                "GIT_COMMITTER_EMAIL": "test@example.com",
                            },
                            clear=False,
                        ):
                            with contextlib.redirect_stdout(stdout):
                                module.push_skill(
                                    "demo-skill",
                                    source_dir,
                                    Path(__file__).resolve(),
                                )

            self.assertIn("No changes for skill 'demo-skill'.", stdout.getvalue())

            remote_skill_dir = self.clone_remote_skill(root, remote_dir)
            self.assertEqual(
                (remote_skill_dir / "SKILL.md").read_text(encoding="utf-8"),
                "# demo\n",
            )
            self.assertFalse((remote_skill_dir / ".env").exists())
            self.assertFalse((remote_skill_dir / ".session").exists())

    def test_push_skill_pushes_non_ignored_changes(self) -> None:
        module = load_push_skill_module(self)

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            remote_dir, seed_dir = self.create_remote_repo(root, "# old\n")

            source_dir = root / "source-skill"
            source_dir.mkdir()
            (source_dir / "SKILL.md").write_text("# new\n", encoding="utf-8")
            (source_dir / ".env").write_text("SECRET=1\n", encoding="utf-8")

            with mock.patch.object(module, "get_repo_root", return_value=seed_dir):
                with mock.patch.object(module, "get_origin_url", return_value=str(remote_dir)):
                    with mock.patch.object(module, "sync_local_skill_manager"):
                        with mock.patch.dict(
                            os.environ,
                            {
                                "GIT_AUTHOR_NAME": "Test User",
                                "GIT_AUTHOR_EMAIL": "test@example.com",
                                "GIT_COMMITTER_NAME": "Test User",
                                "GIT_COMMITTER_EMAIL": "test@example.com",
                            },
                            clear=False,
                        ):
                            module.push_skill(
                                "demo-skill",
                                source_dir,
                                Path(__file__).resolve(),
                            )

            remote_skill_dir = self.clone_remote_skill(root, remote_dir)
            self.assertEqual(
                (remote_skill_dir / "SKILL.md").read_text(encoding="utf-8"),
                "# new\n",
            )
            self.assertFalse((remote_skill_dir / ".env").exists())


if __name__ == "__main__":
    unittest.main()
