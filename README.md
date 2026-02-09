# get-biji-export

把 Get 笔记（biji.com）的笔记数据导出为 Markdown。  

## 功能

- **抖音号关注作者笔记导出**：通过API批量导出抖音号关注作者的全部笔记（含完整原文内容）
- 自动分页获取所有笔记
- 支持从 URL 自动解析参数
- 认证信息集中管理，支持交互式 Token 更新

## 环境要求

- Python 3.11+
- `uv`（依赖管理与运行）
- Chrome / Chromium（用于首次登录抓取 token）

## 安装

```bash
pip install requests
```

或使用 uv:

```bash
uv sync
```

## 快速开始

### 1. 配置认证信息

首次使用需要配置认证信息。打开浏览器访问 biji.com 并登录，然后：

1. 打开 Chrome DevTools (F12) → Network 标签
2. 触发任意 `knowledge-api.trytalks.com` 请求
3. 复制以下请求头值到 `config/biji_auth.json`：

```json
{
    "authorization": "Bearer eyJhbGc...",
    "xi-csrf-token": "xxx",
    "x-appid": "3",
    "cookie": "..."
}
```

或者使用交互式更新：

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

导出的 Markdown 文件保存在 `data/biji_export/` 目录：

```
data/biji_export/
├── 第四种黑猩猩_完整导出_20260207.md
├── AI樟榆树_完整导出_20260207.md
└── ...
```

## 目录结构

```
get-biji-export/
├── config/
│   └── biji_auth.json      # 认证配置
├── data/
│   └── biji_export/        # 导出文件
├── scripts/
│   ├── biji_export.py      # 主导出脚本
│   └── refresh_token_browser.py  # Token 刷新工具
└── README.md
```

## 常见问题

### Token 过期

当遇到 `401 Unauthorized` 或 `500 Server Error` 时，通常是 Token 过期。运行：

```bash
python scripts/biji_export.py --update-token
```

按提示更新认证信息即可。

### 获取 topic_id

如果脚本无法自动获取 `topic_id`，可以：

1. 在浏览器中打开目标页面
2. 打开 DevTools → Network
3. 查找 `topic/detail` 请求，从请求体中获取 `topic_id`
4. 使用 `--topic-id` 参数指定

## 安全提示

- 不要把认证信息提交到 git
- `config/` 和 `data/` 目录已在 `.gitignore` 中忽略
