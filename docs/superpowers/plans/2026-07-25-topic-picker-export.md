# 知识库/博主点选导出实现计划

日期：2026-07-25
前置：API 已实测验证（见 `~/.claude/skills/web-access/references/site-patterns/biji.com.md`）

## 目标

把 GUI 的"手动粘贴博主 URL + Topic ID"改为：获取 Token → 加载知识库列表 → 选知识库 → 选博主 → 导出。手动 URL 保留为兜底。

## 已验证的 API

- `GET /v1/web/topic/mine/list` → `c`: 数组，含 `id_alias`、`name`、`extend_data.all_resource_count`
- `GET /v1/web/subscribe/topic/list?page=1&size=200&exclude_mine=true` → `c.list`，结构同上
- `GET /v1/web/follow/list?topic_id=-1&topic_id_alias={alias}&type=1&page=1&page_size=50` → `c.list`，含 `id`（followId）、`name`、`topic_id`、`extend_data.get_note_count`、`has_next`（分页）
- 认证：现有 `authorization` + `xi-csrf-token` + `x-appid` 请求头
- 失败：token 过期返回 `{"message":"LoginRequired"}`

## Task 1: biji_export.py 加列表接口（TDD）

新增函数：

```python
class AuthError(ExportError): ...  # Token 过期/无效

def list_topics() -> list[dict]:
    """合并我创建的 + 我订阅的知识库。
    返回 [{"id_alias": str, "name": str, "count": int, "source": "mine"|"sub"}]"""

def list_follows(topic_id_alias: str) -> list[dict]:
    """知识库内博主列表（自动分页）。
    返回 [{"follow_id": int, "name": str, "topic_id": int, "note_count": int, "platform": str}]"""
```

- 两者内部用 GET + `get_headers()`；响应无 `c` 字段且 message 含 `LoginRequired` 时抛 `AuthError`
- 重构：`export_notes(url, ...)` 拆出 `export_notes_core(follow_id, author_name, topic_id_alias, topic_id_override, output_dir)`，URL 解析后调 core；GUI 新流程直接调 core
- 测试 `tests/test_biji_lists.py`：monkeypatch `requests.get`，覆盖正常返回、LoginRequired 抛 AuthError、follow 分页翻页

## Task 2: GUI 改造

`gui_app.py` 导出区改为：

1. 「加载知识库」按钮 → 后台线程拉 `list_topics()`，填入 Combobox（显示 `名称 (N 个内容)`）
2. 选中知识库 → 后台线程拉 `list_follows()`，填入博主 Combobox（显示 `博主名 (N 篇)`）
3. 「开始导出」：优先用选中的博主（调 `export_notes_core`）；未选择时回退到手动 URL 输入框（现有逻辑）
4. 手动 URL / Topic ID 输入框保留，标注"手动模式（可选）"
5. `AuthError` → 提示"Token 已过期，请重新点「自动获取 Token」"

## Task 3: 验证 + 打包

- 跑全部 pytest
- 手动验证 GUI 完整流程（需用户在场，token 有效）
- 重新打包 `.app`，验证打包版
- 更新 README 使用步骤
- commit

## 自审

- 接口字段名与已验证的响应一致（`id_alias`/`all_resource_count`/`follow list 的 id`）
- 不改动现有导出主流程逻辑，只拆函数
- 手动模式保留，满足设计兜底要求
