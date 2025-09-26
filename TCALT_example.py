import ctypes
import os
import platform
import re
import socket
import subprocess
import sys
import threading
import time
import urllib.parse
import webbrowser
from pathlib import Path
from tkinter import filedialog, PhotoImage
from typing import Any, Optional

import customtkinter as ctk
import mysql.connector
import psutil
import requests
from CTkMessagebox import CTkMessagebox
from PIL import Image

from db_params_example import Encryption as db_info
from fe_lookup import FieldEngineer
from log_params import logging, logs
from property_check import create_iif
from secrets_keychain import set_login_password, get_login_password, delete_login_password
from settings_json import remember_user, remembered_user, animation_config, load_animation, default_tool

version: float = 0.0

class AppSwitcher:
    @staticmethod
    def start_app(sw_from: ctk.CTk, mode: str, default: int) -> None:
        if default == 1:
            default_tool('save', mode)
        logging.info(f'Switching to Application on mode {mode}')
        safe_destroy(sw_from)
        Application(mode)
    
    @staticmethod
    def start_menu(sw_from: ctk.CTk) -> None:
        logging.info('Switching to Tool Selector')
        safe_destroy(sw_from)
        main_menu()
    
    @staticmethod
    def start_login(sw_from: ctk.CTk) -> None:
        safe_destroy(sw_from)
        Login()

def Submit(*args):
    global db, admin_access, user

    state = rememberMe.get()
    username = user_inp.get().strip()
    passw = passwo_inp.get().strip()

    if len(passw) < 5:
        lab_sm = ctk.CTkLabel(log, text='Your password is at least 5 characters long. Please try again', font=(font, 10))
        log_err.append(lab_sm)
        lab_sm.place(x=150, y=173, anchor='c')
    else:
        try:
            use_pure = platform.system() != "Windows"
            db = mysql.connector.connect(host=enc.db_info('DB_HOST'),
                                            port=enc.db_info('DB_PORT'),
                                            user=enc.db_info('DB_USER'),
                                            password=enc.db_info('DB_PASSWORD'),
                                            database=enc.db_info('DB_NAME'),
                                            connect_timeout=int(enc.db_info('DB_TIMEOUT')),
                                            ssl_disabled=False,
                                            use_pure=use_pure,
                                            )
        except mysql.connector.ProgrammingError as maxU:
            if "max_user_connections" in str(maxU):
                logging.critical("Too many simultaneous connections to Database. Please try again in 3 minutes.")
                alert = CTkMessagebox(title='Max Users Reached',
                            message='Too many simultaneous connections to Database.\n\nPlease try again in 3 minutes.',
                            font=(font, 13),
                            icon='warning',
                            option_1='Close', option_2='Retry',
                            button_color='#0b7054',
                            button_hover_color='darkgreen')
                
                if alert.get() == 'Retry':
                    Submit()

                if alert.get() == 'Close' or 'None':
                    sys.exit(0)
            else:
                logging.critical(f"There was an error connecting to the database.\nProgramming Error: {maxU}")
                user_inp.place_configure(rely=0.18)
                passwo_inp.place_configure(rely=0.34)
                show_pass.place_configure(rely=0.34)
                rememberMe.place_configure(rely=0.48)
                login_btn.place_configure(rely=0.60)
                programminglab = ctk.CTkLabel(log, text='There was an error connecting to the database.', font=(font, 12), text_color="red")
                log_err.append(programminglab)
                programminglab.place(relx=0.5, rely=0.76, anchor='center')
            raise ConnectionError(maxU)
        except mysql.connector.OperationalError as dbUn:
            if "waiting for initial communication packet" in str(dbUn):
                logging.critical(f"Database is currently unavailable. Please try again later. {dbUn}")
                alert = CTkMessagebox(title='Database Unavailable',
                            message='Database is currently unavailable.',
                            font=(font, 13),
                            icon='warning',
                            option_1='Close App',
                            button_color='#0b7054',
                            button_hover_color='darkgreen')
                
                if alert.get() == 'Close App' or 'None':
                    sys.exit(0)
            else:
                logging.critical(f"There was an error connecting to the database.\nOperational Error: {dbUn}")
                user_inp.place_configure(rely=0.18)
                passwo_inp.place_configure(rely=0.34)
                show_pass.place_configure(rely=0.34)
                rememberMe.place_configure(rely=0.48)
                login_btn.place_configure(rely=0.60)
                operationallab = ctk.CTkLabel(log, text='There was an error connecting to the database.', font=(font, 12), text_color="red")
                log_err.append(operationallab)
                operationallab.place(relx=0.5, rely=0.76, anchor='center')
            raise ConnectionError(dbUn)
        except Exception as e:
            logging.critical(f"There was an error connecting to the database.\nError: {e}")
            user_inp.place_configure(rely=0.18)
            passwo_inp.place_configure(rely=0.34)
            show_pass.place_configure(rely=0.34)
            rememberMe.place_configure(rely=0.48)
            login_btn.place_configure(rely=0.60)
            operationallab = ctk.CTkLabel(log, text='There was an error connecting to the database.', font=(font, 12), text_color="red")
            log_err.append(operationallab)
            operationallab.place(relx=0.5, rely=0.76, anchor='center')
            raise ConnectionError(e)
        
        user = None
        password = None
        cursor = None

        if db and db.is_connected():
            logging.info('Connection to database was successful. Attempting login.')
            cursor = db.cursor()
            usercheck = fetch_one(cursor, "SELECT Username from Credentials where Username=%s", username)
            user = usercheck if usercheck else None
            passcheck = fetch_one(cursor, "SELECT Password FROM Credentials WHERE Username=%s", username)
            password = passcheck if passcheck else None

            if username == user and passw == password and cursor:
                id = fetch_one(cursor, "SELECT id FROM Credentials WHERE Username=%s", username)
                cursor.execute("UPDATE Credentials SET LastLogin=%s WHERE id=%s", (gmt, id))
                cursor.execute("UPDATE Credentials SET AppVersion=%s WHERE id=%s", (version, id))
                cursor.execute("UPDATE Credentials SET OS=%s WHERE id=%s", (f"{CurrentOS} {OSType}", id))
                access = fetch_one(cursor, "SELECT Access_Type from Credentials WHERE id=%s", id)
                access_type = access.encode('utf-8')

                try:
                    RememberMe(state)
                except:
                    pass

                if CurrentOS == "Windows":
                    lib_name = "accesstype.dll"
                elif CurrentOS == "Darwin":
                    lib_name = "accesstype.dylib"
                else:
                    logging.critical("Unable to load access type due to incompatible OS.")
                    raise RuntimeError("Incompatible OS")

                dll_path = resource_path('Config', lib_name)
                access_lib = ctypes.CDLL(dll_path)
                access_lib.excel_access.argtypes = [ctypes.c_char_p]
                access_lib.excel_access.restype = ctypes.c_int
                admin_access = bool(access_lib.excel_access(access_type))
                logging.info(f'User {user} signed in successfully.')
                Version_Check()
            else:
                logging.error(f'User {username} failed to login. Please check username and password.')
                cursor.close()
                db.close()
                user_inp.place_configure(rely=0.18)
                passwo_inp.place_configure(rely=0.34)
                show_pass.place_configure(rely=0.34)
                rememberMe.place_configure(rely=0.48)
                login_btn.place_configure(rely=0.60)
                lab = ctk.CTkLabel(log, text='Incorrect username or password.', font=(font, 12), text_color="red")
                log_err.append(lab)
                lab.place(x=150, y=165, anchor='c')
        else:
            logging.error('Connection to database not successful. Please check connection and try again.')
            raise ConnectionError("Unable to connect to database.")

