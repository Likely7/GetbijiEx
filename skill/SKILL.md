---
name: getbijiex
description: 导出 biji.com（Get笔记/得到大脑）知识库中订阅博主（多为抖音）的笔记为 Markdown。当用户想导出 biji 笔记、知识库内容、订阅博主笔记，或提到"biji""得到大脑""Get笔记"导出时使用。依赖本机已安装 GetbijiEx 或其源码。
---

# GetbijiEx

本机装有「GetbijiEx」，以下 CLI 就是它的命令行模式，所有命令**输出 JSON 到 stdout**，过程日志在 stderr。

CLI 命令前缀（后文统称 `CLI`）：

```bash
{{CLI_COMMAND}}
```

## 子命令

```bash
CLI topics                          # 知识库列表：name / id_alias / count / source
CLI follows <id_alias>              # 该知识库的博主列表：name / follow_id / topic_id / note_count
CLI export --follow-id <id> --name <博主名> --alias <id_alias> [--topic-id <id>] [--output-dir <目录>]
CLI export-url <博主页面URL> [--topic-id <id>] [--output-dir <目录>]
CLI token                           # 刷新 Token（弹出浏览器，见下）
```

## 标准流程

1. 用户想导出某博主笔记时：先跑 `topics`；和用户确认知识库后跑 `follows <id_alias>`，按名字匹配目标博主（用户直接给了 followId 可跳过前两步）。
2. 跑 `export`（`follows` 返回里有现成的 `follow_id` 和 `topic_id`）。完成后把 `markdown_path` 告诉用户。导出耗时约每秒 2 篇，几百篇的博主需要几分钟，**设置足够长的 timeout**。
3. 任何命令返回 `{"error": "LoginRequired..."}`（退出码 2）：跑 `CLI token` 刷新。它会弹出 Chrome：
   - 浏览器登录态还在：几秒自动完成，无需用户操作；
   - 登录态失效：浏览器里会出现登录框，**告诉用户「请在弹出的浏览器窗口里登录 biji（扫码或手机验证码）」**，登录成功后会自动继续。token 命令最长阻塞 15 分钟，运行时用长 timeout。
   刷新成功后**重试原命令**。
4. Token（JWT）约 30 分钟过期是正常现象，遇到 LoginRequired 刷新重试即可，不用当作故障。

## 注意

- 导出结果默认在应用数据目录（JSON 结果里的 `output_dir` 字段有完整路径），`markdown_path` 是成品。
- 用户想换输出位置时用 `--output-dir`。
