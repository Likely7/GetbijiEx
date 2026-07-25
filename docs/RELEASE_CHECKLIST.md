# 发布检查清单

每次创建 Git tag 或 GitHub Release 前复制本清单，并记录执行日期、提交 SHA、执行人和结果。

## 1. 版本与代码状态

- [ ] `git status --short --branch` 显示工作区干净。
- [ ] 本地 `main` 与 `origin/main` 指向同一提交。
- [ ] `pyproject.toml` 中的版本号与计划发布版本一致。
- [ ] README、项目状态和路线图已更新。
- [ ] 本次变更有清晰的提交记录和发布说明。

## 2. 自动化验证

```bash
uv sync --dev
uv run pytest -q
uv run python -m compileall -q scripts
node --test tests/test_getbijiex_launcher.mjs
npx -y skills@1.5.20 add . --list
git diff --check
```

- [ ] 全部测试通过，失败数为 0。
- [ ] Python 模块编译检查通过。
- [ ] Node 跨平台启动器测试在 Linux 和 Windows CI 上通过。
- [ ] 标准 `skills` CLI 能发现 `getbijiex`。
- [ ] Git diff 格式检查通过。

## 3. 敏感信息检查

- [ ] `config/biji_auth.json` 未被 Git 跟踪。
- [ ] `.env` 未被 Git 跟踪。
- [ ] 源码和文档中没有真实 Token、Cookie、手机号或本机私有绝对路径。
- [ ] macOS 与 Windows 构建产物中没有认证配置。
- [ ] 如曾误提交认证信息，已清理待发布分支的全部历史并轮换凭证。

## 4. GUI 验收

- [ ] 应用能正常启动且名称显示为 GetbijiEx。
- [ ] 常见窗口尺寸下所有按钮均可见，没有遮挡或截断。
- [ ] “自动获取 Token”能打开 Chrome；首次登录提示清楚。
- [ ] Token 保存后能加载知识库和博主列表。
- [ ] 导出过程中进度条与当前条目正常更新。
- [ ] 导出结束后 Markdown、JSON 路径正确，输出目录能打开。
- [ ] Claude Code 与 Codex 的 Skill 安装按钮可用。

## 5. CLI 与 Skill 验收

- [ ] `GetbijiEx --help` 正常输出。
- [ ] `topics`、`follows`、`export`、`export-url`、`token` 输出契约符合 Skill 文档。
- [ ] stdout 只有 JSON，过程日志位于 stderr。
- [ ] Claude Code 安装路径正确。
- [ ] Codex 安装路径正确。
- [ ] `--dir` 自定义目录安装正确。
- [ ] GetbijiEx 自带安装器会复制完整 Skill 资源，并把默认启动区块替换为本机直连命令。
- [ ] `npx skills add Likely7/GetbijiEx --skill getbijiex` 能安装 `SKILL.md` 和跨平台启动器。
- [ ] npx 安装后的启动器能自动定位、显式配置并调用现有 GetbijiEx，参数和退出码不会丢失。
- [ ] 启动器不会自动执行当前工作目录或父目录中的同名 `scripts/biji_cli.py`。
- [ ] Skill 中不存在未处理的 `{{CLI_COMMAND}}` 占位符。

## 6. 平台构建

### macOS

- [ ] `./build_macos_app.sh` 构建成功。
- [ ] `dist/GetbijiEx.app` 可以启动。
- [ ] 打包版 CLI 可以运行。
- [ ] 记录构建架构：Apple Silicon、Intel 或 universal2。

### Windows

- [ ] `build_windows.ps1` 或 GitHub Actions 构建成功。
- [ ] `GetbijiEx.exe` 在真实 Windows 10/11 环境可启动。
- [ ] Windows Chrome 检测、登录和 Token 捕获通过。
- [ ] Windows 输出目录和 Agent Skill 路径正确。

## 7. GitHub Release

- [ ] 创建版本 tag。
- [ ] 上传 macOS 和 Windows 构建产物。
- [ ] 生成并公布 SHA-256 校验值。
- [ ] 发布说明包含新功能、修复、已知限制和升级说明。
- [ ] 下载公开产物后再做一次冷启动验证。

## 验收记录模板

```text
版本：
提交 SHA：
日期：
执行人：
测试结果：
macOS 验收：
Windows 验收：
敏感信息检查：
已知限制：
Release 地址：
```
