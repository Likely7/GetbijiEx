"""
把本工具的 Agent Skill 安装到 ~/.claude/skills/biji-export/SKILL.md。

模板在仓库 skill/SKILL.md，其中的 {{CLI_COMMAND}} 会被替换为
当前环境的真实调用方式：
- 打包版：app 可执行文件的绝对路径
- 源码版：uv run python scripts/biji_cli.py
"""
import shlex
import sys
from pathlib import Path

from scripts.app_paths import is_frozen, project_root, resources_root

SKILL_NAME = "biji-export"


def cli_command() -> str:
    if is_frozen():
        return shlex.quote(str(Path(sys.executable).resolve()))
    root = project_root()
    return f"cd {shlex.quote(str(root))} && uv run python scripts/biji_cli.py"


def skill_target() -> Path:
    return Path.home() / ".claude" / "skills" / SKILL_NAME / "SKILL.md"


def install_skill() -> Path:
    template_path = resources_root() / "skill" / "SKILL.md"
    template = template_path.read_text(encoding="utf-8")
    target = skill_target()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(template.replace("{{CLI_COMMAND}}", cli_command()), encoding="utf-8")
    return target