excel_button: Optional[ctk.CTkButton] = None
log_button: Optional[ctk.CTkButton] = None

def open_file(path: str) -> None:
    """Opens a file from given path with the device's default software"""
    if CurrentOS == 'Windows':
        os.startfile(path)
    elif CurrentOS == 'Darwin':
        subprocess.run(["open", path], check=True)

class Search:
    def __init__(self, switch_var: ctk.IntVar) -> None:
        self.switch_var = switch_var
        self.index = 0
        Search.results = None

    def run(self, event=None) -> None:
        self.index = 0
        Search.results = self.Search()
        if Search.results and len(Search.results) > 0:
           self.Display_Results(self.index)

    def Search(self) -> Optional[list[dict[str, Any]]]:
        global label_addr, srch_result, btn, batch_Entry, batch_Label

        Clear()

        srch = ent.get().strip()
        
        srch_result = srch
        label_addr = []

        if srch == "":
            no_result_label = ctk.CTkLabel(app, text='Search bar is empty.\nPlease enter your search parameters and \npress Search or Enter to continue', font=(font, 17))
            label_addr.append(no_result_label)
            no_result_label.place(relx=0.5, rely=0.47, anchor='center')
        elif len(srch) < 3:
            short_input = ctk.CTkLabel(app, text='Please enter at least 3 characters to be searched.', font=(font, 17))
            label_addr.append(short_input)
            short_input.place(relx=0.5, rely=0.47, anchor='center')
        else:
            try:
                p = f"%{srch_result}%"
                sql_query = """ """
                with db.cursor(dictionary=True) as cursor:
                    result = fetch_all(cursor, sql_query, p, p)
                if len(result) > 0:
                    return result
                else:
                    nameString = str(srch_result)
                    ent.delete(0, 'end')

                    if len(nameString) > 15:
                        verbiage = f'No Results Found for {nameString[:15]}...'
                    else:
                        verbiage = f'No Results Found for {nameString}.'

                    no_res_name = ctk.CTkLabel(app, text=verbiage, font=(font, 17))
                    label_addr.append(no_res_name)
                    no_res_name.place(x=250, y=150, anchor="c")
                    return None
            except Exception as e:
                logging.error(f"There was an error fetching results from database: {e}")
                intro_label = ctk.CTkLabel(app, text='There was an error displaying results.', font=(font, 17))
                intro.append(intro_label)
                intro_label.place(relx=0.5, rely=0.5, anchor='center')

    def Display_Results(self, index: int = 0):
        global btn, btn_bck

        Clear()

        self.index = index
        mode = int(self.switch_var.get())
        max_results = 5
        results: list[dict[str, Any]] = getattr(Search, "results") or []
        total_results = len(results)
        ent.delete(0, "end")
        
        row = results[index]
        top_result = row.get("Name") or ""
        mid_result   = row.get("Field_Engineer") or row.get("Email") or ""
        bot_result = row.get("Address") or row.get("Phone_Number") or ""
        last_result = row.get("Area") or ""

        display_rows: dict[str, ctk.CTkLabel] = {}

        display_rows["top_row"] = ctk.CTkLabel(app, text="", font=(font, 17))
        if "⭐" in top_result:
            display_rows["top_row"].configure(text_color="#D9A700", font=(font, 17, "bold"))
        label_addr.append(display_rows["top_row"])
        display_rows["top_row"].place(relx=0.5, rely=0.37, anchor='center')

        display_rows["mid_row"] = ctk.CTkLabel(app, text="", font=(font, 17))
        label_addr.append(display_rows["mid_row"])
        display_rows["mid_row"].place(relx=0.5, rely=0.47, anchor='center')

        display_rows["bot_row"] = ctk.CTkLabel(app, text="", font=(font, 17))
        label_addr.append(display_rows["bot_row"])
        display_rows["bot_row"].place(relx=0.5, rely=0.57, anchor='center')

        if last_result != "":
            display_rows["top_row"].place_configure(rely=0.33)
            display_rows["mid_row"].place_configure(rely=0.43)
            display_rows["bot_row"].place_configure(rely=0.53)

            display_rows["last_row"] = ctk.CTkLabel(app, text="", font=(font, 17))
            label_addr.append(display_rows["last_row"])
            display_rows["last_row"].place(relx=0.5, rely=0.63, anchor='center')

            max_results = len(results)

        if mode == 1:
            if last_result == "":
                animation_config(True)
                type_writer_effect(display_rows["top_row"], top_result, callback=lambda:
                    type_writer_effect(display_rows["mid_row"], mid_result, callback=lambda:
                        type_writer_effect(display_rows["bot_row"], bot_result)))
            else:
                animation_config(True)
                type_writer_effect(display_rows["top_row"], top_result, callback=lambda:
                    type_writer_effect(display_rows["mid_row"], mid_result, callback=lambda:
                        type_writer_effect(display_rows["bot_row"], bot_result, callback=lambda:
                                    type_writer_effect(display_rows["last_row"], last_result))))
        else:
            animation_config(False)
            display_rows["top_row"].configure(text=top_result)
            display_rows["mid_row"].configure(text=mid_result)
            display_rows["bot_row"].configure(text=bot_result)
            if "last_row" in display_rows:
                display_rows["last_row"].configure(text=last_result)

        app.unbind("<Right>")
        app.unbind("<Left>")

        if index < max_results - 1 and index < total_results - 1:
            btn = ctk.CTkButton(app, text="", image=rightArrow, width=30, height=10,
                                font=(font, 20), command=lambda i=index: self.Display_Results(self.index+1),
                                fg_color="#0b7054", hover_color="darkgreen")
            app.bind("<Right>", lambda event: self.Display_Results(self.index+1))
            btn.place(relx=0.9, rely=0.47, anchor='center')

        if index > 0:
            btn_bck = ctk.CTkButton(app, text="", image=leftArrow, width=30, height=10,
                                    font=(font, 20), command=lambda i=index: self.Display_Results(self.index-1),
                                    fg_color="#0b7054", hover_color="darkgreen")
            app.bind("<Left>", lambda event: self.Display_Results(self.index-1))
            btn_bck.place(relx=0.1, rely=0.47, anchor='center')

        if index == max_results - 1 and total_results > max_results:
            extra_results = total_results - max_results
            wording = (f"There is {extra_results} more result in the database.\nRefine your search for better results."
                    if extra_results == 1 else
                    f"There are {extra_results} more results in the database.\nRefine your search for better results.")
            more_results_label = ctk.CTkLabel(app, text=wording, font=(font, 12), text_color="red")
            label_addr.append(more_results_label)
            more_results_label.place(relx=0.5, rely=0.7, anchor='center')

