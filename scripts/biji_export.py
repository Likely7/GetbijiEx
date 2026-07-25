"""
Biji.com 通用笔记导出脚本
用法:
  python scripts/biji_export.py <URL>                    # 导出笔记
  python scripts/biji_export.py --update-token           # 更新认证 token

示例:
  python scripts/biji_export.py "https://www.biji.com/subject/20jqglxY/DEFAULT?followId=1109488&followName=水球泡泡"
"""
import requests
import json
import time
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote

from scripts.app_paths import config_dir, output_dir

CONFIG_PATH = config_dir() / "biji_auth.json"
OUTPUT_DIR = output_dir()


class ExportError(Exception):
    pass


class AuthError(ExportError):
    """Token 过期或无效"""


def _get_json(url: str, params: dict | None = None) -> dict:
    """GET 请求并返回 JSON；Token 失效时抛 AuthError。"""
    response = requests.get(url, headers=get_headers(), params=params, timeout=15)
    data = response.json()
    if "LoginRequired" in str(data.get("message", "")):
        raise AuthError("Token 已过期，请重新获取")
    response.raise_for_status()
    return data


def list_topics() -> list:
    """合并我创建的 + 我订阅的知识库。
    返回 [{"id_alias", "name", "count", "source": "mine"|"sub"}]"""
    topics = []

    mine = _get_json("https://knowledge-api.trytalks.com/v1/web/topic/mine/list")
    for t in mine.get("c", []) or []:
        topics.append({
            "id_alias": t.get("id_alias"),
            "name": t.get("name", "未命名"),
            "count": t.get("extend_data", {}).get("all_resource_count", 0),
            "source": "mine",
        })

    sub = _get_json(
        "https://knowledge-api.trytalks.com/v1/web/subscribe/topic/list",
        params={"page": 1, "size": 200, "exclude_mine": "true"},
    )
    for t in (sub.get("c", {}) or {}).get("list", []) or []:
        topics.append({
            "id_alias": t.get("id_alias"),
            "name": t.get("name", "未命名"),
            "count": t.get("extend_data", {}).get("all_resource_count", 0),
            "source": "sub",
        })

    return topics


def list_follows(topic_id_alias: str) -> list:
    """知识库内博主列表（自动分页）。
    返回 [{"follow_id", "name", "topic_id", "note_count", "platform"}]"""
    follows = []
    page = 1
    while True:
        data = _get_json(
            "https://knowledge-api.trytalks.com/v1/web/follow/list",
            params={
                "topic_id": -1,
                "topic_id_alias": topic_id_alias,
                "type": 1,
                "page": page,
                "page_size": 50,
            },
        )
        c = data.get("c", {}) or {}
        for item in c.get("list", []) or []:
            follows.append({
                "follow_id": item.get("id"),
                "name": item.get("name", "未命名"),
                "topic_id": item.get("topic_id"),
                "note_count": item.get("extend_data", {}).get("get_note_count", 0),
                "platform": item.get("platform", ""),
            })
        if not c.get("has_next"):
            break
        page += 1
        time.sleep(0.3)
    return follows


def load_headers() -> dict:
    """从配置文件加载认证 headers"""
    base_headers = {
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
    }
    
    if not CONFIG_PATH.exists():
        print(f"⚠️  配置文件不存在，请先创建: {CONFIG_PATH}")
        print("   运行: python scripts/biji_export.py --update-token")
        return base_headers
    
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            auth = json.load(f)
        
        if not auth.get("authorization"):
            print("⚠️  配置文件中 authorization 为空")
            print("   运行: python scripts/biji_export.py --update-token")
            return base_headers
            
        base_headers["authorization"] = auth["authorization"]
        base_headers["xi-csrf-token"] = auth.get("xi-csrf-token", "")
        base_headers["x-appid"] = auth.get("x-appid", "3")
        
        if auth.get("cookie"):
            base_headers["cookie"] = auth["cookie"]
            
        return base_headers
        
    except Exception as e:
        print(f"❌ 加载配置文件失败: {e}")
        return base_headers


def save_auth_config(config: dict):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    get_headers(force_reload=True)


