# GetbijiEx

把 Get 笔记（biji.com）的笔记数据导出为 Markdown。  

## 项目文档

- [项目状态](docs/PROJECT_STATUS.md)：当前能力、验证基线、工作重点和已知限制
- [路线图](docs/ROADMAP.md)：发布阶段、优先级和后续任务
- [发布检查清单](docs/RELEASE_CHECKLIST.md)：测试、安全、GUI、CLI 和多平台发布验收
- [技术决策记录](docs/DECISIONS.md)：关键架构选择及其原因

## 功能

- **抖音号关注作者笔记导出**：通过API批量导出抖音号关注作者的全部笔记（含完整原文内容）
- 自动分页获取所有笔记
- 支持从 URL 自动解析参数
- **自动获取 Token**：一键弹出 Chrome 自动捕获认证信息，首次登录一次即可（驱动系统 Chrome，登录态持久化）
- **本地 GUI 小工具**：支持自动/手动保存 Token、自定义输出目录、导出 Markdown / JSON
- **Agent 集成**：GetbijiEx 是双模式应用——双击打开 GUI，终端带参数调用 CLI（stdout 输出 JSON）；内置 Skill 可一键安装到 Claude Code 或 Codex，也可通过命令安装到其他 Agent 的 Skill 目录

## Agent / CLI 用法

打包后的 app 自带命令行模式（无需 Python 环境）：

```bash
# macOS 打包版（路径按实际安装位置调整）
"/Applications/GetbijiEx.app/Contents/MacOS/GetbijiEx" topics

# 源码版
uv run python scripts/biji_cli.py topics
```

子命令（全部输出 JSON）：`topics`（知识库列表）、`follows <id_alias>`（博主列表）、`export --follow-id N --name X --alias Y`、`export-url <URL>`、`token`（刷新 Token）、`install-skill`。

### 安装 Agent Skill

GUI 顶部的「Agent 集成」区域可以直接安装到 Claude Code 或 Codex。也可以在终端单独安装：

```bash
# 以下 CLI 代表打包版可执行文件；源码版把它替换为：
# uv run python scripts/biji_cli.py
CLI="/Applications/GetbijiEx.app/Contents/MacOS/GetbijiEx"

# Claude Code：~/.claude/skills/getbijiex/SKILL.md
"$CLI" install-skill

# Codex：~/.codex/skills/getbijiex/SKILL.md
"$CLI" install-skill --agent codex

# 其他 Agent：指定其 Skill 根目录
"$CLI" install-skill --dir "/path/to/agent/skills"
```

安装后，直接对 Agent 说“导出某某博主的 biji 笔记”即可。Skill 会调用本机 GetbijiEx，不需要打开 GUI。

## 环境要求

- Python 3.11+
- `uv`（依赖管理与运行）
- Chrome（用于自动获取 Token）

> **Windows / Linux 用户**：源码本身跨平台。按下方“安装”一节装好依赖后，运行 `uv run python scripts/gui_app.py` 即可；数据会保存在 `%APPDATA%\GetbijiEx`（Windows）或 `~/.local/share/GetbijiEx`（Linux）。仓库内同时提供 macOS、Windows 构建脚本，并通过 GitHub Actions 在对应系统生成安装包。

## 安装

推荐使用 `uv` 进行依赖管理：

```bash
# 安装 uv (如果尚未安装)
pip install uv

# 同步依赖 (会自动创建虚拟环境并安装所有依赖)
uv sync
```

或者使用 pip 手动安装：

```bash
pip install requests DrissionPage
```

## 快速开始

### 图形界面版本（推荐）

仓库现在提供一个本地小工具界面：

```bash
uv run python scripts/gui_app.py
```

你可以在界面里：

1. 点击“自动获取 Token”
2. 首次使用：在弹出的 Chrome 登录窗口中登录 biji；登录成功后工具会自动进入知识库页面、捕获并保存 Token
3. 之后再用：点击一次按钮即可；独立 Chrome 配置会保留登录态，不需要每次重新登录
4. （兜底）也可以手动从 DevTools 复制 `authorization` / `xi-csrf-token` 粘贴后点“保存 Token”
5. Token 保存后会自动加载知识库列表（也可手动点“加载知识库”）
6. 在下拉框里选择知识库 → 自动列出该库的博主 → 选择要导出的博主
7. 按需选择任意输出目录（也可恢复默认目录）
8. 点击“开始导出”

（兜底）也可以在“手动模式”里直接粘贴博主页面 URL、可选填 `topic_id` 导出。

