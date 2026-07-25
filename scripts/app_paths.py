from pathlib import Path
import os
import sys


APP_NAME = "Biji导出小工具"


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


def user_data_root() -> Path:
    """应用数据目录（跨平台）"""
    if sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support" / "BijiExportApp"
    elif sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        root = Path(base) / "BijiExportApp"
    else:
        root = Path.home() / ".local" / "share" / "BijiExportApp"
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
