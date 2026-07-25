"""
把 GetbijiEx 的 Skill 安装到 Claude Code、Codex 或自定义 Agent 目录。

模板在仓库 skill/SKILL.md，其中的 {{CLI_COMMAND}} 会被替换为
当前环境的真实调用方式：
- 打包版：app 可执行文件的绝对路径
- 源码版：uv run python scripts/biji_cli.py
"""
import shlex
import sys
from pathlib import Path

from scripts.app_paths import is_frozen, project_root, resources_root

SKILL_NAME = "getbijiex"

# 各 Agent 的 Skill 安装根目录（相对 home）
AGENT_SKILL_DIRS = {
    "claude": ".claude/skills",
    "codex": ".codex/skills",
}


class UnsupportedAgentError(ValueError):
    pass


def cli_command() -> str:
    if is_frozen():
        return shlex.quote(str(Path(sys.executable).resolve()))
    root = project_root()
    return f"cd {shlex.quote(str(root))} && uv run python scripts/biji_cli.py"


def skill_target(agent: str = "claude", target_dir: str | None = None) -> Path:
    if target_dir:
        base = Path(target_dir).expanduser()
    else:
        try:
            base = Path.home() / AGENT_SKILL_DIRS[agent]
        except KeyError as exc:
            supported = "、".join(AGENT_SKILL_DIRS)
            raise UnsupportedAgentError(
                f"不支持的 Agent：{agent}。支持：{supported}；其他 Agent 请使用 --dir。"
            ) from exc
    return base / SKILL_NAME / "SKILL.md"


def install_skill(agent: str = "claude", target_dir: str | None = None) -> Path:
    template_path = resources_root() / "skill" / "SKILL.md"
    template = template_path.read_text(encoding="utf-8")
    target = skill_target(agent, target_dir)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(template.replace("{{CLI_COMMAND}}", cli_command()), encoding="utf-8")
    return target
