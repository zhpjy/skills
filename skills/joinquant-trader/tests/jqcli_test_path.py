from __future__ import annotations

import sys
from pathlib import Path


def ensure_skill_jqcli_path() -> None:
    skill_dir = Path(__file__).resolve().parents[1]
    scripts_dir = skill_dir / "scripts"
    path = str(scripts_dir)
    if path not in sys.path:
        sys.path.insert(0, path)
