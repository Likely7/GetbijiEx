# get-biji-export

把 Get 笔记（biji.com）的笔记数据导出为 Markdown。  

## 功能

- **抖音号关注作者笔记导出**：通过API批量导出抖音号关注作者的全部笔记（含完整原文内容）
- 自动分页获取所有笔记
- 支持从 URL 自动解析参数
- **自动获取 Token**：一键弹出 Chrome 自动捕获认证信息，首次登录一次即可（驱动系统 Chrome，登录态持久化）
- **本地 GUI 小工具**：支持自动/手动保存 Token、自定义输出目录、导出 Markdown / JSON
- **Agent 集成**：app 是双模式的——双击是 GUI，终端里带参数调用就是 CLI（输出 JSON），配合一键安装的 Claude Code Skill，Agent 可以直接帮你导出笔记

## Agent / CLI 用法

打包后的 app 自带命令行模式（无需 Python 环境）：

```bash
# macOS 打包版（路径按实际安装位置调整）
"/Applications/Biji导出小工具.app/Contents/MacOS/Biji导出小工具" topics

# 源码版
uv run python scripts/biji_cli.py topics
```

子命令（全部输出 JSON）：`topics`（知识库列表）、`follows <id_alias>`（博主列表）、`export --follow-id N --name X --alias Y`、`export-url <URL>`、`token`（刷新 Token）、`install-skill`。

使用 Claude Code 的话，点 GUI 里的「安装 Skill」按钮（或运行 `install-skill` 子命令），会把 Skill 安装到 `~/.claude/skills/biji-export/`，之后直接对 Agent 说"导出某某博主的笔记"即可。

## 环境要求

- Python 3.11+
- `uv`（依赖管理与运行）
- Chrome（用于自动获取 Token）

> **Windows / Linux 用户**：仓库内的打包脚本生成的是 macOS `.app`，但源码本身是跨平台的——按下方"安装"一节装好依赖后，直接 `uv run python scripts/gui_app.py` 即可使用；数据会存到 `%APPDATA%\BijiExportApp`（Windows）或 `~/.local/share/BijiExportApp`（Linux）。如需 Windows 可执行文件，在 Windows 上自行运行 PyInstaller 打包即可。

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
2. 首次使用：在弹出的 Chrome 中登录 biji，并打开任意一篇笔记；工具会自动捕获并保存 Token
3. 之后再用：点一下按钮即可，无需重复登录
4. （兜底）也可以手动从 DevTools 复制 `authorization` / `xi-csrf-token` 粘贴后点“保存 Token”
5. Token 保存后会自动加载知识库列表（也可手动点“加载知识库”）
6. 在下拉框里选择知识库 → 自动列出该库的博主 → 选择要导出的博主
7. 按需选择任意输出目录（也可恢复默认目录）
8. 点击“开始导出”

（兜底）也可以在“手动模式”里直接粘贴博主页面 URL、可选填 `topic_id` 导出。

应用数据会写到：

```text
~/Library/Application Support/BijiExportApp/
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
dist/Biji导出小工具.app
```

之后可直接在 Finder 中双击打开。

打包后的 `.app` 里，Token 获取流程与源码模式相同：

1. 点击“自动获取 Token”
2. 首次使用：在弹出的 Chrome 中登录 biji，并打开任意一篇笔记；工具会自动捕获并保存 Token
3. 之后再用：点一下按钮即可
4. （兜底）也可以手动从 DevTools 复制 `authorization` / `xi-csrf-token` 粘贴保存
5. 再执行导出

### 命令行版本

### 1. 配置认证信息

最简单的方法是使用自动化脚本：

```bash
python scripts/refresh_token_browser.py
# 或使用 uv 运行
uv run scripts/refresh_token_browser.py
```

脚本会自动打开一个浏览器窗口：
1. 请在窗口中登录 biji.com
2. 登录后点击任意一篇笔记
3. 脚本会自动捕获 Token 并保存到 `config/biji_auth.json`
4. 看到 "Token 已更新" 提示后即可关闭窗口

**备选方案（手动抓包）：**

如果自动化脚本无法工作，可以运行手动引导模式：

```bash
python scripts/biji_export.py --update-token
```

### 2. 导出笔记

```bash
# 从 URL 导出
python scripts/biji_export.py "https://www.biji.com/subject/BJ8XV7AJ/DEFAULT?followId=1077890&followName=第四种黑猩猩"

# 指定 topic-id（当自动获取失败时）
python scripts/biji_export.py "https://www.biji.com/subject/20jqglxY/DEFAULT?followId=1109306" --topic-id 2362709
```

### 3. 输出

导出的 Markdown 文件默认保存在 `data/biji_export/` 目录；GUI 模式下也可以自行指定输出目录。

```text
data/biji_export/
├── 第四种黑猩猩_完整导出_20260207.md
├── AI樟榆树_完整导出_20260207.md
└── ...
```

## 目录结构

```text
get-biji-export/
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

当遇到 `401 Unauthorized` 或 `500 Server Error` 时，通常是 Token 过期。

- GUI / 打包 app：再点一次“自动获取 Token”即可；抓不到时手动复制新的 `authorization` / `xi-csrf-token` 后点“保存 Token”
- 命令行 / 源码模式：重新运行 `scripts/refresh_token_browser.py`

### 获取 topic_id

如果脚本无法自动获取 `topic_id`，可以：

1. 在浏览器中打开目标页面
2. 打开 DevTools → Network
3. 查找 `topic/detail` 或相关 posts 请求，从请求参数 / 请求体中获取 `topic_id`
4. 在 GUI 中填写 Topic ID，或在命令行使用 `--topic-id`

## 安全提示

- 不要把认证信息（`config/biji_auth.json` 或 `.env`）提交到 git
- `config/` 和 `data/` 目录已在 `.gitignore` 中忽略
