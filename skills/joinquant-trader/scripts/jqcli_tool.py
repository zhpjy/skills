from __future__ import annotations

import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from jqcli.__main__ import main as jqcli_main
from jqcli.output import error_response, print_json


def is_agent_mode() -> bool:
    return os.environ.get("JQCLI_AGENT_MODE", "1") != "0"


def _is_forbidden_agent_command(argv: list[str]) -> bool:
    if len(argv) < 2 or argv[0] != "backtest":
        return False
    if argv[1] == "status":
        return True
    if argv[1] == "run" and "--wait" not in argv:
        return True
    return False


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if is_agent_mode() and _is_forbidden_agent_command(argv):
        print_json(
            error_response(
                "AGENT_COMMAND_NOT_ALLOWED",
                "agent 模式下不暴露 backtest status，且 backtest run 必须配合 --wait；请改用 backtest wait --backtest-id ... 或 backtest run --wait",
            )
        )
        return 1
    return jqcli_main(argv)

if __name__ == "__main__":
    raise SystemExit(main())
