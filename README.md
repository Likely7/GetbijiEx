# GetbijiEx

把 Get笔记（biji.com / 得到大脑）知识库里订阅博主的笔记，批量导出成 Markdown 和 JSON。

**不会终端、不会 Python、只会用 Agent，也可以安装。直接看下面第一部分。**

## 已经装好软件？一条 npx 命令安装 Skill

如果电脑里已经保留了 GetbijiEx App、Windows 程序或源码，可以把下面一整行复制给支持 Agent Skills 的 Agent 执行：

```bash
npx skills add Likely7/GetbijiEx --skill getbijiex
```

指定安装到 Claude Code：

```bash
npx skills add Likely7/GetbijiEx --skill getbijiex --agent claude-code -g -y
```

指定安装到 Codex：

```bash
npx skills add Likely7/GetbijiEx --skill getbijiex --agent codex -g -y
```

> **这条 npx 命令只安装 Skill，不会安装 GetbijiEx 软件本身。** 它使用的是公开的 `skills` 安装工具，不是本项目发布了一个同名 npm 软件包。执行这条命令需要 Node.js 22.20+。第一次导出时，Skill 会自动查找标准位置和 PATH 中已有的 GetbijiEx；如果没有找到，Agent 会在本机查找并代你配置真实路径。使用源码版时还需要 Python 3.11+ 和 `uv`。

如果你的 Agent 不支持标准 Agent Skills 目录，继续使用下面的完整提示词，让它自己确认 Skill 目录并安装。

---

## 最简单的用法：把这段话复制给你的 Agent

只要 Claude Code、Codex、WorkBuddy 或其他 Agent 能操作本机文件和终端，就可以用下面这段话代你完成安装。

> 点击代码块右上角的复制按钮，把整段复制给你的 Agent。不要自己执行里面的命令。

```text
请直接帮我安装并配置 GetbijiEx，不要只告诉我步骤，请实际执行。

项目地址：https://github.com/Likely7/GetbijiEx

请完成以下事情：
1. 检查我的电脑是 macOS 还是 Windows，并确认已经安装 Git、Python 3.11+ 和 Chrome。
2. 如果没有 uv，请帮我安装 uv。
3. 把项目克隆到一个长期保留、以后不会随便移动的位置；如果已经克隆过，就更新到 main 最新版本。
4. 在项目目录执行 uv sync。
5. 找到“你这个 Agent 自己使用的 Skill 根目录”。不要让我猜路径，也不要默认一定是 Claude Code。请根据你自己的配置确认真实目录。
6. 在 GetbijiEx 项目目录执行：
   uv run python scripts/biji_cli.py install-skill --dir "你确认的 Skill 根目录"
7. 检查安装后的 getbijiex/SKILL.md 是否存在，并确认里面已经没有 {{CLI_COMMAND}} 占位符。
8. 告诉我安装结果，以及以后应该对你说什么才能导出笔记。
9. 如果需要首次登录，请启动 GetbijiEx 图形界面，然后明确告诉我：请在弹出的 Chrome 窗口里登录 biji。登录这一步必须由我本人完成。

如果你没有操作本机终端或文件的权限，请直接告诉我你缺少什么权限，不要假装安装成功。
```

安装完成后，你可以直接对 Agent 说：

```text
帮我导出 Get笔记里「知识库名称」中的「博主名称」全部笔记。
```

如果你不知道准确名称，也可以说：

```text
先列出我的 Get笔记知识库，再让我选择知识库和博主，最后帮我导出。
```

### 第一次使用会发生什么

1. Agent 或软件会打开一个独立的 Chrome 窗口。
2. 你需要在这个窗口里登录 biji，扫码或输入验证码都可以。
3. 登录成功后，GetbijiEx 会自动获取所需凭证。
4. 这个独立 Chrome 会保存 Cookie 和登录状态，通常不需要每次重新登录。
5. Biji 的短期 Token 大约 30 分钟过期是正常现象，GetbijiEx 会利用保存的登录状态重新获取。

---

## 已经装好 GetbijiEx，只想单独安装 Skill

### 支持 Agent Skills 的 Agent：直接复制 npx 命令

