# 自动获取 Token 功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用 DrissionPage 驱动系统 Chrome 自动捕获 biji.com 的认证 Token，接入 GUI 和命令行，源码与打包版均可用，用户只需首次登录一次。

**Architecture:** 新增核心模块 `scripts/auto_token.py`（纯逻辑 `extract_auth` + 浏览器流程 `capture_token`）；`refresh_token_browser.py` 改为薄壳 CLI；`gui_app.py` 加"自动获取 Token"按钮并把耗时操作移到后台线程。设计文档：`docs/superpowers/specs/2026-07-25-auto-token-design.md`。

**Tech Stack:** Python 3.11, DrissionPage 4.1.1.2（已安装）, tkinter, pytest（本次加入 dev 依赖）, PyInstaller。

## Global Constraints

- 用户数据目录一律通过 `scripts/app_paths.py` 的 `user_data_root()` 获取（`~/Library/Application Support/BijiExportApp/`），不写死路径。
- Token 保存必须复用 `scripts/biji_export.py` 的 `save_auth_config(config: dict)`，config 结构为 `{"authorization", "xi-csrf-token", "x-appid"}`。
- 手动粘贴 Token 的 GUI 入口保留，不删。
- 项目用 `uv` 管理依赖，运行测试用 `uv run pytest`，运行脚本用 `uv run python ...`。
- Chrome 可执行文件候选路径：`/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` 与 `~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`。
- 面向用户的文案用自然中文（用户既有偏好）。

---

### Task 1: auto_token.py 纯逻辑部分 + 单元测试

**Files:**
- Create: `scripts/auto_token.py`
- Create: `tests/test_auto_token.py`
- Modify: `pyproject.toml`（dev 依赖加 pytest）

**Interfaces:**
- Produces（后续任务依赖）:
  - `extract_auth(headers: dict) -> dict | None` — 从请求头提取 Token；大小写不敏感；缺 `authorization` 或 `xi-csrf-token` 返回 `None`；`x-appid` 缺省为 `"3"`。
  - `chrome_path() -> str | None` — 返回系统 Chrome 可执行文件路径，找不到返回 `None`。
  - `chrome_profile_dir() -> Path` — 返回 `user_data_root() / "chrome_profile"`，自动创建。
  - `class TokenCaptureError(Exception)` / `class ChromeNotFoundError(TokenCaptureError)` / `class CaptureCancelled(Exception)`（本任务先定义，Task 2 使用）。

- [ ] **Step 1: dev 依赖加 pytest**

修改 `pyproject.toml` 的 `[dependency-groups]`：

```toml
[dependency-groups]
dev = [
    "pyinstaller>=6.16.0",
    "pytest>=8.0.0",
]
```

Run: `uv sync`

- [ ] **Step 2: 写失败测试**

创建 `tests/test_auto_token.py`：

```python
from scripts.auto_token import extract_auth


def test_extract_auth_lowercase_keys():
    headers = {
        "authorization": "Bearer abc123",
        "xi-csrf-token": "csrf-xyz",
        "x-appid": "3",
    }
    assert extract_auth(headers) == {
        "authorization": "Bearer abc123",
        "xi-csrf-token": "csrf-xyz",
        "x-appid": "3",
    }


def test_extract_auth_mixed_case_keys():
    headers = {
        "Authorization": "Bearer abc123",
        "Xi-Csrf-Token": "csrf-xyz",
    }
    result = extract_auth(headers)
    assert result["authorization"] == "Bearer abc123"
    assert result["xi-csrf-token"] == "csrf-xyz"
    assert result["x-appid"] == "3"  # 缺省值


def test_extract_auth_missing_authorization():
    assert extract_auth({"xi-csrf-token": "csrf-xyz"}) is None


def test_extract_auth_missing_csrf():
    assert extract_auth({"authorization": "Bearer abc123"}) is None


def test_extract_auth_empty():
    assert extract_auth({}) is None
```

- [ ] **Step 3: 跑测试确认失败**

Run: `uv run pytest tests/test_auto_token.py -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'scripts.auto_token'`

- [ ] **Step 4: 实现纯逻辑部分**

创建 `scripts/auto_token.py`：

```python
"""
自动获取 biji.com 认证 Token（DrissionPage 驱动系统 Chrome）。

- extract_auth: 纯逻辑，从请求头提取 Token（可单测）
- capture_token: 浏览器流程（Task 2 实现）
"""
from pathlib import Path

from scripts.app_paths import user_data_root

BIJI_HOME = "https://www.biji.com"
API_DOMAIN = "knowledge-api.trytalks.com"
# 首次使用需要登录，超过这个秒数还没抓到就在日志里提示用户
FIRST_LOGIN_HINT_SECONDS = 120

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
```