def Clear():
        try:
            for label in log_err:
                if isinstance(label, ctk.CTkLabel):
                    label.destroy()
            log_err.clear()
        except Exception:
            pass

        try:
            for label in intro:
                if isinstance(label, ctk.CTkLabel):
                    label.destroy()
            intro.clear()
        except Exception:
            pass

        try:
            for label in label_addr: label.destroy()
            label_addr.clear()
        except:
            pass

        try:
            btn.place_forget()
        except:
            pass

        try:
            btn_bck.place_forget()
        except:
            pass

def fetch_one(cursor, query: str, *params: str) -> Any:
    cursor.execute(query, params)
    row = cursor.fetchone()
    return row[0]

def fetch_all(cursor, query:str, *params: str) -> list[dict[str, Any]]:
    cursor.execute(query, params)
    rows = cursor.fetchall()
    return rows

def type_writer_effect(label: ctk.CTkLabel, full_text: str, delay: int = 9, callback=None) -> None:
    def animate(i=0):
        if i <= len(full_text):
            label.configure(text=full_text[:i])
            label.after(delay, animate, i + 1)
        else:
            if callback:
                callback()
    animate()

def Version_Check() -> None:
    global v

    with db.cursor() as cursor:
        version_select = fetch_one(cursor, "")
        version_result = fetch_one(cursor, "", version_select)
        link_result = fetch_one(cursor, "", version_select)
        auto_link_result = fetch_one(cursor, "", version_select)

    v = version_result
    
    if version >= float(v):
        logging.info(f'TCALT Version {version} is the latest version.')
        db.commit()
        AppSwitcher.start_menu(log)
    else:
        logging.info(f'App version: {version}')
        logging.info(f'Please update tool to version {v} for latest bug fixes and improvements.')
        Update_Message(link_result, auto_link_result)
        
