import sys
import customtkinter as ctk

from PIL import Image
from platform import system
from tkinter import messagebox

from helper_functions import _center_window, _resource_path, _safe_destroy, _set_icon
from log_params import Logs

Logs()
CurrentOS = system()

if CurrentOS not in ('Windows', 'Darwin'):
    root = ctk.CTk()
    root.withdraw()
    messagebox.showerror("Unsupported OS", "TCALT is not supported in your current OS.")
    sys.exit(1)
elif CurrentOS == 'Windows':
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(2)

def _start_main(win) -> None:
    _safe_destroy(win)
    import main

def show_splash() -> None:
    splash = ctk.CTk()
    ctk.set_appearance_mode('dark')
    splash.overrideredirect(True)
    splash.title('TCALT Splash')
    _set_icon(CurrentOS, splash)
    _center_window(splash, 350, 100)
    splash.configure(fg_color="#000000")

    logo_path = _resource_path('path', 'to_image.png')
    img = Image.open(logo_path)
    img.thumbnail((300, 100))
    logo = ctk.CTkImage(dark_image=img, size=img.size)

    label = ctk.CTkLabel(splash, image=logo, text="Loading...", font=('Georgia', 15), compound="top")
    label.pack(expand=True)
    splash.after(2250, lambda: _start_main(splash))
    splash.mainloop()
show_splash()