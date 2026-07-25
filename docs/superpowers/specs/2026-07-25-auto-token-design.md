# 自动获取 Token 功能设计

日期：2026-07-25
状态：已确认

## 背景与目标

目前获取 biji.com 的认证 Token（`authorization` / `xi-csrf-token`）需要用户手动打开浏览器 DevTools 复制，流程繁琐。项目里已有基于 Playwright 的自动抓取脚本（`refresh_token_browser.py`），但：

1. 没有接入 GUI；
2. 打包成 `.app` 后因找不到 Playwright 的 Chromium 而报错，打包版只能手动粘贴。

**目标**：在 GUI 和命令行中提供"一键自动获取 Token"，源码运行和打包后的 `.app` 都能用；用户只需在首次使用时登录一次 biji。

**非目标**：

- 不做首次运行引导、新手教程等额外 UX（用户明确表示不需要）。
- 不处理 app 签名 / 公证问题。
- 不删除手动粘贴 Token 的入口（保留为兜底）。

## 方案选型

采用 **DrissionPage 驱动系统 Chrome**，理由：

- DrissionPage 已在 `pyproject.toml` 依赖中（此前未使用）；
- 纯 Python 实现，PyInstaller 打包无额外负担（对比 Playwright 需要打包内置 node driver，这正是打包版报错的根源）；
- 直接启动系统已安装的 Chrome，无需下载浏览器内核。

被拒绝的备选：Playwright `channel="chrome"`（打包复杂）、本地代理抓包（HTTPS 证书问题，过度设计）。

## 整体结构

```
scripts/auto_token.py              # 新增：核心模块，DrissionPage 抓 Token
scripts/gui_app.py                 # 修改：加「自动获取 Token」按钮，后台线程执行
scripts/refresh_token_browser.py   # 修改：改为薄壳，内部调用 auto_token.py
```

## 核心流程（auto_token.py）

1. 用 DrissionPage 启动系统 Chrome，用户数据目录为
   `~/Library/Application Support/BijiExportApp/chrome_profile/`（即 `user_data_root() / "chrome_profile"`），登录态由此持久化。
2. 开始监听网络请求，打开 `https://www.biji.com`。
3. 监听发往 `knowledge-api.trytalks.com` 的请求，从请求头中提取
   `authorization`、`xi-csrf-token`、`x-appid`。
   - 已登录时，biji 首页会自动发起该域名的 API 请求，无需用户额外操作。
4. 抓到后调用现有的 `biji_export.save_auth_config()` 保存，自动关闭浏览器。
5. 若 120 秒内未抓到（典型情况：首次使用、未登录），通过日志回调提示
   "请在浏览器中登录 biji 并打开任意一篇笔记"，继续等待，直到抓到或用户关闭浏览器窗口（视为取消）。

**对外接口**：一个主函数，接受日志回调（`Callable[[str], None]`）和取消检测，返回成功/失败结果。GUI 与 CLI 各自接入。

## GUI 改动（gui_app.py）

- "打开 biji 登录页"按钮改为"**自动获取 Token**"，点击后在后台线程执行上述流程；
  日志通过 `root.after(0, ...)` 安全刷回界面；结束后自动刷新 Token 状态显示。
- 顺带修复已知问题：**导出也移到后台线程**，避免长导出时界面卡死。
  （日志输出同理走 `root.after`。）
- 手动粘贴 Token 的输入框和"保存 Token"按钮保留不动。

## 命令行改动（refresh_token_browser.py）

- 入口命令 `python scripts/refresh_token_browser.py` 保持不变；
- 内部实现从 Playwright 换成调用 `auto_token.py`；
- 依赖随之清理：`pyproject.toml` 移除 `playwright`（确认无其他引用后）。

## 异常处理

| 情况 | 行为 |
|---|---|
| 未安装 Chrome | 提示"未找到 Chrome，请使用手动粘贴 Token"，界面恢复就绪 |
| 用户中途关闭浏览器窗口 | 视为取消，不报错，界面恢复就绪 |
| 超时未抓到且窗口被关 | 同上，按取消处理 |
| 抓到但保存失败 | 报错并保留浏览器现场提示重试（复用现有异常提示方式） |

## 打包注意事项

- 确认 `Biji导出小工具.spec` 不打包 `config/biji_auth.json` 和用户数据（开发时检查）。
- DrissionPage 为纯 Python，预期 PyInstaller 直接可打包；若缺隐式依赖，在 spec 的 `hiddenimports` 补充。

## 验证方式（手动）

依赖真实登录，不写自动化测试：

1. 源码模式跑 GUI，删除旧配置 → 点"自动获取 Token" → 登录 biji → 确认抓到并保存。
2. 再点一次 → 确认无需重新登录、数秒内抓到。
3. 用抓到的 Token 实际导出一次笔记，确认 Token 可用。
4. 重新打包 `.app`，在打包版重复第 2、3 步。
5. 命令行 `python scripts/refresh_token_browser.py` 跑通一次。