def safe_destroy(win: ctk.CTk) -> None:
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

def Update_Message(link_result, auto_link) -> None:
    alert = CTkMessagebox(
        title = 'TC App Outdated',
        message = 'TC Address Lookup Tool is outdated.\n'
        f'You are using version {version}.\n'
        f'The new version is {v}.',
        font = (font, 13),
        icon = 'info',
        option_1 = 'Later',
        option_2 = 'Website',
        option_3 = 'Download',
        button_color='#0b7054',
        button_hover_color='darkgreen')
    
    if alert.get() == 'Download':
        db.close()
        user_inp.place_configure(rely=0.13)
        passwo_inp.place_configure(rely=0.29)
        show_pass.place_configure(rely=0.29)
        rememberMe.place_configure(rely=0.43)
        login_btn.place_configure(rely=0.55)
        lab = ctk.CTkLabel(log, text='Downloading new version.', font=(font, 12), text_color="#DCE4EE")
        download_progress = ctk.CTkProgressBar(log, orientation="horizontal", progress_color="#0b7054", width=100, height=5)
        download_progress.set(0)
        log_err.append(lab)
        lab.place(relx=0.5, rely=0.70, anchor='c')
        download_progress.place(x=150, y=175, anchor="center")
        log.update()

        try:
            logging.info("Downloading latest version...")
            download_file = None
            installer_path = None

            if CurrentOS == "Windows":
                download_file = "TCALT.Windows.Setup.exe"
                installer_path = Path(os.environ["TEMP"], download_file)
            
            if CurrentOS == "Darwin":
                download_file = "TCALT.Silicon.MacOS.Setup.pkg"
                installer_path = Path(os.environ.get("TMPDIR", "/tmp"), download_file)

            download = requests.get(f"{auto_link}/{download_file}", stream=True)
            total_size = int(download.headers.get("content-length", 0))
            chunk_size = 8192
            downloaded = 0

            if installer_path:
                with open(installer_path, "wb") as file:
                    for chunk in download.iter_content(chunk_size=chunk_size):
                        file.write(chunk)
                        downloaded += len(chunk)
                        progress = downloaded / total_size
                        download_progress.set(progress)
                        log.update_idletasks()
            
                logging.info("Download complete. Installing new version.")
                lab.configure(text="Download complete. Installing new version...")

                if CurrentOS == "Windows":
                    subprocess.run([installer_path, "/SILENT", "/NORESTART", "/LAUNCH"], check=True)
                
                if CurrentOS == "Darwin":
                    subprocess.run(["open", installer_path], check=True)
                    
            sys.exit(0)
    
        except Exception as e:
            db.close()
            logging.error(f"Failed downloading new version: {e}")
            if download_progress:
                download_progress.place_forget()
            user_inp.place_configure(rely=0.13)
            passwo_inp.place_configure(rely=0.29)
            show_pass.place_configure(rely=0.29)
            rememberMe.place_configure(rely=0.43)
            login_btn.place_configure(rely=0.55)
            lab.place_configure(rely=0.73)
            lab.configure(text='Failed downloading new version.')

    elif alert.get() == 'Website':
        db.close()
        webbrowser.open(link_result)
            
    else:
        if version - float(v) <= -0.5:
            db.close()
            logging.error("App version is no longer supported. Please updated to the latest version to continue.")
            user_inp.place_configure(rely=0.13)
            passwo_inp.place_configure(rely=0.29)
            show_pass.place_configure(rely=0.29)
            rememberMe.place_configure(rely=0.43)
            login_btn.place_configure(rely=0.55)
            login_btn.configure(text='Update')
            lab = ctk.CTkLabel(log, text='App version is no longer supported.\nPlease update to the latest version to continue.', font=(font, 12), text_color="red")
            log_err.append(lab)
            lab.place(x=150, y=165, anchor='c')
        else:
            db.commit()
            AppSwitcher.start_menu(log)