- [ ] **Step 5: 跑测试确认通过**

Run: `uv run pytest tests/test_auto_token.py -v`
Expected: 5 passed

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock scripts/auto_token.py tests/test_auto_token.py
git commit -m "feat: add auto_token module core logic with tests"
```

---

### Task 2: capture_token 浏览器流程 + CLI 薄壳

**Files:**
- Modify: `scripts/auto_token.py`（追加 `capture_token`）
- Modify: `scripts/refresh_token_browser.py`（整体重写为薄壳）

**Interfaces:**
- Consumes: Task 1 的 `extract_auth` / `chrome_path` / `chrome_profile_dir` / 异常类；`scripts.biji_export.save_auth_config(config: dict)`。
- Produces:
  - `capture_token(log: Callable[[str], None] = print) -> dict` — 启动 Chrome、监听并保存 Token，返回保存的 config。抛 `ChromeNotFoundError`（无 Chrome）、`CaptureCancelled`（用户关窗）、`TokenCaptureError`（其他失败）。Task 3 的 GUI 依赖这个签名。
- CLI 行为：`python scripts/refresh_token_browser.py`（入口名不变）。

DrissionPage 已验证的 API（在本项目 .venv 里确认过，照用即可）：
- `ChromiumOptions().set_browser_path(exe).set_user_data_path(str(path))`
- `page.listen.start(target)` → `page.listen.steps()` 生成器持续 yield 数据包；浏览器被关闭时循环自然结束
- `packet.request.headers` 是请求头 dict
- `page.states.is_alive` 判断浏览器是否还活着
- `page.quit()` 关闭浏览器

- [ ] **Step 1: 实现 capture_token**

在 `scripts/auto_token.py` 的 import 区追加：

```python
import time
from typing import Callable

from DrissionPage import ChromiumOptions, ChromiumPage

from scripts import biji_export
```

在文件末尾追加：

```python
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

    try:
        page = ChromiumPage(options)
    except Exception as exc:
        raise TokenCaptureError(f"启动 Chrome 失败：{exc}") from exc

    captured = None
    try:
        page.listen.start(API_DOMAIN)
        page.get(BIJI_HOME)
        log("已打开 biji.com，正在监听登录请求…")

        start = time.monotonic()
        hinted = False
        for packet in page.listen.steps():
            auth = extract_auth(packet.request.headers)
            if auth:
                captured = auth
                break
            if not hinted and time.monotonic() - start > FIRST_LOGIN_HINT_SECONDS:
                log("还没抓到：请先在浏览器里登录 biji，再打开任意一篇笔记")
                hinted = True
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

    raise TokenCaptureError("未捕获到 Token")
```

- [ ] **Step 2: 语法与导入自检**

Run: `uv run python -c "from scripts.auto_token import capture_token, extract_auth; print('ok')"`
Expected: 输出 `ok`

Run: `uv run pytest tests/test_auto_token.py -v`
Expected: 仍 5 passed（新代码不破坏旧测试）

- [ ] **Step 3: 重写 CLI 为薄壳**

整体替换 `scripts/refresh_token_browser.py`：

```python
"""
Biji.com Token 自动获取脚本
用法: uv run python scripts/refresh_token_browser.py
首次使用会自动打开 Chrome，请登录 biji 并打开任意一篇笔记；
之后再次运行会自动捕获 Token，无需操作。
"""
import sys

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
```

- [ ] **Step 4: 手动验证（需要用户配合登录）**

Run: `uv run python scripts/refresh_token_browser.py`
Expected:
- 弹出 Chrome 窗口打开 biji.com
- 未登录时在浏览器里登录并打开一篇笔记后，终端输出"✅ 已捕获并保存 Token"，浏览器自动关闭
- `cat ~/Library/Application\ Support/BijiExportApp/config/biji_auth.json` 能看到新 Token

再跑一次确认已登录状态下无需操作即可抓到。

- [ ] **Step 5: Commit**

```bash
git add scripts/auto_token.py scripts/refresh_token_browser.py
git commit -m "feat: auto-capture token via DrissionPage + system Chrome"
```

---

### Task 3: GUI 集成（自动获取按钮 + 后台线程）

**Files:**
- Modify: `scripts/gui_app.py`

**Interfaces:**
- Consumes: Task 2 的 `capture_token(log)`、`ChromeNotFoundError`、`CaptureCancelled`、`TokenCaptureError`。
- Produces: GUI 行为变化——"打开 biji 登录页"按钮变为"自动获取 Token"；Token 获取与导出都在后台线程执行，界面不卡死。无新函数签名对外。

- [ ] **Step 1: 改 import 和按钮**

`scripts/gui_app.py` 顶部 import 区，在 `import subprocess` 后加 `import threading`；在 `from scripts import biji_export` 后加：

```python
from scripts import auto_token
```

`build_ui` 中找到：

```python
self.open_login_button = ttk.Button(auth_btns, text="打开 biji 登录页", command=self.handle_refresh_token)
```

替换为：

```python
self.open_login_button = ttk.Button(auth_btns, text="自动获取 Token", command=self.handle_auto_token)
```

同一段上面那行说明文字：

```python
            text="先点“打开 biji 登录页”，登录后打开任意笔记，在浏览器 DevTools 的 Request Headers 里复制 token。",
