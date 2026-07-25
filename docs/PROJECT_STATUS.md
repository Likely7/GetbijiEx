# 项目状态

> 最后更新：2026-07-26
> 当前阶段：核心功能完成，进入公开发布前的稳定化阶段
> 主分支：`main`
> 远端仓库：https://github.com/Likely7/GetbijiEx

## 项目目标

GetbijiEx 用于把 biji.com（Get笔记/得到大脑）知识库中订阅博主的笔记批量导出为 Markdown 和 JSON。产品同时面向两类用户：

- 普通用户：通过本地 GUI 登录、选择知识库和博主、查看进度并导出。
- Agent 用户：通过 JSON CLI 和内置 Skill 调用，不需要打开 GUI。

## 当前能力

| 模块 | 状态 | 说明 |
|---|---|---|
| 自动获取 Token | 已完成 | 独立 Chrome 配置保存 Cookie 和登录态；短期 JWT 过期后可自动刷新 |
| 知识库列表 | 已完成 | 合并用户创建与订阅的知识库 |
| 博主列表 | 已完成 | 支持自动分页 |
| Markdown / JSON 导出 | 已完成 | 支持选择式导出和 URL 兜底模式 |
| 导出进度 | 已完成 | GUI 显示当前条目和总体进度，完成后打开输出目录 |
| 跨平台数据目录 | 已完成 | macOS、Windows、Linux 分别使用各自标准应用数据目录 |
| 双模式应用 | 已完成 | 无参数启动 GUI，带参数进入 JSON CLI |
| Agent Skill | 已完成 | 支持标准 `npx skills add`、Claude Code、Codex 和自定义 Skill 根目录 |
| 小白安装说明 | 已完成 | README 提供 npx 单行命令、可直接复制给 Agent 的完整安装提示词和各平台命令 |
| macOS 打包 | 已完成 | 本机与 GitHub Actions 均已验证 |
| Windows 打包 | 已完成 | GitHub Actions 已验证可生成 Windows 产物 |
| 自动化测试 | 已完成 | 覆盖 Token 提取、列表分页、CLI、Skill 安装、npx 启动器和数据迁移 |
| 正式 Release | 待完成 | 需要确定版本号、生成发布说明并上传版本产物 |

## 最近验证基线

2026-07-26 对 npx Skill 安装改造完成了本地发布前验证：

- `pytest`：28 个测试通过。
- Node 启动器：13 个测试通过，其中包含不信任工作目录源码、缺失 `uv` 提示和参数/退出码转发测试。
- 标准 `skills` CLI 可以发现并在隔离 HOME 中安装 `getbijiex`。
- 源码版和打包版 `install-skill` 均能复制完整 Skill 资源并生成直连命令。
- macOS Apple Silicon PyInstaller 构建成功，打包版 CLI 和 Skill 安装命令通过烟雾测试。
- Git diff 格式检查和敏感信息扫描通过。
- Linux 与 Windows 的 Node 启动器测试已纳入 GitHub Actions；推送后仍需确认远端工作流结果。

历史完整发布基线为提交 `9d466ca`；本文件之后的改动仍须按 [发布检查清单](RELEASE_CHECKLIST.md) 重新验证，不能沿用旧结果代替新验证。

## 当前工作重点

1. 在真实 Windows 设备上验证 GUI、Chrome Token 获取和导出全流程。
2. 准备首个公开版本号与 Release 说明，让普通用户可以直接下载稳定版本，而不是从 Actions 获取产物。
3. 在 Intel Mac 上验证或提供 `x86_64` / universal2 构建。
4. 缩减不再使用的历史依赖，降低打包体积。

## 已知限制

- Biji 的 JWT 大约 30 分钟过期；这是接口机制，不代表网站 Cookie 登录态失效。
- 首次使用仍需要用户在 GetbijiEx 打开的 Chrome 窗口中登录 biji。
- macOS 应用未做 Apple Developer ID 签名和公证，首次打开可能需要用户在系统安全设置中确认。
- macOS 构建产物与构建机器架构一致；当前本地验证产物为 Apple Silicon。
- GitHub Actions 可以构建 Windows 产物，但真实 Windows GUI 与 Chrome 联动仍需要人工验收。
- npx 命令只安装 Skill，不包含 GetbijiEx 软件本身；使用 npx 安装的 Skill 需要 Node.js 22.20+，本机必须已有 App、Windows 程序或源码；源码模式还需要 Python 3.11+ 和 `uv`。
- Biji 是外部服务，其接口结构和鉴权规则变化可能导致功能失效。

## 项目文档

- [路线图](ROADMAP.md)：后续阶段、优先级和完成标准。
- [发布检查清单](RELEASE_CHECKLIST.md)：每次公开发布前必须执行的验证。
- [技术决策记录](DECISIONS.md)：关键架构选择及其原因。
- [README](../README.md)：面向用户的安装与使用说明。
