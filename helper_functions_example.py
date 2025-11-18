from pathlib import Path
from typing import TYPE_CHECKING, Literal, Union

from log_params import Logs, logging
log = Logs()

if TYPE_CHECKING:
    import customtkinter as ctk
    from mysql.connector.abstracts import MySQLConnectionAbstract
    from mysql.connector.pooling import PooledMySQLConnection

    DatabaseConnection = Union[MySQLConnectionAbstract, PooledMySQLConnection]

def _browse_file() -> 'Path':
    """Opens a file dialog for user to select a file to be uploaded."""
    from tkinter import filedialog
    file_path = filedialog.askopenfilename(
        title="Select a CSV file",
        filetypes=[("Desc", "file_type")]
    )
    if file_path:
        logging.info(f"File {file_path} successfully loaded.")
        return Path(file_path).resolve()
    else:
        logging.warning("No file was selected. Please select a file to continue.")
        raise FileNotFoundError

def _center_window(win: 'ctk.CTk', width: int, height: int) -> None:
    """Finds center of screen and sets customtkinter geometry."""
    screen_w = win.winfo_screenwidth()
    screen_h = win.winfo_screenheight()
    x = int((screen_w / 2) - (width / 2))
    y = int((screen_h / 2) - (height / 2))
    win.geometry(f"{width}x{height}+{x}+{y}")

def _count_instances(process_name) -> int:
    """Checks if the app is already running."""
    import psutil
    count = 0

    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == process_name:
            count += 1
    return count

def _current_time(lookup: Literal['date', 'full', 'time'] | None = None) -> str:
    import time
    if lookup == "date":
        return time.strftime("%Y-%m-%d")
    elif lookup == 'full':
        return time.strftime("%Y-%m-%d %H:%M %Z")
    elif lookup == "time":
        return time.strftime("%H:%M")
    elif not lookup:
        return time.strftime("%Y-%m-%d %H:%M")

def _fetch_all(cursor, query:str, *params: str) -> list[dict[str, object]]:
    cursor.execute(query, params)
    rows = cursor.fetchall()
    return rows

def _fetch_one(cursor, query: str, *params: str) -> str:
    cursor.execute(query, params)
    row = cursor.fetchone()
    return row[0]

def _focus_in(var: 'ctk.StringVar', entry: 'ctk.CTkEntry', placeholder: str) -> None:
    """Removes a placeholder text in a CTkEntry widget when inactive.\n
    Use lambda i:"""
    if entry.get() == placeholder:
        entry.configure(text_color="#DCE4EE")
        var.set("")

def _focus_out(var: 'ctk.StringVar', entry: 'ctk.CTkEntry', placeholder: str) -> None:
    """Sets a placeholder text in a CTkEntry widget when inactive.\n
    Use lambda i:"""
    if entry.get() == "":
        entry.configure(text_color="#9D9D9D")
        var.set(placeholder)

def _limit_entry(var: 'ctk.StringVar', max_len: int = 30) -> None:
    """Limits the number of characters allowed in a CTkEntry widget.\n
    Use lambda *i:"""
    value = var.get()
    if len(value) > max_len:
        var.set(value[:max_len])

def _open_file(CurrentOS: str, path: str) -> None:
    """Opens a file from given path with the device's default software"""
    import os, subprocess
    if CurrentOS == 'Windows':
        os.startfile(path)
    elif CurrentOS == 'Darwin':
        subprocess.run(["open", path], check=True)

def _resource_path(*parts: str) -> 'Path':
    """Finds files necessary for the operation of the app."""
    import sys
    from pathlib import Path
    _MEIPASS = getattr(sys, "_MEIPASS", None)
    if _MEIPASS:
        base = Path(_MEIPASS)
    else:
        base = Path(__file__).resolve().parent
    return base.joinpath(*parts)

def _safe_destroy(win: 'ctk.CTk') -> None:
    """Safely closes an existing app window."""
    if not win.winfo_exists():
        return
    for widget in win.winfo_children():
        try:
            widget.destroy()
        except Exception as e:
            logging.error(f'Failed removing {widget}: {e}')
    for event_id in win.tk.call('after', 'info'):
        try:
            win.after_cancel(event_id)
        except Exception as e:
            logging.error(f"Failed removing event {event_id}: {e}")  
    try:
        win.destroy()
    except Exception as e:
        logging.error(f'Failed removing window {win}: {e}')

def _set_icon(CurrentOS: str, win: 'ctk.CTk') -> object:
    """Finds and sets icon based on current OS."""
    from tkinter import PhotoImage
    if CurrentOS == 'Windows':
        return win.iconbitmap(_resource_path('path', 'to_image.ico'))
    elif CurrentOS == 'Darwin':
        logo_path = _resource_path('path', 'to_image.gif')
        img = PhotoImage(file=logo_path)
        return win.iconphoto(False, img)

def _typing_effect(label: 'ctk.CTkLabel', full_text: str, delay: int = 9, callback=None) -> None:
    def animate(i=0):
        if i <= len(full_text):
            label.configure(text=full_text[:i])
            label.after(delay, animate, i + 1)
        else:
            if callback:
                callback()
    animate()

def _window_close(database: 'DatabaseConnection', window: 'ctk.CTk') -> None:
    try:
        database.close()
        logging.info('Connection to Database terminated.')
    except Exception as e:
        logging.critical(f"Error closing the app. Please send '.log' to email@domain.com.\nError: {e}")
    _safe_destroy(window)
    log.trim_log()