def Application(mode: str):
    global app, ent, srch_btn, tool_btn, intro, rightArrow, leftArrow

    app = ctk.CTk()
    ctk.set_appearance_mode('dark')
    center_window(app, 500, 300)
    app.resizable(False,False)
    app.title('TC Address Lookup Tool')
    _set_icon(app)
    
    placeholder_text = "Enter Address or Name Here"
    entry = ctk.StringVar(value=placeholder_text)
    entry.trace_add("write", lambda *i: _Limit_Entry(entry))
    ent = ctk.CTkEntry(master=app, textvariable=entry, justify='center', font=(font, 13), width=280)
    switch_var = ctk.IntVar(value=0)
    search_instance = Search(switch_var)
    ent.bind('<Return>', search_instance.run)
    ent.bind("<FocusIn>", lambda i: _On_Focus_In(entry, ent, placeholder_text))
    ent.bind("<FocusOut>", lambda i: _On_Focus_Out(entry, ent, placeholder_text))
    ent.place(relx=0.4, rely=0.1, anchor='center')
    intro = []
    intro_label = ctk.CTkLabel(app, text=f'Hello, {user}!\nEnter Address or Name Above and Press ENTER to Search.', font=(font, 15))

    try:
        rightArrow = ctk.CTkImage(Image.open(resource_path('images', 'arrow-right.png')),
                                size=(24, 24))
        leftArrow = ctk.CTkImage(Image.open(resource_path('images', 'arrow-left.png')),
                                size=(24, 24))
        support = ctk.CTkImage(Image.open(resource_path('images', 'email.png')),
                                size=(15, 15))
        tool_icon = ctk.CTkImage(Image.open(resource_path('images', 'menu.png')),
                                 size=(20, 20))
    except Exception as e:
        logging.critical(f"There was an error loading aplication pictures. {e}")
        sys.exit(1)

    intro.append(intro_label)
    intro_label.place(x=250, y=150, anchor='center')
    ctk.CTkLabel(app, text="Support", text_color="#777777", justify="center", font=(font, 10.5)).place(relx=0.05, rely=0.973, anchor="center")
    switch_btn = ctk.CTkSwitch(app, text="", variable=switch_var, progress_color='#0b7054')
    if load_animation():
        switch_btn.toggle()
    switch_btn.place(relx=1.01, rely=0.89, anchor='center')
    srch_btn = ctk.CTkButton(app, text='Search', command=search_instance.run, font=(font, 13, 'bold'), fg_color='#0b7054', hover_color='darkgreen', width=120)
    tool_btn = ctk.CTkButton(app, text='', image=tool_icon, command=lambda: AppSwitcher.start_menu(app), font=(font, 13, 'bold'), fg_color='#0b7054', hover_color='darkgreen', width=10, height=24)
    sprt_btn = ctk.CTkButton(app, text='', image=support, width=25, height=25, command=Support, font=(font, 8, 'bold'), fg_color='#0b7054', hover_color='darkgreen')
    srch_btn.place(relx=0.83, rely=0.1, anchor='center')
    tool_btn.place(relx=0.06, rely=0.1, anchor='center')
    sprt_btn.place(relx=0.05, rely=0.90, anchor="center")
    ctk.CTkLabel(
                app, text='⭐ - VIP Member.\nPlease be sure to enter the address or member name\ncorrectly to ensure proper operation of this tool.',
                font=(font, 13), text_color='#555555').place(relx=0.5, rely=1, anchor="s")
    
    ctk.CTkLabel(app, text=f'ver. {version}', font=(font, 10), text_color=f'{"red" if float(v) > version else "#777777"}').place(relx=0.955, rely=0.97, anchor="center")

    app.bind_all('<Any-KeyPress>', lambda i: Reset_Timer(app))
    app.bind_all('<Any-ButtonPress>', lambda i: Reset_Timer(app))
    app.protocol('WM_DELETE_WINDOW', lambda: Window_Close_App(app))
    app.after(500, ent.focus_set)
    if not getattr(sys, "frozen", False):
        ctk.CTkLabel(app, text="Dev Mode", text_color='red', font=(font, 10), height=0).place(relx=0.950, rely=0.027, anchor='center')
    if mode != '__Member':
        entry.set(mode)
        search_instance.run()
    Reset_Timer(app)
    app.mainloop()
    
