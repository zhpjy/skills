import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.lib import common


class ToolCommonTests(unittest.TestCase):
    def test_validate_skill_name_accepts_single_directory_name(self) -> None:
        common.validate_skill_name("demo-skill")

    def test_validate_skill_name_rejects_paths(self) -> None:
        invalid_names = ["", ".", "..", "../demo", "nested/demo", "/tmp/demo", r"nested\\demo"]
        for skill_name in invalid_names:
            with self.subTest(skill_name=skill_name):
                with self.assertRaisesRegex(
                    ValueError,
                    "skill_name must be a single directory name",
                ):
                    common.validate_skill_name(skill_name)

    def test_replace_directory_replaces_existing_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_dir = root / "source"
            target_dir = root / "target"
            source_dir.mkdir()
            target_dir.mkdir()
            (source_dir / "SKILL.md").write_text("new\n", encoding="utf-8")
            (target_dir / "SKILL.md").write_text("old\n", encoding="utf-8")
            (target_dir / "stale.txt").write_text("stale\n", encoding="utf-8")

            common.replace_directory(source_dir, target_dir)

            self.assertEqual((target_dir / "SKILL.md").read_text(encoding="utf-8"), "new\n")
            self.assertFalse((target_dir / "stale.txt").exists())

    def test_replace_directory_preserves_existing_directory_when_copy_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_dir = root / "source"
            target_dir = root / "target"
            source_dir.mkdir()
            target_dir.mkdir()
            (source_dir / "SKILL.md").write_text("new\n", encoding="utf-8")
            (target_dir / "SKILL.md").write_text("old\n", encoding="utf-8")
            (target_dir / "stale.txt").write_text("stale\n", encoding="utf-8")

            original_copytree = common.shutil.copytree

            def failing_copytree(src: Path, dst: Path, *args, **kwargs):
                if Path(dst).parent == target_dir.parent:
                    raise OSError("copy failed")
                return original_copytree(src, dst, *args, **kwargs)

            with mock.patch.object(common.shutil, "copytree", side_effect=failing_copytree):
                with self.assertRaisesRegex(OSError, "copy failed"):
                    common.replace_directory(source_dir, target_dir)

            self.assertEqual((target_dir / "SKILL.md").read_text(encoding="utf-8"), "old\n")
            self.assertEqual((target_dir / "stale.txt").read_text(encoding="utf-8"), "stale\n")

    def test_run_git_returns_completed_process(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            common.run_git(["init"], cwd=repo_root)

            result = common.run_git(["rev-parse", "--is-inside-work-tree"], cwd=repo_root)

            self.assertEqual(result.stdout.strip(), "true")

    def test_run_git_raises_with_git_output_on_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            common.run_git(["init"], cwd=repo_root)

            with self.assertRaisesRegex(RuntimeError, "git not-a-command failed"):
                common.run_git(["not-a-command"], cwd=repo_root)

    def test_run_git_disables_terminal_prompts(self) -> None:
        completed = common.subprocess.CompletedProcess(
            args=["git", "status"],
            returncode=0,
            stdout="ok\n",
            stderr="",
        )

        with mock.patch.object(common.subprocess, "run", return_value=completed) as run_mock:
            common.run_git(["status"], cwd=Path("/tmp/repo"))

        self.assertEqual(run_mock.call_args.kwargs["env"]["GIT_TERMINAL_PROMPT"], "0")

    def test_write_repo_info_writes_expected_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir)

            common.write_repo_info(
                skill_dir=skill_dir,
                repo_url="git@example.com:repo.git",
            )

            repo_info = json.loads((skill_dir / "repo-info.json").read_text(encoding="utf-8"))
            self.assertEqual(
                repo_info,
                {
                    "repo_url": "git@example.com:repo.git",
                },
            )

    def test_write_local_repo_state_writes_expected_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            common.write_local_repo_state(
                project_root=project_root,
                repo_root=Path("/repo/root"),
            )

            state = json.loads(
                (
                    project_root
                    / ".agents"
                    / ".local"
                    / "skill-manager.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(
                state,
                {
                    "repo_root": "/repo/root",
                },
            )


if __name__ == "__main__":
    unittest.main()
