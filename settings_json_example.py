import json
from pathlib import Path
from typing import Dict, Any, Literal

from app_paths import config_path, find_desktop

DEFAULTS: Dict[str, Any] = {
    "username": "",
    "remember_me": False,
    "animation": False,
    "default_tool": "",
    "desktop_path": "",
    "config_path": "",
    "paths": []
}

def _dynamic_defaults() -> Dict[str, str]:
    return {
        **DEFAULTS,
        "desktop_path": str(find_desktop()),
        "config_path": str(config_path())
    }

def load_config() -> Dict[str, Any]:
    p: Path = config_path()
    if not p.exists():
        dyn = _dynamic_defaults()
        save_config(dyn)
        return dyn.copy()

    try:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                data = {}
    except Exception:
        data = {}

    dyn = _dynamic_defaults()
    merged = {**dyn, **{key: value for key, value in data.items() if key in dyn}}
    return merged

def save_config(cfg: Dict[str, Any]) -> None:
    p: Path = config_path()
    with p.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

def animation_config(value: bool) -> None:
    cfg = load_config()
    cfg["animation"] = bool(value)
    save_config(cfg)

def load_animation() -> bool:
    cfg = load_config()
    return cfg["animation"]

def remember_user(username: str, remember: bool) -> None:
    cfg = load_config()
    cfg["username"] = username if remember else ""
    cfg["remember_me"] = bool(remember)
    save_config(cfg)

def remembered_user() -> str:
    cfg = load_config()
    return cfg["username"] if cfg.get("remember_me") else ""

def add_path(path: str) -> None:
    cfg = load_config()
    if path not in cfg["paths"]:
        cfg["paths"].append(path)
    save_config(cfg)

def remove_path(path: str) -> None:
    cfg = load_config()
    if "paths" in cfg and path in cfg["paths"]:
        cfg["paths"].remove(path)
    save_config(cfg)

def default_tool(mode: Literal['clear', 'load', 'save'], tool: str = "") -> str | None:
    """
    Use 'save' to save tool as default\n
    Use 'load' to load default tool\n
    Use 'clear' to clear default tool
    """
    cfg = load_config()
    if mode == 'save':
        if 'default_tool' not in cfg:
            cfg['default_tool'] = ""
        if tool != "" and tool not in cfg["default_tool"]:
            cfg['default_tool'] = str(tool)
            save_config(cfg)
    elif mode == 'load':
        default = cfg.get('default_tool') or ""
        return default
    elif mode == 'clear':
        cfg['default_tool'] = ""
        save_config(cfg)