def Support():
    today = time.strftime("%Y-%m-%d")
    extract = []
    found_today = False
    
    try:
        with open(logger.log_path, "r", encoding="utf-8", errors="ignore") as recent_log:
            for lines in recent_log:
                if not found_today:
                    if today in lines:
                        found_today = True
                        extract.append(lines)
                else:
                    extract.append(lines)
        recent_log.close()
        subject = f"[TCALT] Support needed - {user}"
        body = "Assistance needed with the TCALT program. Most recent log is attached below:\n\n" + "".join(extract[-70:])
        subject_encoded = urllib.parse.quote(subject)
        body_encoded = urllib.parse.quote(body)
        mailto_link = f"mailto:email@domain.com&subject={subject_encoded}&body={body_encoded}"
        webbrowser.open(mailto_link)
    except Exception as e:
        logging.error(f"There was an error starting support: {e}")

def Window_Close_App(window: ctk.CTk) -> None:
    try:
        db.close()
        logging.info('Connection to TC Database terminated.')
    except:
        logging.critical("Error closing the app.")
    safe_destroy(window)

def Login():
    global log, user_inp, passwo_inp, rememberMe, show_pass, login_btn

    log = ctk.CTk()
    ctk.set_appearance_mode('dark')
    center_window(log, 300, 220)
    log.title('TCO Login')
    log.resizable(False, False)
    _set_icon(log)
    
    cfg_user = remembered_user()
    if cfg_user:
        userVar = ctk.StringVar(value=cfg_user)
        user_inp = ctk.CTkEntry(master=log, textvariable=userVar, justify='center', width=150, font=(font, 13))
    else:
        user_inp = ctk.CTkEntry(master=log, placeholder_text='Username', justify='center', width=150, font=(font, 13))
        user_inp.place(relx=0.5, rely=0.23, anchor="center")
        logging.info("No saved credentials found. Please use your username and password to continue.")
    user_inp.place(relx=0.5, rely=0.23, anchor="center")

    saved_pass = get_login_password(cfg_user) if cfg_user else None
    if saved_pass:
        passVar = ctk.StringVar(value=saved_pass)
        passwo_inp = ctk.CTkEntry(master=log, textvariable=passVar, justify='center', show='•', width=150, font=(font, 13))
        logging.info(f"Remember-me info for user {cfg_user} retrieved successfully.")
    else:
        passwo_inp = ctk.CTkEntry(master=log, placeholder_text='Password', justify='center', show='•', width=150, font=(font, 13))
    passwo_inp.place(relx=0.5, rely=0.39, anchor="center")

    passwo_inp.bind('<Return>', Submit)

    rememberMe = ctk.CTkCheckBox(log, text='Remember Me', checkbox_height=17, checkbox_width=17, corner_radius=3, hover=False, fg_color='darkgreen', font=(font, 13))
    if cfg_user:
        rememberMe.select()
    rememberMe.place(relx=0.5, rely=0.53, anchor="center")

    def Show_Pass(envent=None) -> None:
        if passwo_inp.cget("show") == "•":
            passwo_inp.configure(show='')
            show_pass.configure(image=hidepass_image)
        elif passwo_inp.cget("show") == "":
            passwo_inp.configure(show='•')
            show_pass.configure(image=showpass_image)
        log.update_idletasks()

    try:
        showpass_image = ctk.CTkImage(dark_image=Image.open(resource_path('images', 'view.png')),
                                    size=(13, 13))
        hidepass_image = ctk.CTkImage(dark_image=Image.open(resource_path('images', 'hidden.png')),
                                    size=(13, 13))
        tc_logo = ctk.CTkImage(dark_image=Image.open(resource_path('images', 'TCO.png')),
                                    size=(130, 23))
    except Exception as e:
        logging.critical(f"There was an error loading login images. {e}")
        sys.exit(1)

    show_pass = ctk.CTkButton(log, text="", image=showpass_image, height=20, width=20, fg_color="#0b7054", hover_color="darkgreen", bg_color="transparent", corner_radius=3, font=(font, 11), command=Show_Pass)
    show_pass.place(relx=0.695, rely=0.39, anchor="center")

    login_btn = ctk.CTkButton(log, text='Login', command=Submit, width=150, font=(font, 13, 'bold'), fg_color='#0b7054', hover_color='darkgreen')
    login_btn.place(relx=0.5, rely=0.7, anchor="center")
    ctk.CTkLabel(log, text=f'ver. {version}', font=(font, 9)).place(x=295, y=225, anchor='se') 
    ctk.CTkLabel(log, image=tc_logo, text='').place(x=150, y=200, anchor='c')

    if not _internet_connection():
        login_btn.configure(state='disabled', text='Connection Failed', fg_color='darkred')
        passwo_inp.unbind('<Return>')
        user_inp.place_configure(rely=0.18)
        passwo_inp.place_configure(rely=0.34)
        show_pass.place_configure(rely=0.34)
        rememberMe.place_configure(rely=0.48)
        login_btn.place_configure(rely=0.60)
        connectionerror = ctk.CTkLabel(log, text='There was an error connecting to the database.\nPlease check your connection and try again.', font=(font, 12), text_color="red")
        log_err.append(connectionerror)
        connectionerror.place(relx=0.5, rely=0.76, anchor='center')
    log.mainloop()

