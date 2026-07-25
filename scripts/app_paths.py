from pathlib import Path
import os
import sys


APP_NAME = "GetbijiEx"
OLD_APP_DIR_NAME = "BijiExportApp"  # 旧版数据目录名，用于迁移


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def project_root() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def resources_root() -> Path:
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", project_root()))
    return project_root()


def _data_base() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support"
    if sys.platform.startswith("win"):
        return Path(os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming"))
    return Path.home() / ".local" / "share"


def user_data_root() -> Path:
    """应用数据目录（跨平台）。旧版 BijiExportApp 目录自动迁移为 GetbijiEx。"""
    base = _data_base()
    root = base / APP_NAME
    old = base / OLD_APP_DIR_NAME
    if not root.exists() and old.exists():
        try:
            old.rename(root)
        except OSError:
            pass  # 迁移失败就用新目录重新开始，不阻塞启动
    root.mkdir(parents=True, exist_ok=True)
    return root


def config_dir() -> Path:
    path = user_data_root() / "config"
    path.mkdir(parents=True, exist_ok=True)
    return path


def output_dir() -> Path:
    path = user_data_root() / "data" / "biji_export"
    path.mkdir(parents=True, exist_ok=True)
    return path


def logs_dir() -> Path:
    path = user_data_root() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def helper_script_path() -> Path:
    return resources_root() / "scripts" / "refresh_token_browser.py"
