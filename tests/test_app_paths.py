from scripts import app_paths


def test_user_data_root_migrates_legacy_directory(monkeypatch, tmp_path):
    old_root = tmp_path / app_paths.OLD_APP_DIR_NAME
    old_root.mkdir()
    (old_root / "keep.txt").write_text("登录数据", encoding="utf-8")
    monkeypatch.setattr(app_paths, "_data_base", lambda: tmp_path)

    root = app_paths.user_data_root()

    assert root == tmp_path / app_paths.APP_NAME
    assert not old_root.exists()
    assert (root / "keep.txt").read_text(encoding="utf-8") == "登录数据"


def test_user_data_root_keeps_legacy_directory_when_new_exists(monkeypatch, tmp_path):
    old_root = tmp_path / app_paths.OLD_APP_DIR_NAME
    new_root = tmp_path / app_paths.APP_NAME
    old_root.mkdir()
    new_root.mkdir()
    (old_root / "old.txt").write_text("旧数据", encoding="utf-8")
    (new_root / "new.txt").write_text("新数据", encoding="utf-8")
    monkeypatch.setattr(app_paths, "_data_base", lambda: tmp_path)

    root = app_paths.user_data_root()

    assert root == new_root
    assert old_root.exists()
    assert (new_root / "new.txt").read_text(encoding="utf-8") == "新数据"
