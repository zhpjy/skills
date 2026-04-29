import importlib
import io
import contextlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock


def load_install_skill(test_case: unittest.TestCase):
    try:
        module = importlib.import_module("tools.sync_skill")
    except ModuleNotFoundError as exc:
        test_case.fail(
            "missing implementation module 'tools.sync_skill'; "
            "create tools/sync_skill.py with an install_skill() function"
        )

    try:
        return module.install_skill
    except AttributeError as exc:
        test_case.fail(
            "missing implementation function 'install_skill' in tools.sync_skill"
        )


def load_install_skill_module(test_case: unittest.TestCase):
    try:
        return importlib.import_module("tools.sync_skill")
    except ModuleNotFoundError:
        test_case.fail(
            "missing implementation module 'tools.sync_skill'; "
            "create tools/sync_skill.py with install_skill(), "
            "clone_repository(), and main()"
        )


class InstallSkillTests(unittest.TestCase):
    def test_install_skill_copies_remote_directory_into_local_agents(self) -> None:
        install_skill = load_install_skill(self)

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            project_dir = workspace / "project"
            project_dir.mkdir()

            def fake_clone(repo_url: str, clone_dir: Path) -> None:
                remote_skill_dir = clone_dir / "skills" / "demo-skill"
                remote_skill_dir.mkdir(parents=True)
                (remote_skill_dir / "SKILL.md").write_text("# demo\n", encoding="utf-8")

            install_skill(
                repo_url="https://example.com/repo.git",
                skill_name="demo-skill",
                project_root=project_dir,
                clone_repo=fake_clone,
            )

            installed = project_dir / ".agents" / "skills" / "demo-skill" / "SKILL.md"
            self.assertTrue(installed.exists())
            self.assertEqual(installed.read_text(encoding="utf-8"), "# demo\n")

    def test_install_skill_replaces_existing_local_skill_directory(self) -> None:
        install_skill = load_install_skill(self)

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            project_dir = workspace / "project"
            project_dir.mkdir()

            local_skill_dir = project_dir / ".agents" / "skills" / "demo-skill"
            local_skill_dir.mkdir(parents=True)
            (local_skill_dir / "SKILL.md").write_text("old\n", encoding="utf-8")
            (local_skill_dir / "extra.txt").write_text("stale\n", encoding="utf-8")

            def fake_clone(repo_url: str, clone_dir: Path) -> None:
                remote_skill_dir = clone_dir / "skills" / "demo-skill"
                remote_skill_dir.mkdir(parents=True)
                (remote_skill_dir / "SKILL.md").write_text("new\n", encoding="utf-8")

            install_skill(
                repo_url="https://example.com/repo.git",
                skill_name="demo-skill",
                project_root=project_dir,
                clone_repo=fake_clone,
            )

            installed_dir = project_dir / ".agents" / "skills" / "demo-skill"
            self.assertEqual(
                (installed_dir / "SKILL.md").read_text(encoding="utf-8"),
                "new\n",
            )
            self.assertFalse((installed_dir / "extra.txt").exists())

    def test_install_skill_errors_when_remote_skill_is_missing(self) -> None:
        install_skill = load_install_skill(self)

        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir) / "project"
            project_dir.mkdir()

            def fake_clone(repo_url: str, clone_dir: Path) -> None:
                (clone_dir / "skills").mkdir(parents=True)

            with self.assertRaisesRegex(
                ValueError,
                "Skill 'missing-skill' not found in repository",
            ):
                install_skill(
                    repo_url="https://example.com/repo.git",
                    skill_name="missing-skill",
                    project_root=project_dir,
                    clone_repo=fake_clone,
                )

    def test_install_skill_rejects_invalid_skill_name(self) -> None:
        install_skill = load_install_skill(self)

        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir) / "project"
            project_dir.mkdir()

            invalid_names = ["../demo-skill", "nested/demo-skill", "/tmp/demo-skill"]
            for skill_name in invalid_names:
                with self.subTest(skill_name=skill_name):
                    with self.assertRaisesRegex(
                        ValueError,
                        "skill_name must be a single directory name",
                    ):
                        install_skill(
                            repo_url="https://example.com/repo.git",
                            skill_name=skill_name,
                            project_root=project_dir,
                            clone_repo=lambda repo_url, clone_dir: None,
                        )

    def test_install_skill_preserves_existing_skill_when_copy_fails(self) -> None:
        module = load_install_skill_module(self)

        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir) / "project"
            project_dir.mkdir()

            local_skill_dir = project_dir / ".agents" / "skills" / "demo-skill"
            local_skill_dir.mkdir(parents=True)
            (local_skill_dir / "SKILL.md").write_text("old\n", encoding="utf-8")
            (local_skill_dir / "extra.txt").write_text("stale\n", encoding="utf-8")

            def fake_clone(repo_url: str, clone_dir: Path) -> None:
                remote_skill_dir = clone_dir / "skills" / "demo-skill"
                remote_skill_dir.mkdir(parents=True)
                (remote_skill_dir / "SKILL.md").write_text("new\n", encoding="utf-8")

            original_copytree = module.replace_directory.__globals__["shutil"].copytree

            def failing_copytree(src: Path, dst: Path, *args, **kwargs):
                if Path(dst).parent == local_skill_dir.parent:
                    raise OSError("copy failed")
                return original_copytree(src, dst, *args, **kwargs)

            with mock.patch.object(
                module.replace_directory.__globals__["shutil"],
                "copytree",
                side_effect=failing_copytree,
            ):
                with self.assertRaisesRegex(OSError, "copy failed"):
                    module.install_skill(
                        repo_url="https://example.com/repo.git",
                        skill_name="demo-skill",
                        project_root=project_dir,
                        clone_repo=fake_clone,
                    )

            self.assertEqual(
                (local_skill_dir / "SKILL.md").read_text(encoding="utf-8"),
                "old\n",
            )
            self.assertEqual(
                (local_skill_dir / "extra.txt").read_text(encoding="utf-8"),
                "stale\n",
            )

    def test_main_returns_exit_code_1_on_install_failure(self) -> None:
        module = load_install_skill_module(self)

        stderr = io.StringIO()
        with mock.patch.object(
            module,
            "install_skill",
            side_effect=RuntimeError("clone failed"),
        ):
            with contextlib.redirect_stderr(stderr):
                exit_code = module.main(
                    ["--repo", "https://example.com/repo.git", "--skill", "demo-skill"]
                )

        self.assertEqual(exit_code, 1)
        self.assertIn("clone failed", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
