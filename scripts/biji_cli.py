"""
GetbijiEx 的 Agent 友好 CLI。

所有子命令把结构化结果以 JSON 打印到 stdout，过程日志走 stderr，
方便 Agent 解析。打包后的 app 带参数调用时走的就是这个入口。

用法:
  GetbijiEx topics                        # 知识库列表
  GetbijiEx follows <topic_id_alias>      # 知识库内博主列表
  GetbijiEx export --follow-id N --name X --alias Y [--topic-id N] [--output-dir D]
  GetbijiEx export-url <URL> [--topic-id N] [--output-dir D]
  GetbijiEx token                         # 刷新 Token（弹浏览器）
  GetbijiEx install-skill [--agent claude|codex] [--dir D]
"""
import argparse
import contextlib
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import auto_token, biji_export


def _out(obj: dict) -> None:
    print(json.dumps(obj, ensure_ascii=False))


def _fail(message: str, code: int = 1) -> None:
    _out({"error": message})
    sys.exit(code)


def main():
    parser = argparse.ArgumentParser(description="GetbijiEx CLI（输出 JSON）")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("topics", help="列出知识库")

    p_follows = sub.add_parser("follows", help="列出知识库内博主")
    p_follows.add_argument("alias", help="topic_id_alias")

    p_export = sub.add_parser("export", help="按 follow_id 导出博主笔记")
    p_export.add_argument("--follow-id", type=int, required=True)
    p_export.add_argument("--name", required=True, help="博主名")
    p_export.add_argument("--alias", required=True, help="topic_id_alias")
    p_export.add_argument("--topic-id", type=int, default=None)
    p_export.add_argument("--output-dir", default=None)

    p_export_url = sub.add_parser("export-url", help="按博主页面 URL 导出")
    p_export_url.add_argument("url")
    p_export_url.add_argument("--topic-id", type=int, default=None)
    p_export_url.add_argument("--output-dir", default=None)

    sub.add_parser("token", help="刷新 Token（会弹出浏览器）")

    p_install = sub.add_parser("install-skill", help="把 Agent Skill 安装到本机")
    p_install.add_argument(
        "--agent",
        default="claude",
        choices=["claude", "codex"],
        help="目标 Agent（默认 claude）",
    )
    p_install.add_argument(
        "--dir",
        default=None,
        help="自定义 Skill 安装目录（其他 Agent 用这个，直接指定目录）",
    )

    args = parser.parse_args()

    try:
        if args.command == "topics":
            _out({"topics": biji_export.list_topics()})

        elif args.command == "follows":
            _out({"follows": biji_export.list_follows(args.alias)})

        elif args.command == "export":
            # 导出过程 print 很多进度，全部赶到 stderr，保证 stdout 只有 JSON
            with contextlib.redirect_stdout(sys.stderr):
                result = biji_export.export_notes_core(
                    args.follow_id,
                    args.name,
                    args.alias,
                    topic_id_override=args.topic_id,
                    output_dir=args.output_dir,
                )
            _out(result)

        elif args.command == "export-url":
            with contextlib.redirect_stdout(sys.stderr):
                result = biji_export.export_notes(
                    args.url,
                    topic_id_override=args.topic_id,
                    output_dir=args.output_dir,
                )
            _out(result)

        elif args.command == "token":
            auto_token.capture_token(log=lambda m: print(m, file=sys.stderr))
            _out({"ok": True})

        elif args.command == "install-skill":
            from scripts import skill_installer
            target = skill_installer.install_skill(agent=args.agent, target_dir=args.dir)
            _out({"ok": True, "skill_path": str(target)})

    except biji_export.AuthError:
        _fail("LoginRequired: Token 已过期，请先运行 token 子命令刷新", code=2)
    except auto_token.CaptureCancelled:
        _fail("CaptureCancelled: 用户关闭了浏览器窗口", code=3)
    except Exception as exc:
        _fail(f"{type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
