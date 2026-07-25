from pathlib import Path

import pytest

from scripts import skill_installer


def test_skill_target_defaults_to_claude(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    target = skill_installer.skill_target()

    assert target == tmp_path / ".claude" / "skills" / "getbijiex" / "SKILL.md"


def test_skill_target_supports_codex(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    target = skill_installer.skill_target("codex")

    assert target == tmp_path / ".codex" / "skills" / "getbijiex" / "SKILL.md"


def make_skill_resources(tmp_path, template=None):
    resource_root = tmp_path / "resources"
    template_dir = resource_root / "skills" / "getbijiex"
    scripts_dir = template_dir / "scripts"
    scripts_dir.mkdir(parents=True)
    if template is None:
        template = (
            "name: getbijiex\n"
            f"{skill_installer.COMMAND_START}\n"
            "node launcher.mjs\n"
            f"{skill_installer.COMMAND_END}\n"
        )
    (template_dir / "SKILL.md").write_text(template, encoding="utf-8")
    (scripts_dir / "getbijiex-cli.mjs").write_text("// launcher\n", encoding="utf-8")
    return resource_root


def test_install_skill_copies_resources_and_renders_command(monkeypatch, tmp_path):
    resource_root = make_skill_resources(tmp_path)
    custom_root = tmp_path / "other-agent" / "skills"
    monkeypatch.setattr(skill_installer, "resources_root", lambda: resource_root)
    monkeypatch.setattr(skill_installer, "cli_command", lambda: "GetbijiEx topics")

    target = skill_installer.install_skill(target_dir=str(custom_root))

    assert target == custom_root / "getbijiex" / "SKILL.md"
    text = target.read_text(encoding="utf-8")
    assert "GetbijiEx topics" in text
    assert "node launcher.mjs" not in text
    assert "{{CLI_COMMAND}}" not in text
    assert (target.parent / "scripts" / "getbijiex-cli.mjs").read_text(
        encoding="utf-8"
    ) == "// launcher\n"


def test_install_skill_is_idempotent(monkeypatch, tmp_path):
    resource_root = make_skill_resources(tmp_path)
    custom_root = tmp_path / "agent-skills"
    monkeypatch.setattr(skill_installer, "resources_root", lambda: resource_root)
    commands = iter(["first-command", "second-command"])
    monkeypatch.setattr(skill_installer, "cli_command", lambda: next(commands))

    target = skill_installer.install_skill(target_dir=str(custom_root))
    (target.parent / "obsolete.txt").write_text("old", encoding="utf-8")
    target = skill_installer.install_skill(target_dir=str(custom_root))

    text = target.read_text(encoding="utf-8")
    assert "second-command" in text
    assert "first-command" not in text
    assert not (target.parent / "obsolete.txt").exists()


@pytest.mark.parametrize(
    "template",
    [
        "name: getbijiex\n",
        (
            f"{skill_installer.COMMAND_START}\n{skill_installer.COMMAND_END}\n"
            f"{skill_installer.COMMAND_START}\n{skill_installer.COMMAND_END}\n"
        ),
    ],
)
def test_install_skill_rejects_invalid_command_markers(monkeypatch, tmp_path, template):
    resource_root = make_skill_resources(tmp_path, template=template)
    monkeypatch.setattr(skill_installer, "resources_root", lambda: resource_root)

    with pytest.raises(skill_installer.SkillTemplateError, match="命令标记"):
        skill_installer.install_skill(target_dir=str(tmp_path / "skills"))


def test_cli_command_quotes_posix_source_path(monkeypatch, tmp_path):
    root = tmp_path / "源码 path's"
    monkeypatch.setattr(skill_installer, "is_frozen", lambda: False)
    monkeypatch.setattr(skill_installer, "project_root", lambda: root)

    command = skill_installer.cli_command(platform="darwin")

    assert command.startswith("uv --directory ")
    assert "scripts/biji_cli.py" in command
    assert "'\"'\"'" in command


def test_cli_command_quotes_windows_source_path(monkeypatch, tmp_path):
    root = tmp_path / "Source path's"
    monkeypatch.setattr(skill_installer, "is_frozen", lambda: False)
    monkeypatch.setattr(skill_installer, "project_root", lambda: root)

    command = skill_installer.cli_command(platform="win32")

    assert command == (
        f"uv --directory '{str(root.resolve()).replace(chr(39), chr(39) * 2)}' "
        "run python scripts/biji_cli.py"
    )


def test_cli_command_uses_powershell_call_operator_for_frozen_windows(monkeypatch):
    monkeypatch.setattr(skill_installer, "is_frozen", lambda: True)
    monkeypatch.setattr(skill_installer.sys, "executable", "C:/Program Files/GetbijiEx/GetbijiEx.exe")

    command = skill_installer.cli_command(platform="win32")

    assert command.startswith("& '")
    assert "GetbijiEx.exe" in command


def test_render_direct_command_marks_windows_as_powershell():
    template = (
        f"{skill_installer.COMMAND_START}\n"
        "old command\n"
        f"{skill_installer.COMMAND_END}\n"
    )

    rendered = skill_installer._render_direct_command(
        template,
        "& 'C:\\Program Files\\GetbijiEx\\GetbijiEx.exe'",
        platform="win32",
    )

    assert "请在 PowerShell 中执行" in rendered
    assert "```powershell" in rendered
    assert "```bash" not in rendered


def test_render_direct_command_marks_posix_as_bash():
    template = (
        f"{skill_installer.COMMAND_START}\n"
        "old command\n"
        f"{skill_installer.COMMAND_END}\n"
    )

    rendered = skill_installer._render_direct_command(
        template,
        "'/Applications/GetbijiEx.app/Contents/MacOS/GetbijiEx'",
        platform="darwin",
    )

    assert "请在 Bash 兼容终端中执行" in rendered
    assert "```bash" in rendered


def test_unknown_agent_requires_custom_directory():
    with pytest.raises(skill_installer.UnsupportedAgentError, match="--dir"):
        skill_installer.skill_target("other")