```bash
npx skills add Likely7/GetbijiEx --skill getbijiex
```

不带 `-g` 时默认安装到当前项目；希望这个 Agent 在所有项目中都能使用时，加上 `-g`。如果 Agent 要求明确指定目标，可以加上 `--agent claude-code`、`--agent codex` 或它实际支持的 Agent 名称。安装工具会把整个 `getbijiex` Skill 和跨平台启动器一起安装。

### 不支持标准安装方式：让 Agent 调用 GetbijiEx 自带安装器

GetbijiEx 自带的 Skill 安装子命令是 `install-skill`。

> **注意：Skill 不是导出软件本身。** Skill 只是告诉 Agent 怎么调用 GetbijiEx。电脑里必须同时保留 GetbijiEx 软件或源码，删掉以后 Skill 就无法导出。

### 最省事：把这段话复制给 WorkBuddy 或其他 Agent

```text
请帮我把 GetbijiEx Skill 安装到你自己的 Skill 文件夹里。

请先在我的电脑中找到 GetbijiEx：
- 如果是源码版，找到包含 scripts/biji_cli.py 的 GetbijiEx 项目目录；
- 如果是 macOS App，通常在 /Applications/GetbijiEx.app；
- 如果是 Windows 版，找到 GetbijiEx.exe 所在目录。

然后请你自己确认“你这个 Agent 实际使用的 Skill 根目录”，不要让我猜路径。

确认后执行对应命令：

源码版：
uv run python scripts/biji_cli.py install-skill --dir "你的 Skill 根目录"

macOS App：
"/Applications/GetbijiEx.app/Contents/MacOS/GetbijiEx" install-skill --dir "你的 Skill 根目录"

Windows：
& "GetbijiEx.exe 的完整路径" install-skill --dir "你的 Skill 根目录"

最后检查 Skill 根目录下是否生成 getbijiex/SKILL.md，并告诉我安装是否成功。
如果你没有终端或本机文件权限，请直接说明，不能假装安装成功。
```

### 只想复制一条明确命令

如果你的 Agent 已经知道自己的 Skill 根目录，把下面**对应电脑的一整行**复制给它，并告诉它把 `你的 Skill 根目录` 换成真实目录后执行。

#### 源码版

先进入 GetbijiEx 项目目录，再执行：

```bash
uv run python scripts/biji_cli.py install-skill --dir "/你的Agent/skills目录"
```

#### macOS App

```bash
"/Applications/GetbijiEx.app/Contents/MacOS/GetbijiEx" install-skill --dir "/你的Agent/skills目录"
```

#### Windows

在 PowerShell 中执行：

```powershell
& "C:\你解压的位置\GetbijiEx\GetbijiEx.exe" install-skill --dir "C:\你的Agent\skills目录"
```

### Claude Code 和 Codex 有预设命令

在 GetbijiEx 源码目录执行：

```bash
# Claude Code：安装到 ~/.claude/skills/getbijiex/
uv run python scripts/biji_cli.py install-skill

# Codex：安装到 ~/.codex/skills/getbijiex/
uv run python scripts/biji_cli.py install-skill --agent codex
```

如果使用的是 macOS App，把命令前半部分换成：

```bash
"/Applications/GetbijiEx.app/Contents/MacOS/GetbijiEx" install-skill
"/Applications/GetbijiEx.app/Contents/MacOS/GetbijiEx" install-skill --agent codex
```

---

## 不用 Agent，直接下载软件

目前可以从 GitHub Actions 下载自动构建的软件包：

