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


def test_install_skill_supports_custom_directory(monkeypatch, tmp_path):
    resource_root = tmp_path / "resources"
    template_dir = resource_root / "skill"
    template_dir.mkdir(parents=True)
    (template_dir / "SKILL.md").write_text(
        "name: getbijiex\n{{CLI_COMMAND}}\n",
        encoding="utf-8",
    )
    custom_root = tmp_path / "other-agent" / "skills"
    monkeypatch.setattr(skill_installer, "resources_root", lambda: resource_root)
    monkeypatch.setattr(skill_installer, "cli_command", lambda: "GetbijiEx topics")

    target = skill_installer.install_skill(target_dir=str(custom_root))

    assert target == custom_root / "getbijiex" / "SKILL.md"
    assert target.read_text(encoding="utf-8") == "name: getbijiex\nGetbijiEx topics\n"


def test_unknown_agent_requires_custom_directory():
    with pytest.raises(skill_installer.UnsupportedAgentError, match="--dir"):
        skill_installer.skill_target("other")
