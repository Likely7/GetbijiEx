"""
Biji.com Token 自动获取脚本
用法: uv run python scripts/refresh_token_browser.py
首次使用会自动打开 Chrome，请登录 biji 并打开任意一篇笔记；
之后再次运行会自动捕获 Token，无需操作。
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.auto_token import (
    CaptureCancelled,
    ChromeNotFoundError,
    TokenCaptureError,
    capture_token,
)


def main():
    print("\n=== Biji.com Token 自动获取程序 ===")
    print("程序将启动 Chrome 浏览器：")
    print("- 首次使用：请在浏览器中登录 biji，再打开任意一篇笔记")
    print("- 已登录过：程序会自动捕获 Token，无需操作\n")

    try:
        capture_token(log=print)
    except ChromeNotFoundError as exc:
        print(f"❌ {exc}")
        sys.exit(1)
    except CaptureCancelled:
        print("\n已取消（浏览器窗口被关闭）")
        sys.exit(0)
    except TokenCaptureError as exc:
        print(f"❌ {exc}")
        sys.exit(1)

    print("\n🎉 Token 已更新！现在可以运行导出脚本了。")


if __name__ == "__main__":
    main()
