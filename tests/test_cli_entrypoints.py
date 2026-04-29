import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class CliEntrypointTests(unittest.TestCase):
    def test_tool_scripts_support_help_when_run_as_files(self) -> None:
        script_paths = [
            REPO_ROOT / "tools" / "sync_skill.py",
            REPO_ROOT / "tools" / "push_skill.py",
            REPO_ROOT / "tools" / "sync_vendor.py",
            REPO_ROOT / "tools" / "sync_bundle.py",
        ]

        for script_path in script_paths:
            with self.subTest(script=script_path.name):
                result = subprocess.run(
                    [sys.executable, str(script_path), "--help"],
                    cwd=REPO_ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, msg=result.stderr)
                self.assertIn("usage:", result.stdout)


if __name__ == "__main__":
    unittest.main()
