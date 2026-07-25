"""
自动获取 biji.com 认证 Token（DrissionPage 驱动系统 Chrome）。

- extract_auth: 纯逻辑，从请求头提取 Token（可单测）
- capture_token: 浏览器流程
"""
import time
from pathlib import Path
from typing import Callable

from DrissionPage import ChromiumOptions, ChromiumPage

from scripts import biji_export
from scripts.app_paths import user_data_root

BIJI_HOME = "https://www.biji.com/subject"
API_DOMAIN = "knowledge-api.trytalks.com"
# 首次使用需要登录，超过这个秒数还没抓到就在日志里提示用户
FIRST_LOGIN_HINT_SECONDS = 120
# 空闲监听超过这个秒数就自动把页面导航回知识库页面，重新触发请求
RENAVIGATE_SECONDS = 30
# 总时长上限，避免界面永远卡在等待状态
MAX_TOTAL_SECONDS = 900

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    str(Path.home() / "Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
]


class TokenCaptureError(Exception):
    """抓取 Token 失败"""


class ChromeNotFoundError(TokenCaptureError):
    """未找到系统 Chrome"""


class CaptureCancelled(Exception):
    """用户关闭了浏览器窗口，取消抓取"""


def extract_auth(headers: dict) -> dict | None:
    """从请求头提取认证信息；大小写不敏感。缺关键字段返回 None。"""
    lower = {str(k).lower(): v for k, v in headers.items()}
    authorization = lower.get("authorization")
    csrf = lower.get("xi-csrf-token")
    if not authorization or not csrf:
        return None
    return {
        "authorization": authorization,
        "xi-csrf-token": csrf,
        "x-appid": lower.get("x-appid") or "3",
    }


def chrome_path() -> str | None:
    """返回系统 Chrome 可执行文件路径，找不到返回 None。"""
    for candidate in CHROME_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return None


def chrome_profile_dir() -> Path:
    """浏览器用户数据目录（登录态持久化在这里），自动创建。"""
    path = user_data_root() / "chrome_profile"
    path.mkdir(parents=True, exist_ok=True)
    return path


def capture_token(log: Callable[[str], None] = print) -> dict:
    """
    启动系统 Chrome 抓取 biji Token 并保存。
    - 首次使用：用户在浏览器里登录 biji 并打开任意一篇笔记
    - 已登录过：打开首页即自动抓到，全程无需操作
    用户关闭浏览器窗口视为取消（抛 CaptureCancelled）。
    """
    executable = chrome_path()
    if not executable:
        raise ChromeNotFoundError("未找到 Chrome，请安装 Chrome，或改用手动粘贴 Token")

    options = ChromiumOptions().set_browser_path(executable)
    options.set_user_data_path(str(chrome_profile_dir()))
    # 自动选空闲端口：默认 9222 可能被用户日常 Chrome（开远程调试）占用，
    # 否则会错误地接管用户的浏览器
    options.auto_port()

    try:
        page = ChromiumPage(options)
    except Exception as exc:
        raise TokenCaptureError(f"启动 Chrome 失败：{exc}") from exc

    captured = None
    try:
        page.listen.start(API_DOMAIN)
        page.get(BIJI_HOME)
        log("已打开 biji 知识库页面，正在监听登录请求…")

        start = time.monotonic()
        hinted = False
        while captured is None:
            if not page.states.is_alive:
                break
            elapsed = time.monotonic() - start
            if elapsed > MAX_TOTAL_SECONDS:
                break
            if not hinted and elapsed > FIRST_LOGIN_HINT_SECONDS:
                log("还没抓到：请先在浏览器里登录 biji，登录成功后会自动完成")
                hinted = True

            for packet in page.listen.steps(timeout=RENAVIGATE_SECONDS):
                auth = extract_auth(packet.request.headers)
                if auth:
                    captured = auth
                    break

            if captured is None and page.states.is_alive:
                # 兜底：空闲超时后重新导航回知识库页面，主动触发一次请求
                # （覆盖登录后跳转到其他页面、页面未自动刷新等情况）
                try:
                    page.get(BIJI_HOME)
                except Exception:
                    break
    except Exception as exc:
        raise TokenCaptureError(f"监听请求时出错：{exc}") from exc
    finally:
        try:
            page.quit()
        except Exception:
            pass

    if captured:
        biji_export.save_auth_config(captured)
        log("✅ 已捕获并保存 Token")
        return captured

    if not page.states.is_alive:
        raise CaptureCancelled("浏览器窗口已关闭，取消获取 Token")

    raise TokenCaptureError("等待超时，未捕获到 Token。请重试，或改用手动粘贴 Token")
