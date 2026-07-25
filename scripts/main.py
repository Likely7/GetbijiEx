"""
统一入口：无参数启动 GUI，带参数走 CLI。
打包后的 app 因此既能双击使用，也能被 Agent 在终端调用。
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main():
    if len(sys.argv) > 1:
        from scripts import biji_cli
        biji_cli.main()
    else:
        from scripts import gui_app
        gui_app.main()


if __name__ == "__main__":
    main()