1. 打开 [Build packages 构建页面](https://github.com/Likely7/GetbijiEx/actions/workflows/build.yml)。
2. 点击最上面带绿色对勾的构建记录。
3. 滚动到页面底部的 **Artifacts**。
4. 根据电脑下载：
   - Mac：`GetbijiEx-macOS`
   - Windows：`GetbijiEx-Windows`

> GitHub 可能要求先登录才能下载 Actions 里的 Artifacts。正式 Release 发布后会改成更直接的下载方式。

### Mac 安装

1. 解压 `GetbijiEx-macOS`。
2. 把 `GetbijiEx.app` 拖进“应用程序”。
3. 双击打开。如果 macOS 阻止运行，就右键点击 App，选择“打开”，再确认一次。

### Windows 安装

1. 解压 `GetbijiEx-Windows`。
2. **保留整个 GetbijiEx 文件夹，不要只拿走 exe。**
3. 双击文件夹里的 `GetbijiEx.exe`。
4. 如果 Windows 弹出 SmartScreen 提示，请确认软件来自本仓库后，选择“更多信息”→“仍要运行”。

---

## 图形界面怎么用

打开 GetbijiEx 后，只做下面几步：

1. 点击 **自动获取 Token**。
2. 第一次使用时，在弹出的 Chrome 窗口里登录 biji。
3. 登录完成后，软件会自动加载知识库；也可以点击 **加载知识库**。
4. 选择知识库。
5. 选择博主。
6. 点击 **开始导出**。
7. 等待进度条完成，软件会自动打开输出文件夹。

默认数据位置：

- macOS：`~/Library/Application Support/GetbijiEx/`
- Windows：`%APPDATA%\GetbijiEx\`
- Linux：`~/.local/share/GetbijiEx/`

---

## 常见问题

### 为什么安装了 Skill 还是不能导出？

Skill 只是 Agent 的调用说明，不包含 GetbijiEx 程序。请确认：

- GetbijiEx App、exe 或源码仍然存在；
- 安装 Skill 后没有移动或删除 GetbijiEx；
- Agent 有执行本机命令和访问文件的权限；
- 首次使用时已经在弹出的 Chrome 中登录 biji。

### Token 为什么很快过期？

Biji 的接口 Token 大约 30 分钟过期，这是正常现象，不代表 Cookie 登录状态也失效。GetbijiEx 会使用独立 Chrome 中保存的登录状态刷新 Token。

### Agent 返回 `LoginRequired` 怎么办？

直接对 Agent 说：

```text
请运行 GetbijiEx 的 token 子命令刷新 Token，成功后重试刚才的导出。
```

如果弹出登录窗口，请你本人完成登录。

### 导出的文件在哪里？

命令执行完成后会返回 `markdown_path` 和 `output_dir`。直接对 Agent 说：

```text
请告诉我刚才导出的 Markdown 完整路径，并帮我打开输出文件夹。
```

---

<details>
<summary><strong>给开发者：源码运行、CLI 和构建说明</strong></summary>

## 源码环境

- Python 3.11+
- `uv`
- Chrome

```bash
git clone https://github.com/Likely7/GetbijiEx.git
cd GetbijiEx
uv sync --dev
```

启动 GUI：

```bash
uv run python scripts/gui_app.py
```

查看 CLI：

```bash
uv run python scripts/biji_cli.py --help
```

主要子命令：

```text
topics
follows <id_alias>
export --follow-id N --name X --alias Y
export-url <URL>
token
install-skill
```

CLI 的 stdout 只输出 JSON，过程日志写入 stderr，供 Agent 稳定解析。

## macOS 构建

```bash
./build_macos_app.sh
```

输出：`dist/GetbijiEx.app`

## Windows 构建

在 Windows PowerShell 中执行：

```powershell
.\build_windows.ps1
```

输出：`dist\GetbijiEx\GetbijiEx.exe`

PyInstaller 不能从 macOS 直接交叉构建 Windows 应用。仓库中的 GitHub Actions 会在对应系统分别构建。

## 自动化验证

```bash
uv run pytest -q
node --test tests/test_getbijiex_launcher.mjs
npx -y skills@1.5.20 add . --list
```

最后一条命令用于确认标准 Skill 安装工具能从本仓库发现 `getbijiex`。

</details>

---

## 项目管理文档

以下内容主要给维护者和开发者看，普通用户不需要阅读：

- [项目状态](docs/PROJECT_STATUS.md)
- [路线图](docs/ROADMAP.md)
- [发布检查清单](docs/RELEASE_CHECKLIST.md)
- [技术决策记录](docs/DECISIONS.md)

## 安全提示

- 不要公开或提交 `config/biji_auth.json`、`.env`、Token、Cookie。
- 本项目不会把你的 Biji 登录信息上传到本仓库。
- 登录数据保存在你自己电脑的 GetbijiEx 应用数据目录中。
