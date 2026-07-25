import json

import pytest

from scripts import biji_cli, biji_export, skill_installer


def run_cli(argv, capsys):
    """执行 biji_cli.main() 并返回 (stdout 解析后的 JSON, SystemExit code 或 None)"""
    code = None
    try:
        biji_cli.main()
    except SystemExit as e:
        code = e.code
    parsed = json.loads(capsys.readouterr().out)
    return parsed, code


def test_topics_outputs_json(monkeypatch, capsys):
    monkeypatch.setattr(__import__("sys"), "argv", ["biji_cli", "topics"])
    monkeypatch.setattr(
        biji_export,
        "list_topics",
        lambda: [{"id_alias": "abc", "name": "测试库", "count": 3, "source": "mine"}],
    )

    data, code = run_cli(["biji_cli", "topics"], capsys)
    assert code is None
    assert data == {"topics": [{"id_alias": "abc", "name": "测试库", "count": 3, "source": "mine"}]}


def test_follows_outputs_json(monkeypatch, capsys):
    monkeypatch.setattr(__import__("sys"), "argv", ["biji_cli", "follows", "abc"])
    monkeypatch.setattr(
        biji_export,
        "list_follows",
        lambda alias: [{"follow_id": 1, "name": "博主", "topic_id": 2, "note_count": 5, "platform": "DOUYIN"}],
    )

    data, code = run_cli(None, capsys)
    assert code is None
    assert data["follows"][0]["follow_id"] == 1


def test_auth_error_exit_code_2(monkeypatch, capsys):
    monkeypatch.setattr(__import__("sys"), "argv", ["biji_cli", "topics"])

    def raise_auth():
        raise biji_export.AuthError("Token 已过期，请重新获取")

    monkeypatch.setattr(biji_export, "list_topics", raise_auth)

    data, code = run_cli(None, capsys)
    assert code == 2
    assert "LoginRequired" in data["error"]


def test_export_writes_progress_to_stderr(monkeypatch, capsys):
    monkeypatch.setattr(
        __import__("sys"),
        "argv",
        ["biji_cli", "export", "--follow-id", "1", "--name", "博主", "--alias", "abc"],
    )

    def fake_export_core(follow_id, name, alias, topic_id_override=None, output_dir=None, progress=None):
        print("进度日志不应出现在 stdout")
        return {"author_name": name, "count": 1, "json_path": "j", "markdown_path": "m",
                "topic_id": 2, "output_dir": "d"}

    monkeypatch.setattr(biji_export, "export_notes_core", fake_export_core)

    data, code = run_cli(None, capsys)
    assert code is None
    assert data["author_name"] == "博主"
    assert data["markdown_path"] == "m"


def test_install_skill_passes_agent_and_directory(monkeypatch, capsys, tmp_path):
    custom_dir = tmp_path / "agent-skills"
    expected = custom_dir / "getbijiex" / "SKILL.md"
    called = {}

    def fake_install_skill(agent="claude", target_dir=None):
        called.update(agent=agent, target_dir=target_dir)
        return expected

    monkeypatch.setattr(
        __import__("sys"),
        "argv",
        [
            "biji_cli",
            "install-skill",
            "--agent",
            "codex",
            "--dir",
            str(custom_dir),
        ],
    )
    monkeypatch.setattr(skill_installer, "install_skill", fake_install_skill)

    data, code = run_cli(None, capsys)

    assert code is None
    assert called == {"agent": "codex", "target_dir": str(custom_dir)}
    assert data == {"ok": True, "skill_path": str(expected)}
