"""
Biji.com Token 自动刷新脚本 (浏览器版)
用法: python scripts/refresh_token_browser.py
依赖: pip install playwright && playwright install chromium
"""
import json
import os
import sys
from playwright.sync_api import sync_playwright

from scripts.app_paths import config_dir

CONFIG_PATH = config_dir() / "biji_auth.json"


def browser_launch_args() -> dict:
    if getattr(sys, "frozen", False):
        executable_path = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH")
        if not executable_path:
            raise RuntimeError(
                "未找到 Chromium 可执行文件。请先运行 Playwright 安装，或在环境变量 PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH 中指定浏览器路径。"
            )
        return {"headless": False, "executable_path": executable_path}
    return {"headless": False}

def main():
    print("\n=== Biji.com Token 自动刷新程序 ===")
    print("程序将启动浏览器窗口，请在窗口中完成登录。")
    print("登录成功后并点击任意笔记，程序将自动捕获并保存 Token。\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(**browser_launch_args())
        context = browser.new_context()
        page = context.new_page()

        captured = {
            "authorization": None,
            "xi-csrf-token": None,
            "x-appid": "3"
        }

        def handle_request(request):
            url = request.url
            if "knowledge-api.trytalks.com" in url:
                headers = request.headers
                if "authorization" in headers and "xi-csrf-token" in headers:
                    if headers["authorization"] != captured["authorization"]:
                        captured["authorization"] = headers["authorization"]
                        captured["xi-csrf-token"] = headers["xi-csrf-token"]
                        captured["x-appid"] = headers.get("x-appid", "3")
                        print(f"✅ 已捕获认证信息!")
                        print(f"   Auth: {captured['authorization'][:30]}...")
                        save_config(captured)

        # 监听请求
        page.on("request", handle_request)

        # 访问首页
        page.goto("https://www.biji.com")

        print("等待登录及 API 请求 (完成后可关闭浏览器或在终端按 Ctrl+C)...")
        
        try:
            # 保持运行直到捕获到数据或被用户关闭
            while not captured["authorization"]:
                page.wait_for_timeout(1000)
            
            print("\n🎉 Token 已更新！现在你可以运行导出脚本了。")
            print("你可以在 10 秒后关闭浏览器，或直接按 Ctrl+C 退出。")
            page.wait_for_timeout(10000)
            
        except KeyboardInterrupt:
            print("\n用户退出")
        finally:
            browser.close()

def save_config(config):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"💾 配置已更新到: {CONFIG_PATH}")

if __name__ == "__main__":
    main()