```

替换为：

```python
            text="点“自动获取 Token”后会弹出 Chrome：首次使用请登录 biji 并打开任意笔记，之后自动完成。抓不到时再手动粘贴。",
```

- [ ] **Step 2: 替换 handle_refresh_token 为后台线程版**

删除整个 `handle_refresh_token` 方法（原来的 webbrowser 流程），替换为：

```python
    def handle_auto_token(self):
        self.set_busy(True, "正在自动获取 Token...")
        self.append_log("启动 Chrome，准备自动获取 Token…")
        threading.Thread(target=self._auto_token_worker, daemon=True).start()

    def _auto_token_worker(self):
        def log(msg):
            self.root.after(0, self.append_log, msg)

        try:
            auto_token.capture_token(log=log)
        except auto_token.CaptureCancelled:
            self.root.after(0, self._auto_token_done, None)
        except Exception as exc:
            self.root.after(0, self._auto_token_done, str(exc))
        else:
            self.root.after(0, self._auto_token_done, "success")

    def _auto_token_done(self, result):
        self.set_busy(False, "准备就绪")
        self.refresh_auth_status()
        if result == "success":
            self.append_log("✅ Token 已自动获取并保存")
            messagebox.showinfo("获取成功", "Token 已自动获取并保存")
        elif result is None:
            self.append_log("已取消获取 Token（浏览器窗口被关闭）")
        else:
            self.append_log(f"❌ {result}")
            messagebox.showerror("获取失败", result)