def update_token():
    """交互式更新 token"""
    print("\n=== 更新 Biji.com 认证 Token ===\n")
    print("步骤:")
    print("1. 在 Chrome 中打开 https://www.biji.com")
    print("2. 确保已登录")
    print("3. F12 打开 DevTools -> Network")
    print("4. 点击任意笔记，找到 knowledge-api.trytalks.com 请求")
    print("5. 复制以下 Request Headers:\n")

    auth = input("authorization (Bearer xxx...): ").strip()
    if not auth.startswith("Bearer "):
        auth = "Bearer " + auth

    csrf = input("xi-csrf-token: ").strip()
    appid = input("x-appid (默认 3): ").strip() or "3"

    config = {
        "authorization": auth,
        "xi-csrf-token": csrf,
        "x-appid": appid,
    }

    save_auth_config(config)

    print(f"\n✅ Token 已保存到: {CONFIG_PATH}")

    print("\n测试连接...")
    headers = get_headers(force_reload=True)
    try:
        response = requests.post(
            "https://knowledge-api.trytalks.com/v1/web/follow/account/posts",
            headers=headers,
            json={"topic_id": -1, "follow_id": 1, "page": 1, "page_size": 1},
            timeout=10,
        )
        if response.status_code == 200:
            print("✅ 认证有效!")
        else:
            print(f"⚠️  认证可能无效 (HTTP {response.status_code})")
    except Exception as e:
        print(f"⚠️  连接测试失败: {e}")


# 全局 HEADERS，延迟加载
HEADERS = None

def get_headers(force_reload: bool = False):
    global HEADERS
    if HEADERS is None or force_reload:
        HEADERS = load_headers()
    return HEADERS


def parse_biji_url(url: str) -> dict:
    """从 URL 解析 followId, followName, topic_id_alias"""
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    
    follow_id = query.get("followId", [None])[0]
    follow_name = query.get("followName", [None])[0]
    
    if follow_name:
        follow_name = unquote(follow_name)
    
    path_match = re.search(r'/subject/([^/]+)', parsed.path)
    topic_id_alias = path_match.group(1) if path_match else None
    
    return {
        "follow_id": int(follow_id) if follow_id else None,
        "follow_name": follow_name,
        "topic_id_alias": topic_id_alias
    }


def get_topic_id(topic_id_alias: str, follow_id: int) -> int:
    """通过 follow_id 获取 topic_id"""
    url = "https://knowledge-api.trytalks.com/v1/web/follow/account/posts"
    payload = {
        "topic_id": -1,
        "follow_id": follow_id,
        "page": 1,
        "page_size": 1
    }
    
    try:
        response = requests.post(url, headers=get_headers(), json=payload)
        response.raise_for_status()
        data = response.json()
        posts = data.get("c", {}).get("posts", [])
        if posts:
            return posts[0].get("topic_id", -1)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            print("❌ 认证失败 (403 Forbidden)")
            print("   请运行: python scripts/biji_export.py --update-token")
        else:
            print(f"获取 topic_id 失败: {e}")
    except Exception as e:
        print(f"获取 topic_id 失败: {e}")
    
    return -1


def fetch_post_list(topic_id: int, follow_id: int) -> list:
    """获取所有笔记列表"""
    print("获取笔记列表...")
    all_posts = []
    page = 1
    page_size = 20
    
    while True:
        url = "https://knowledge-api.trytalks.com/v1/web/follow/account/posts"
        payload = {
            "topic_id": topic_id,
            "follow_id": follow_id,
            "page": page,
            "page_size": page_size
        }
        
        try:
            response = requests.post(url, headers=get_headers(), json=payload)
            response.raise_for_status()
            data = response.json()
            
            posts = data.get("c", {}).get("posts", [])
            if not posts:
                print(f"  第 {page} 页: 无更多数据")
                break
                
            print(f"  第 {page} 页: 找到 {len(posts)} 条笔记")
            all_posts.extend(posts)
            
            if len(posts) < page_size:
                print(f"  第 {page} 页: 已到达列表末尾")
                break
                
            page += 1
            time.sleep(0.5)
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                print("❌ 认证失败，请刷新 token")
            else:
                print(f"获取第 {page} 页失败: {e}")
            break
        except Exception as e:
            print(f"获取第 {page} 页失败: {e}")
            break
            
    print(f"共找到 {len(all_posts)} 条笔记")
    return all_posts