def RememberMe(state):
    username = user_inp.get().strip()
    if state == 1:
        remember_user(username, True)
        set_login_password(username, passwo_inp.get().strip())
        logging.info("Credentials saved successfully.")
    else:
        remember_user("", False)
        delete_login_password(username)

def User_Inactive(win: ctk.CTk):
    Window_Close_App(win)
    logging.info('Disconnected due to inactivity. Please login again.')
    Login()

timer: str | None = None
error_list: list[str] = []

def Reset_Timer(window: ctk.CTk, event=None):
    global timer

    if timer is not None:
        window.after_cancel(timer)

    start_time: float = time.time()
    timer = window.after(1000, Update_Timer, start_time, window)

def Update_Timer(start_time: float, window: ctk.CTk) -> None:
    global timer

    elapsed_time: float = time.time() - start_time
    remaining_time: int = 180 - int(elapsed_time)

    if remaining_time > 0:
        timer = window.after(1000, Update_Timer, start_time, window)
    else:
        User_Inactive(window)

def count_process_instances(process_name) -> int:
    count = 0

    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == process_name:
            count += 1
    return count

def Excel_Thread() -> None:
    def run():
        "Run excel function"

    threading.Thread(target=run, daemon=True).start()

def browse_file() -> Path:
    file_path = filedialog.askopenfilename(
        title="Select a CSV file",
        filetypes=[("", "*.csv")]
    )
    if file_path:
        logging.info(f"File {file_path} successfully loaded.")
        return Path(file_path).resolve()
    else:
        logging.warning("No file was selected. Please select a CSV file to continue.")
        raise FileNotFoundError

def resource_path(*parts: str) -> Path:
    return Path()/'to file'

