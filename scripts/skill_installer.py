"""把 GetbijiEx Skill 安装到 Claude Code、Codex 或自定义 Agent 目录。"""

import os
import shlex
import shutil
import sys
from pathlib import Path

from scripts.app_paths import is_frozen, project_root, resources_root

SKILL_NAME = "getbijiex"
COMMAND_START = "<!-- GETBIJIEX_CLI_COMMAND_START -->"
COMMAND_END = "<!-- GETBIJIEX_CLI_COMMAND_END -->"

# 各 Agent 的 Skill 安装根目录（相对 home）
AGENT_SKILL_DIRS = {
    "claude": ".claude/skills",
    "codex": ".codex/skills",
}


class UnsupportedAgentError(ValueError):
    pass


class SkillTemplateError(ValueError):
    pass


def _powershell_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def cli_command(platform: str | None = None) -> str:
    platform = platform or sys.platform
    if is_frozen():
        executable = str(Path(sys.executable).resolve())
        if platform.startswith("win"):
            return f"& {_powershell_quote(executable)}"
        return shlex.quote(executable)

    root = str(project_root().resolve())
    if platform.startswith("win"):
        return f"uv --directory {_powershell_quote(root)} run python scripts/biji_cli.py"
    return f"uv --directory {shlex.quote(root)} run python scripts/biji_cli.py"


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


def _render_direct_command(
    template: str,
    command: str,
    platform: str | None = None,
) -> str:
    if template.count(COMMAND_START) != 1 or template.count(COMMAND_END) != 1:
        raise SkillTemplateError("Skill 模板必须包含且只包含一组 CLI 命令标记。")
    platform = platform or sys.platform
    shell_description = (
        "PowerShell 中" if platform.startswith("win") else "Bash 兼容终端中"
    )
    code_fence = "powershell" if platform.startswith("win") else "bash"
    start = template.index(COMMAND_START)
    end = template.index(COMMAND_END, start) + len(COMMAND_END)
    replacement = (
        f"{COMMAND_START}\n"
        "以下命令前缀由 GetbijiEx 安装器生成，后文统称为 `CLI`。"
        f"请在 {shell_description}执行：\n\n"
        f"```{code_fence}\n"
        f"{command}\n"
        "```\n"
        f"{COMMAND_END}"
    )
    return template[:start] + replacement + template[end:]


def install_skill(agent: str = "claude", target_dir: str | None = None) -> Path:
    source = resources_root() / "skills" / SKILL_NAME
    template_path = source / "SKILL.md"
    template = template_path.read_text(encoding="utf-8")
    rendered = _render_direct_command(template, cli_command(), sys.platform)

    target = skill_target(agent, target_dir)
    destination = target.parent
    destination.parent.mkdir(parents=True, exist_ok=True)

    temporary = destination.with_name(f".{destination.name}.tmp-{os.getpid()}")
    if temporary.exists():
        shutil.rmtree(temporary)
    shutil.copytree(source, temporary)
    (temporary / "SKILL.md").write_text(rendered, encoding="utf-8")

    if destination.exists():
        shutil.rmtree(destination)
    temporary.replace(destination)
    return target
