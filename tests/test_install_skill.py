import importlib
import tempfile
import unittest
from pathlib import Path


def load_install_skill(test_case: unittest.TestCase):
    try:
        module = importlib.import_module("tools.install_skill")
    except ModuleNotFoundError as exc:
        test_case.fail(
            "missing implementation module 'tools.install_skill'; "
            "create tools/install_skill.py with an install_skill() function"
        )

    try:
        return module.install_skill
    except AttributeError as exc:
        test_case.fail(
            "missing implementation function 'install_skill' in tools.install_skill"
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


if __name__ == "__main__":
    unittest.main()
