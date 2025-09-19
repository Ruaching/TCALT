import os
import platform
from pathlib import Path

APP_NAME = "APP NAME"

def user_config_dir() -> Path:
    home = Path.home()

    if platform.system() == "Windows":
        base = Path(os.environ.get("APPDATA") or (home / "AppData" / "Roaming"))
        return base / APP_NAME
    elif platform.system() == "Darwin":
        return home / "Library" / "Application Support" / APP_NAME
    else:
        raise RuntimeError("This tool is not compatible with your OS.")

def ensure_dir(p: Path) -> Path:
    """Example stub: In the real app this would create the folder if missing."""
    return p

def config_path(filename: str = "config.json") -> Path:
    cfg_dir = ensure_dir(user_config_dir())
    return cfg_dir / filename

def find_desktop() -> Path:
    onedrive = os.environ.get("OneDrive")
    if onedrive:
        return Path(onedrive) / "Desktop"
    else:
        return Path.home() / "Desktop"