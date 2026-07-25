# get-biji-export

把 Get 笔记（biji.com）的笔记数据导出为 Markdown。  

## 功能

- **抖音号关注作者笔记导出**：通过API批量导出抖音号关注作者的全部笔记（含完整原文内容）
- 自动分页获取所有笔记
- 支持从 URL 自动解析参数
- **自动认证刷新**：源码模式提供浏览器自动化脚本，一键获取有效 Token
- **本地 GUI 小工具**：支持手动保存 Token、自定义输出目录、导出 Markdown / JSON

## 环境要求

- Python 3.11+
- `uv`（依赖管理与运行）
- Chrome / Chromium（用于源码模式自动抓 token）

## 安装

推荐使用 `uv` 进行依赖管理：

```bash
# 安装 uv (如果尚未安装)
pip install uv

# 同步依赖 (会自动创建虚拟环境并安装所有依赖，包括 playwright)
uv sync

# 安装浏览器驱动 (仅首次运行需要)
uv run playwright install chromium
```

或者使用 pip 手动安装：

```bash
pip install requests playwright
playwright install chromium
```

## 快速开始

### 图形界面版本（推荐）

仓库现在提供一个本地小工具界面：

```bash
uv run python scripts/gui_app.py
```

你可以在界面里：

1. 点击“打开 biji 登录页”
2. 在浏览器中登录 biji，并打开任意一篇笔记
3. 打开 DevTools → Network，找到 `knowledge-api.trytalks.com` 请求
4. 复制 `authorization`、`xi-csrf-token`，粘贴回工具并点击“保存 Token”
5. 粘贴 biji 博主页面 URL
6. 可选填写 `topic_id`
7. 按需选择任意输出目录（也可恢复默认目录）
8. 点击“开始导出”

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

打包后的 `.app` 里，Token 获取流程是：

1. 点击“打开 biji 登录页”
2. 在系统浏览器里登录 biji，并打开任意笔记
3. 在浏览器 DevTools 的 Network 面板里找到 `knowledge-api.trytalks.com` 请求
4. 复制 `authorization`、`xi-csrf-token`，回到 app 粘贴
5. 点击“保存 Token”
6. 再执行导出

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

- GUI / 打包 app：重新打开 biji 登录页，复制新的 `authorization` / `xi-csrf-token` 后点“保存 Token”
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
