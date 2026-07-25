# 项目状态

> 最后更新：2026-07-25  
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
| Agent Skill | 已完成 | 支持 Claude Code、Codex 和自定义 Skill 根目录 |
| macOS 打包 | 已完成 | 本机与 GitHub Actions 均已验证 |
| Windows 打包 | 已完成 | GitHub Actions 已验证可生成 Windows 产物 |
| 自动化测试 | 已完成 | 覆盖 Token 提取、列表分页、CLI、Skill 安装和数据迁移 |
| 正式 Release | 待完成 | 需要确定版本号、生成发布说明并上传版本产物 |

## 最近验证基线

最近一次完整发布基线为提交 `9d466ca`：

- `pytest`：20 个测试通过。
- macOS PyInstaller 构建成功。
- Windows GitHub Actions 构建成功。
- macOS GUI 已实际启动并检查关键控件。
- Claude Code、Codex、自定义目录三种 Skill 安装方式均验证通过。
- Git 历史和打包产物中不包含 `config/biji_auth.json`。

本文件之后的改动必须按 [发布检查清单](RELEASE_CHECKLIST.md) 重新验证，不能沿用旧结果代替新验证。

## 当前工作重点

1. 修正不同窗口高度下的 GUI 可见性和布局细节。
2. 在真实 Windows 设备上验证 GUI、Chrome Token 获取和导出全流程。
3. 准备首个公开版本号与 Release 说明。
4. 缩减不再使用的历史依赖，降低打包体积。

## 已知限制

- Biji 的 JWT 大约 30 分钟过期；这是接口机制，不代表网站 Cookie 登录态失效。
- 首次使用仍需要用户在 GetbijiEx 打开的 Chrome 窗口中登录 biji。
- macOS 应用未做 Apple Developer ID 签名和公证，首次打开可能需要用户在系统安全设置中确认。
- macOS 构建产物与构建机器架构一致；当前本地验证产物为 Apple Silicon。
- GitHub Actions 可以构建 Windows 产物，但真实 Windows GUI 与 Chrome 联动仍需要人工验收。
- Biji 是外部服务，其接口结构和鉴权规则变化可能导致功能失效。

## 项目文档

- [路线图](ROADMAP.md)：后续阶段、优先级和完成标准。
- [发布检查清单](RELEASE_CHECKLIST.md)：每次公开发布前必须执行的验证。
- [技术决策记录](DECISIONS.md)：关键架构选择及其原因。
- [README](../README.md)：面向用户的安装与使用说明。