应用数据会写到：

```text
~/Library/Application Support/GetbijiEx/
```

其中包括：
- `config/biji_auth.json`
- `data/biji_export/`
- `logs/`

### 打包成可双击启动的 macOS 应用

如果你不想每次通过命令行启动，可以构建 `.app`：

```bash
chmod +x build_macos_app.sh
./build_macos_app.sh
```

构建完成后，应用位于：

```text
dist/GetbijiEx.app
```

之后可直接在 Finder 中双击打开。

打包后的 `.app` 与源码版使用相同的 Token 获取流程：

1. 点击“自动获取 Token”
2. 首次使用时在自动弹出的登录窗口中登录 biji，工具随后自动捕获并保存 Token
3. 后续点击一次即可；只有登录态真正失效时才需要再次登录
4. （兜底）也可以手动从 DevTools 复制 `authorization` / `xi-csrf-token` 粘贴保存
5. 选择知识库和博主后执行导出

### Windows 可执行文件

Windows 需要在 Windows 环境中构建，不能由 macOS 交叉打包：

```powershell
.\build_windows.ps1
```

构建结果位于 `dist\GetbijiEx\GetbijiEx.exe`。仓库的 GitHub Actions 工作流也会同时构建 macOS 与 Windows 压缩包，方便直接下载分发。

### 命令行版本

#### 1. 配置认证信息

最简单的方法是使用自动化脚本：

```bash
python scripts/refresh_token_browser.py
# 或使用 uv 运行
uv run scripts/refresh_token_browser.py
```

脚本会自动打开一个独立的 Chrome 窗口：
1. 首次使用时请在自动弹出的窗口中登录 biji.com
2. 登录成功后，工具会自动打开知识库页面并捕获 Token
3. Token 会保存到 GetbijiEx 应用数据目录的 `config/biji_auth.json`
4. 独立 Chrome 配置会保留 Cookie 和登录态；下次刷新短期 Token 通常不需要重新登录

**备选方案（手动抓包）：**

如果自动化脚本无法工作，可以运行手动引导模式：

```bash
python scripts/biji_export.py --update-token
```

#### 2. 导出笔记

```bash
# 从 URL 导出
python scripts/biji_export.py "https://www.biji.com/subject/BJ8XV7AJ/DEFAULT?followId=1077890&followName=第四种黑猩猩"

# 指定 topic-id（当自动获取失败时）
python scripts/biji_export.py "https://www.biji.com/subject/20jqglxY/DEFAULT?followId=1109306" --topic-id 2362709
```

#### 3. 输出

导出的 Markdown 文件默认保存在 `data/biji_export/` 目录；GUI 模式下也可以自行指定输出目录。

```text
data/biji_export/
├── 第四种黑猩猩_完整导出_20260207.md
├── AI樟榆树_完整导出_20260207.md
└── ...
```

## 目录结构

```text
GetbijiEx/
├── config/
│   └── biji_auth.json      # 认证配置 (自动生成)
├── data/
│   └── biji_export/        # 导出文件
├── scripts/
│   ├── biji_export.py      # 主导出脚本
│   ├── gui_app.py          # 本地 GUI 小工具
│   └── refresh_token_browser.py  # 源码模式浏览器自动化 Token 刷新工具
├── .env.example            # 环境变量示例
└── README.md
```

## 常见问题

### Token 过期

Biji 接口使用的 JWT 大约 30 分钟过期，这是正常现象；GetbijiEx 的独立 Chrome 配置会长期保存 Cookie 和网站登录态，因此刷新 JWT 通常只需要几秒，不等于每次都要重新登录。

- GUI / 打包 app：加载知识库时遇到过期会自动刷新并重试一次，也可以手动点击“自动获取 Token”
- 命令行 / Agent：运行 `token` 子命令，成功后重试原命令
- 只有 biji 网站登录态本身失效时，才需要在弹出的 Chrome 中重新登录

### 获取 topic_id

如果脚本无法自动获取 `topic_id`，可以：

1. 在浏览器中打开目标页面
2. 打开 DevTools → Network
3. 查找 `topic/detail` 或相关 posts 请求，从请求参数 / 请求体中获取 `topic_id`
4. 在 GUI 中填写 Topic ID，或在命令行使用 `--topic-id`

## 安全提示

- 不要把认证信息（`config/biji_auth.json` 或 `.env`）提交到 git
- `config/` 和 `data/` 目录已在 `.gitignore` 中忽略