def main_menu() -> None:
    menu = ctk.CTk()
    ctk.set_appearance_mode('dark')
    menu.title('Tool Selector')
    _set_icon(menu)
    menu.resizable(False, False)

    fe_icon_path = resource_path('images', 'field_engineer.png')
    member_icon_path = resource_path('images', 'members.png')
    fe_icon = ctk.CTkImage(Image.open(fe_icon_path), size=(64, 64))
    member_icon = ctk.CTkImage(Image.open(member_icon_path), size=(64, 64))

    TOOLS = ['Field Engineer Information', 'Member Information']

    default = default_tool('load')
    
    if default and default != '' and default_mode['value'] == 0:
        default_mode['value'] = 1
        menu.after(100, lambda: AppSwitcher.start_app(menu, default, 0))

    make_default = ctk.CTkCheckBox(menu, text='Set as default tool', checkbox_height=17, checkbox_width=17, corner_radius=3, hover=False, fg_color='darkgreen', font=(font, 11))
    default_label = ctk.CTkLabel(menu, text=f'Default: {default}', font=(font, 11))
    fe_button = ctk.CTkButton(menu, image=fe_icon, text='', width=96, height=80, fg_color='#0b7054', hover_color='darkgreen', command=lambda: AppSwitcher.start_app(menu, '__Field_Engineer', int(make_default.get())))
    member_button = ctk.CTkButton(menu, image=member_icon, text='', width=96, height=80, fg_color='#0b7054', hover_color='darkgreen', command=lambda: AppSwitcher.start_app(menu, '__Member', int(make_default.get())))
    fe_label = ctk.CTkLabel(menu, text=TOOLS[2], font=(font, 11, 'bold'), height=0)
    member_label = ctk.CTkLabel(menu, text=TOOLS[3], font=(font, 11, 'bold'), height=0)

    center_window(menu, 350, 150)
    fe_button.place(relx=0.3, rely=0.35, anchor='center')
    member_button.place(relx=0.7, rely=0.35, anchor='center')
    fe_label.place(relx=0.3, rely=0.7, anchor='center')
    member_label.place(relx=0.7, rely=0.7, anchor='center')
    make_default.place(relx=0.27, rely=0.9, anchor='center')
    default_label.place(relx=0.47, rely=0.9, anchor='w')
    menu.protocol('WM_DELETE_WINDOW', lambda: Window_Close_App(menu))
    Reset_Timer(menu)
    menu.mainloop()

def center_window(win, width, height) -> None:
    win.update_idletasks()
    screen_w = win.winfo_screenwidth()
    screen_h = win.winfo_screenheight()
    x = int((screen_w / 2) - (width / 2))
    y = int((screen_h / 2) - (height / 2))
    win.geometry(f"{width}x{height}+{x}+{y}")

if __name__ == "__main__":
    CurrentOS = platform.system()
    OSType = platform.release()
    OSVersion = platform.version()        
    gmt = time.strftime('%Y-%m-%d %H:%M %Z', time.localtime(time.time()))
    logger = logs()
    enc = db_info()
    logging.info(f'Operating System: {CurrentOS} {OSType}. Version: {OSVersion}. TCALT Version: {version}')

    log_err: list[str | ctk.CTkLabel] = []
    default_mode = {'value': 0}

    def _internet_connection(host=None, port=None, timeout=3) -> bool:
        if host is None or port is None:
            host = enc.db_info('DB_HOST'); port = int(enc.db_info('DB_PORT'))
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except Exception as e:
            logging.critical(f'Connection to database unsuccessful. Returned error: {e}')
        return False
    
    def _set_icon(win: ctk.CTk) -> object:
        """Select the correct icon based on current OS"""
        if CurrentOS == 'Windows':
            return win.iconbitmap(resource_path('images', 'Logo.ico'))
        elif CurrentOS == 'Darwin':
            logo_path = resource_path('images', 'Logo.gif')
            img = PhotoImage(file=logo_path)
            return win.iconphoto(False, img)
        
    def _On_Focus_In(var: ctk.StringVar, entry: ctk.CTkEntry, placeholder: str) -> None:
        """Removes a placeholder text in a CTkEntry widget when inactive.\n
        Use lambda i:"""
        if entry.get() == placeholder:
            entry.configure(text_color="#DCE4EE")
            var.set("")
    
    def _On_Focus_Out(var: ctk.StringVar, entry: ctk.CTkEntry, placeholder: str):
        """Sets a placeholder text in a CTkEntry widget when inactive.\n
        Use lambda i:"""
        if entry.get() == "":
            entry.configure(text_color="#9D9D9D")
            var.set(placeholder)

    def _Limit_Entry(var: ctk.StringVar, max_len: int = 30):
        """Limits the number of characters allowed in a CTkEntry widget.\n
        Use lambda *i:"""
        value = var.get()
        if len(value) > max_len:
            var.set(value[:max_len])
    if CurrentOS == "Windows":
        from pygetwindow import getWindowsWithTitle
        font = "Malgun Gothic"
        process_name = "TCALT.exe"
        instances_windows = count_process_instances(process_name)

        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception as e:
            logging.error(f'Failed to set DPI settings: {e}')

        if instances_windows > 1:
            logging.critical('Another instance of this program is already running. Bringing app to foreground...')

            for window in getWindowsWithTitle('TCO Login') or getWindowsWithTitle('TCALT'):
                window.activate()
                logging.info('App brought to foreground.')
                break

            sys.exit(0)
    elif CurrentOS == "Darwin":
        font = "Helvetica Neue"
        process_name = "TCALT"
        instances_macos = count_process_instances(process_name)

        if instances_macos > 1:
            logging.critical('Another instance of this program is already running.')
            sys.exit(0)
    else:
        logging.critical(f"TCALT is not compatible with your system.\nCurrent OS = {CurrentOS}")
        sys.exit(1)