def fetch_post_detail(post_id, topic_id_alias: str):
    """获取单条笔记详情"""
    url = "https://knowledge-api.trytalks.com/v1/web/topic/post/detail"
    payload = {
        "topic_id": -1,
        "topic_id_alias": topic_id_alias,
        "post_id": str(post_id),
        "load_media_text": True
    }
    
    try:
        response = requests.post(url, headers=get_headers(), json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("c", {})
    except Exception as e:
        print(f"获取笔记详情失败 {post_id}: {e}")
        return None


def export_to_markdown(full_data: list, author_name: str, output_dir: Path) -> str:
    """导出为 Markdown 文件"""
    output_dir.mkdir(parents=True, exist_ok=True)
    md_path = output_dir / f"{author_name}_完整导出_{datetime.now().strftime('%Y%m%d')}.md"
    timestamp_str = datetime.now().strftime("%Y-%m-%d")
    
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# {author_name} 笔记导出\n\n")
        f.write(f"导出时间: {timestamp_str}\n")
        f.write(f"总计笔记数: {len(full_data)}\n\n")
        f.write("---\n\n")
        
        for post in full_data:
            title = post.get("post_title", "无标题") or post.get("post_name", "无标题")
            publish_ts = post.get("post_publish_time", 0)
            if publish_ts:
                publish_date = datetime.fromtimestamp(int(publish_ts)).strftime("%Y-%m-%d %H:%M:%S")
            else:
                publish_date = "未知日期"
                
            original_url = post.get("post_url", "")
            content = post.get("post_media_text", "") or post.get("post_summary", "")
            
            f.write(f"## {title}\n\n")
            f.write(f"**发布时间**: {publish_date}\n\n")
            if original_url:
                f.write(f"**原链接**: [{original_url}]({original_url})\n\n")
            
            f.write(f"{content}\n\n")
            f.write("---\n\n")
            
    return str(md_path)


def export_notes(url: str, topic_id_override: int = None, output_dir: str | Path | None = None):
    """从博主页面 URL 导出笔记"""
    print(f"解析 URL: {url}")

    params = parse_biji_url(url)
    follow_id = params["follow_id"]
    author_name = params["follow_name"]
    topic_id_alias = params["topic_id_alias"]

    if not follow_id or not author_name:
        raise ExportError("URL 缺少 followId 或 followName 参数")

    return export_notes_core(
        follow_id,
        author_name,
        topic_id_alias,
        topic_id_override=topic_id_override,
        output_dir=output_dir,
    )


def export_notes_core(
    follow_id: int,
    author_name: str,
    topic_id_alias: str,
    topic_id_override: int = None,
    output_dir: str | Path | None = None,
):
    """导出笔记主流程"""
    target_output_dir = Path(output_dir).expanduser() if output_dir else OUTPUT_DIR
    target_output_dir.mkdir(parents=True, exist_ok=True)

    print(f"博主: {author_name}")
    print(f"Follow ID: {follow_id}")
    print(f"Topic Alias: {topic_id_alias}")

    if topic_id_override:
        topic_id = topic_id_override
        print(f"使用手动指定 Topic ID: {topic_id}")
    else:
        topic_id = get_topic_id(topic_id_alias, follow_id)

    if topic_id == -1:
        raise ExportError(
            "无法获取 topic_id，请尝试手动指定 --topic-id。\n"
            "获取方式：F12 打开网络面板 → 刷新博主主页 → 找到 posts 请求 → 查看 Payload 中的 topic_id"
        )
    print(f"Topic ID: {topic_id}")

    posts = fetch_post_list(topic_id, follow_id)

    if not posts:
        raise ExportError("未找到笔记")

    full_data = []
    print("获取笔记详情...")
    for i, post in enumerate(posts):
        post_id = post.get("post_id")
        title = post.get("post_title", "Untitled") or post.get("post_name", "Untitled")
        print(f"[{i+1}/{len(posts)}] 获取: {title[:50]}...")

        detail = fetch_post_detail(post_id, topic_id_alias)
        if detail:
            full_data.append(detail)
        else:
            full_data.append(post)

        time.sleep(0.5)

    json_path = target_output_dir / f"{author_name}_full_data.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(full_data, f, ensure_ascii=False, indent=2)
    print(f"JSON 已保存: {json_path}")

    md_path = export_to_markdown(full_data, author_name, target_output_dir)
    print(f"Markdown 已保存: {md_path}")

    print(f"\n✅ 导出完成! 共 {len(full_data)} 条笔记")
    return {
        "author_name": author_name,
        "count": len(full_data),
        "json_path": str(json_path),
        "markdown_path": str(md_path),
        "topic_id": topic_id,
        "output_dir": str(target_output_dir),
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Biji.com 笔记导出")
    parser.add_argument("url", nargs="?", help="博主主页 URL")
    parser.add_argument("--update-token", "-u", action="store_true", help="交互式更新 Token")
    parser.add_argument("--topic-id", type=int, help="手动指定 Topic ID (如果自动获取失败)")

    args = parser.parse_args()

    if args.update_token:
        update_token()
        return

    if not args.url:
        parser.print_help()
        sys.exit(1)

    try:
        export_notes(args.url, topic_id_override=args.topic_id)
    except ExportError as exc:
        print(f"❌ {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
