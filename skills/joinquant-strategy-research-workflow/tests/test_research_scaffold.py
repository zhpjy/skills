import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "research_scaffold.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("research_scaffold", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ResearchScaffoldTest(unittest.TestCase):
    def test_render_template_rejects_unused_context_keys(self):
        research_scaffold = load_module()
        with self.assertRaises(ValueError):
            research_scaffold._render_template(
                "README.md.tmpl",
                {
                    "research_date": "20260512",
                    "topic": "中证红利低波增强",
                    "research_name": "20260512-中证红利低波增强",
                    "extra": "unused",
                },
            )

    def test_render_template_rejects_unfilled_placeholders(self):
        research_scaffold = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            assets_dir = Path(tmp)
            (assets_dir / "broken.tmpl").write_text(
                "Hello {{name}} {{missing}}\n",
                encoding="utf-8",
            )
            research_scaffold.ASSETS_DIR = assets_dir

            with self.assertRaises(ValueError):
                research_scaffold._render_template(
                    "broken.tmpl",
                    {"name": "demo"},
                )

    def test_init_package_creates_readme_path_and_versions_dir(self):
        research_scaffold = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = research_scaffold.init_package(
                root=root,
                research_date="20260512",
                topic="中证红利低波增强",
            )

            self.assertEqual(
                package_dir.name,
                "20260512-中证红利低波增强",
            )
            self.assertTrue((package_dir / "README.md").exists())
            self.assertTrue((package_dir / "PATH.md").exists())
            self.assertTrue((package_dir / "candidate").is_dir())
            self.assertTrue((package_dir / "versions").is_dir())

    def test_init_package_sanitizes_topic_for_directory_name(self):
        research_scaffold = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = research_scaffold.init_package(
                root=root,
                research_date="20260512",
                topic="alpha/beta:gamma*delta",
            )

            self.assertEqual(
                package_dir.name,
                "20260512-alpha-beta-gamma-delta",
            )
            self.assertFalse((root / "20260512-alpha").exists())

    def test_init_package_renders_topic_into_templates(self):
        research_scaffold = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = research_scaffold.init_package(
                root=root,
                research_date="20260512",
                topic="中证红利低波增强",
            )

            readme = (package_dir / "README.md").read_text(encoding="utf-8")
            path_md = (package_dir / "PATH.md").read_text(encoding="utf-8")

            self.assertIn("中证红利低波增强", readme)
            self.assertIn("候选工作区：candidate/", readme)
            self.assertIn("聚宽远端目录", readme)
            self.assertIn("研究决策日志", path_md)
            self.assertIn("20260512-中证红利低波增强", path_md)
            self.assertIn("- 时间：20260512", path_md)

    def test_init_version_copies_strategy_and_creates_result_and_meta(self):
        research_scaffold = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = research_scaffold.init_package(
                root=root,
                research_date="20260512",
                topic="中证红利低波增强",
            )
            source_file = package_dir / "candidate" / "strategy.py"
            source_file.write_text(
                "def initialize(context):\n    pass\n",
                encoding="utf-8",
            )

            version_dir = research_scaffold.init_version(
                package_dir=package_dir,
                version_id="r01-main",
                source_file=source_file,
                parent_version=None,
                branch_type="main",
                remote_directory_name="20260512-中证红利低波增强",
            )

            self.assertTrue((version_dir / "strategy.py").exists())
            self.assertTrue((version_dir / "result.md").exists())
            self.assertTrue((version_dir / "meta.json").exists())
            self.assertEqual(
                (version_dir / "strategy.py").read_text(encoding="utf-8"),
                "def initialize(context):\n    pass\n",
            )

            meta = json.loads((version_dir / "meta.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["version_id"], "r01-main")
            self.assertEqual(meta["parent_version"], None)
            self.assertEqual(meta["branch_type"], "main")
            self.assertEqual(
                meta["remote_directory_name"],
                "20260512-中证红利低波增强",
            )
            self.assertEqual(meta["compile_status"], "pending")
            self.assertEqual(meta["latest_backtest_id"], None)

    def test_init_version_rejects_source_file_outside_candidate_workspace(self):
        research_scaffold = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = research_scaffold.init_package(
                root=root,
                research_date="20260512",
                topic="中证红利低波增强",
            )
            source_file = root / "strategies" / "source_strategy.py"
            source_file.parent.mkdir()
            source_file.write_text(
                "def initialize(context):\n    pass\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                research_scaffold.init_version(
                    package_dir=package_dir,
                    version_id="r01-main",
                    source_file=source_file,
                    parent_version=None,
                    branch_type="main",
                    remote_directory_name="20260512-中证红利低波增强",
                )

    def test_init_version_updates_readme_for_first_main_version(self):
        research_scaffold = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = research_scaffold.init_package(
                root=root,
                research_date="20260512",
                topic="中证红利低波增强",
            )
            source_file = package_dir / "candidate" / "strategy.py"
            source_file.write_text(
                "def initialize(context):\n    pass\n",
                encoding="utf-8",
            )

            research_scaffold.init_version(
                package_dir=package_dir,
                version_id="r01-main",
                source_file=source_file,
                parent_version=None,
                branch_type="main",
                remote_directory_name="20260512-中证红利低波增强",
            )

            readme = (package_dir / "README.md").read_text(encoding="utf-8")
            self.assertIn("- 当前主线版本：r01-main", readme)
            self.assertIn("- 当前最优版本：r01-main", readme)
            self.assertIn("- 聚宽远端目录：20260512-中证红利低波增强", readme)
            self.assertNotIn("未确定", readme)
            self.assertNotIn("待创建", readme)
            self.assertIn(
                "| r01-main | main | - | 待补充 | pending | 首个主线版本 |",
                readme,
            )

    def test_init_version_reuses_bound_remote_directory_name(self):
        research_scaffold = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = research_scaffold.init_package(
                root=root,
                research_date="20260512",
                topic="中证红利低波增强",
            )
            source_file = package_dir / "candidate" / "strategy.py"
            source_file.write_text(
                "def initialize(context):\n    pass\n",
                encoding="utf-8",
            )
            research_scaffold.init_version(
                package_dir=package_dir,
                version_id="r01-main",
                source_file=source_file,
                parent_version=None,
                branch_type="main",
                remote_directory_name="20260512-中证红利低波增强",
            )

            with self.assertRaises(ValueError):
                research_scaffold.init_version(
                    package_dir=package_dir,
                    version_id="r02-main",
                    source_file=source_file,
                    parent_version=None,
                    branch_type="main",
                    remote_directory_name="another-remote-dir",
                )

    def test_init_version_rejects_first_remote_directory_name_mismatch(self):
        research_scaffold = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = research_scaffold.init_package(
                root=root,
                research_date="20260512",
                topic="中证红利低波增强",
            )
            source_file = root / "source_strategy.py"
            source_file.write_text(
                "def initialize(context):\n    pass\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                research_scaffold.init_version(
                    package_dir=package_dir,
                    version_id="r01-main",
                    source_file=source_file,
                    parent_version=None,
                    branch_type="main",
                    remote_directory_name="totally-different-remote",
                )

    def test_init_version_requires_parent_version_for_exp_branch(self):
        research_scaffold = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = research_scaffold.init_package(
                root=root,
                research_date="20260512",
                topic="中证红利低波增强",
            )
            source_file = root / "source_strategy.py"
            source_file.write_text(
                "def initialize(context):\n    pass\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                research_scaffold.init_version(
                    package_dir=package_dir,
                    version_id="r02-exp-a",
                    source_file=source_file,
                    parent_version=None,
                    branch_type="exp-a",
                    remote_directory_name="20260512-中证红利低波增强",
                )

    def test_init_version_requires_existing_parent_version_directory(self):
        research_scaffold = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = research_scaffold.init_package(
                root=root,
                research_date="20260512",
                topic="中证红利低波增强",
            )
            source_file = root / "source_strategy.py"
            source_file.write_text(
                "def initialize(context):\n    pass\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                research_scaffold.init_version(
                    package_dir=package_dir,
                    version_id="r02-exp-a",
                    source_file=source_file,
                    parent_version="r01-main",
                    branch_type="exp-a",
                    remote_directory_name="20260512-中证红利低波增强",
                )

    def test_init_version_rejects_invalid_version_id(self):
        research_scaffold = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = research_scaffold.init_package(
                root=root,
                research_date="20260512",
                topic="中证红利低波增强",
            )
            source_file = root / "source_strategy.py"
            source_file.write_text(
                "def initialize(context):\n    pass\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                research_scaffold.init_version(
                    package_dir=package_dir,
                    version_id="v1",
                    source_file=source_file,
                    parent_version=None,
                    branch_type="main",
                    remote_directory_name="20260512-中证红利低波增强",
                )

    def test_init_version_rejects_invalid_branch_type(self):
        research_scaffold = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = research_scaffold.init_package(
                root=root,
                research_date="20260512",
                topic="中证红利低波增强",
            )
            source_file = root / "source_strategy.py"
            source_file.write_text(
                "def initialize(context):\n    pass\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                research_scaffold.init_version(
                    package_dir=package_dir,
                    version_id="r01-exp-a",
                    source_file=source_file,
                    parent_version=None,
                    branch_type="exp-aa",
                    remote_directory_name="20260512-中证红利低波增强",
                )

    def test_init_version_rejects_mismatched_branch_type(self):
        research_scaffold = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = research_scaffold.init_package(
                root=root,
                research_date="20260512",
                topic="中证红利低波增强",
            )
            source_file = root / "source_strategy.py"
            source_file.write_text(
                "def initialize(context):\n    pass\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                research_scaffold.init_version(
                    package_dir=package_dir,
                    version_id="r01-main",
                    source_file=source_file,
                    parent_version=None,
                    branch_type="exp-a",
                    remote_directory_name="20260512-中证红利低波增强",
                )

    def test_init_version_rejects_source_file_directory(self):
        research_scaffold = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = research_scaffold.init_package(
                root=root,
                research_date="20260512",
                topic="中证红利低波增强",
            )
            source_dir = root / "source_dir"
            source_dir.mkdir()

            with self.assertRaises(ValueError):
                research_scaffold.init_version(
                    package_dir=package_dir,
                    version_id="r01-main",
                    source_file=source_dir,
                    parent_version=None,
                    branch_type="main",
                    remote_directory_name="20260512-中证红利低波增强",
                )

    def test_init_version_rejects_invalid_package_dir_structure(self):
        research_scaffold = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = root / "broken-package"
            package_dir.mkdir()
            source_file = root / "source_strategy.py"
            source_file.write_text(
                "def initialize(context):\n    pass\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                research_scaffold.init_version(
                    package_dir=package_dir,
                    version_id="r01-main",
                    source_file=source_file,
                    parent_version=None,
                    branch_type="main",
                    remote_directory_name="20260512-中证红利低波增强",
                )

    def test_cli_reports_friendly_error_for_invalid_package_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = root / "broken-package"
            package_dir.mkdir()
            source_file = root / "source_strategy.py"
            source_file.write_text(
                "def initialize(context):\n    pass\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "init-version",
                    "--package-dir",
                    str(package_dir),
                    "--version-id",
                    "r01-main",
                    "--source-file",
                    str(source_file),
                    "--branch-type",
                    "main",
                    "--remote-directory-name",
                    "20260512-中证红利低波增强",
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid package directory", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_cli_reports_friendly_error_for_existing_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            existing = root / "20260512-中证红利低波增强"
            existing.mkdir()

            result = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "init-package",
                    "--root",
                    str(root),
                    "--date",
                    "20260512",
                    "--topic",
                    "中证红利低波增强",
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("File exists", result.stderr)
            self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
