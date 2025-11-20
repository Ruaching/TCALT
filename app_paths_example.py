import os
from pathlib import Path
from platform import system

APP_NAME = "app"
HOME = Path.home()
CURRENT_OS = system()

def config_path(filename: str = "some_file.json") -> Path:
    cfg_dir: Path = user_config_dir()
    return cfg_dir/filename

def dev_path() -> Path:
    return Path(__file__).parent.resolve()

def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path

def find_desktop() -> Path:
    onedrive = os.environ.get("OneDrive")
    if onedrive:
        path: Path = Path(onedrive)/'Desktop'
    else:
        path: Path = HOME/'Desktop'
    return path

def user_config_dir() -> Path:
    "Finds and sets application config folders in APPDATA (Windows) or Application Support (MacOS)"
    return HOME