```

- [ ] **Step 3: 导出移到后台线程**

把整个 `handle_export` 方法替换为：

```python
    def handle_export(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("缺少 URL", "请先输入 biji 博主页面 URL")
            return

        topic_text = self.topic_id_var.get().strip()
        topic_id = None
        if topic_text:
            try:
                topic_id = int(topic_text)
            except ValueError:
                messagebox.showwarning("Topic ID 无效", "Topic ID 必须是数字")
                return

        output = self.output_dir_var.get().strip() or None
        self.set_busy(True, "正在导出笔记...")
        self.append_log(f"开始导出：{url}")
        threading.Thread(
            target=self._export_worker, args=(url, topic_id, output), daemon=True
        ).start()

    def _export_worker(self, url, topic_id, output):
        try:
            result = biji_export.export_notes(
                url, topic_id_override=topic_id, output_dir=output
            )
        except Exception as exc:
            self.root.after(0, self._export_done, None, str(exc))
        else:
            self.root.after(0, self._export_done, result, None)

    def _export_done(self, result, error):
        self.set_busy(False, "准备就绪")
        self.refresh_auth_status()
        if error is not None:
            self.append_log(f"❌ {error}")
            messagebox.showerror("操作失败", error)
            return
        self.append_log(f"✅ 导出完成：{result['author_name']}，共 {result['count']} 条")
        self.append_log(f"输出目录：{result['output_dir']}")
        self.append_log(f"Markdown：{result['markdown_path']}")
        self.append_log(f"JSON：{result['json_path']}")
        messagebox.showinfo(
            "导出完成",
            f"已导出 {result['count']} 条笔记\n\n输出目录:\n{result['output_dir']}\n\nMarkdown:\n{result['markdown_path']}",
        )
```

（与原逻辑一致，只是搬到后台线程；`webbrowser` import 如果不再被引用则一并删除——替换后检查文件头部。）

- [ ] **Step 4: 自检**

Run: `uv run python -c "import ast; ast.parse(open('scripts/gui_app.py').read()); print('syntax ok')"`
Expected: `syntax ok`

Run: `uv run pytest tests/ -v`
Expected: 5 passed

- [ ] **Step 5: 手动验证（需要用户配合）**

Run: `uv run python scripts/gui_app.py`
Expected:
- 点"自动获取 Token"→ Chrome 弹出 →（已登录状态）几秒内日志显示"✅ Token 已自动获取并保存"，期间界面可正常拖动不卡死
- 抓取途中手动关闭 Chrome 窗口 → 日志显示"已取消"，界面恢复就绪
- 粘贴一个博主 URL 点"开始导出"→ 界面不卡死，完成后显示导出结果

- [ ] **Step 6: Commit**

```bash
git add scripts/gui_app.py
git commit -m "feat: auto token button in GUI, run capture and export in background threads"
```

---

### Task 4: 打包修复、依赖清理与整体验证

**Files:**
- Modify: `Biji导出小工具.spec`（路径错误修复 + hiddenimports 更新）
- Modify: `pyproject.toml`（移除 playwright）
- Modify: `README.md`（更新 Token 获取说明）

**Interfaces:**
- Consumes: 前三个任务的全部产出。
- Produces: 可用的 `dist/Biji导出小工具.app`。

背景：`Biji导出小工具.spec` 里的 `pathex` 和 `datas` 指向 `/Users/macbook/Downloads/getbiji_dy_export`（**错误路径**，项目在 Documents 下），且 `hiddenimports` 包含已改为薄壳的 `scripts.refresh_token_browser`。

- [ ] **Step 1: 确认 playwright 已无引用**

Run: `grep -rn "playwright" scripts/`
Expected: 无任何输出（Task 2 重写后应无残留）。若有残留，先清掉再继续。

- [ ] **Step 2: 移除 playwright 依赖**

`pyproject.toml` 的 `dependencies` 中删除 `"playwright>=1.55.0",` 一行。

Run: `uv sync`
Run: `uv run pytest tests/ -v`（Expected: 5 passed）
Run: `uv run python -c "from scripts.auto_token import capture_token; print('ok')"`（Expected: `ok`）

- [ ] **Step 3: 修复 spec 文件**

将 `Biji导出小工具.spec` 中：

```python
    pathex=['/Users/macbook/Downloads/getbiji_dy_export'],
```

改为：

```python
    pathex=['/Users/macbook/Documents/getbiji_dy_export'],
```

```python
    datas=[('/Users/macbook/Downloads/getbiji_dy_export/scripts', './scripts')],
```

改为：

```python
    datas=[('/Users/macbook/Documents/getbiji_dy_export/scripts', './scripts')],
```

```python
    hiddenimports=['scripts.app_paths', 'scripts.biji_export', 'scripts.refresh_token_browser'],
```

改为：

```python
    hiddenimports=['scripts.app_paths', 'scripts.biji_export', 'scripts.auto_token'],
```

- [ ] **Step 4: 重新打包**

Run: `./build_macos_app.sh`
Expected: 成功生成 `dist/Biji导出小工具.app`，无 ImportError。若报 DrissionPage 相关模块缺失，在 spec 的 `hiddenimports` 补上对应模块名后重跑。

- [ ] **Step 5: 手动验证打包版（需要用户配合）**

双击打开 `dist/Biji导出小工具.app`：
- 点"自动获取 Token"→ 几秒内自动抓到（chrome_profile 已在本机有登录态）
- 用新 Token 导出一次笔记，确认可用

- [ ] **Step 6: 更新 README**

`README.md` 中"图形界面版本"和"打包成可双击启动的 macOS 应用"两节的 Token 获取步骤，统一改为：

```markdown
1. 点击"自动获取 Token"
2. 首次使用：在弹出的 Chrome 中登录 biji，并打开任意一篇笔记；工具会自动捕获并保存 Token
3. 之后再用：点一下按钮即可，无需重复登录
4. （兜底）也可以手动从 DevTools 复制 authorization / xi-csrf-token 粘贴保存
```

"命令行版本"一节的自动化脚本说明里，把"自动打开一个浏览器窗口"的描述同步为"自动打开 Chrome（使用系统 Chrome 与独立用户数据目录）"。环境要求一节把"Chrome / Chromium"改为"Chrome"，并删除 `uv run playwright install chromium` 一行。

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "build: fix spec paths, drop playwright, update README for auto token"
```

---

## Self-Review 记录

- **Spec 覆盖**：核心模块（Task 1/2）、CLI 薄壳（Task 2）、GUI 按钮与后台线程（Task 3）、spec 修复与打包验证（Task 4）、README（Task 4）、移除 playwright（Task 4）——设计文档每条都有对应任务。
- **类型一致性**：`capture_token(log=...)` 签名在 Task 2 定义、Task 3 消费一致；异常类名 `ChromeNotFoundError` / `CaptureCancelled` / `TokenCaptureError` 全文一致；`_auto_token_done(result)` 用 `"success"` / `None` / 错误字符串三态，定义与使用一致。
- **已知取舍**：`capture_token` 的浏览器流程无法自动化测试（依赖真实登录），按设计文档以手动验证代替，单元测试只覆盖纯逻辑 `extract_auth`。
