import os
import sys
import platform
import requests
import subprocess
import time
import zipfile
import shutil
import threading
import tempfile
import customtkinter as ctk
from tkinter import messagebox
from packaging import version

# --- KONFIGURACJA ---
REPO_OWNER = "oskarkonitz"
REPO_NAME = "SPlanner"
CURRENT_VERSION = "1.1.2"


# Dodano argument 'txt' do funkcji
def check_for_updates(txt, silent=True):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200: return

        data = response.json()
        latest_tag = data["tag_name"].lstrip("v")

        if version.parse(latest_tag) > version.parse(CURRENT_VERSION):
            system = platform.system()
            asset_url = None
            asset_name = None

            for asset in data["assets"]:
                name = asset["name"].lower()
                if system == "Windows" and name.endswith(".exe"):
                    asset_url = asset["browser_download_url"]
                    asset_name = asset["name"]
                elif system == "Darwin" and name.endswith(".zip"):
                    asset_url = asset["browser_download_url"]
                    asset_name = asset["name"]

            if asset_url:
                ask_download(txt, latest_tag, asset_url, asset_name, data["body"])
            else:
                if not silent:
                    messagebox.showwarning(txt.get("msg_error", "Error"),
                                           txt.get("upd_no_file", "No file for your system."))
        else:
            if not silent:
                messagebox.showinfo(txt.get("msg_info", "Info"),
                                    txt.get("upd_latest", "You have the latest version").format(
                                        version=CURRENT_VERSION))

    except Exception as e:
        print(f"Update error: {e}")
        if not silent:
            messagebox.showerror(txt.get("msg_error", "Error"), txt.get("upd_net_error", "No internet connection."))


def ask_download(txt, ver, url, filename, body):
    # Formatuje wiadomość używając szablonu z pliku językowego
    # DODANO: parametr 'current=CURRENT_VERSION'
    msg = txt.get("upd_available_msg", "New version {ver} available!").format(
        ver=ver,
        body=body,
        current=CURRENT_VERSION
    )

    if messagebox.askyesno(txt.get("upd_title", "Update"), msg):
        DownloadWindow(txt, url, filename)


class DownloadWindow(ctk.CTkToplevel):
    def __init__(self, txt, url, filename):
        super().__init__()
        self.txt = txt
        self.title(txt.get("upd_win_title", "Downloading update..."))
        self.geometry("300x150")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        self.url = url
        self.filename = filename

        self.lbl = ctk.CTkLabel(self, text=txt.get("upd_downloading", "Downloading..."), font=("Arial", 14))
        self.lbl.pack(pady=20)

        self.progress = ctk.CTkProgressBar(self)
        self.progress.pack(pady=10, padx=20)
        self.progress.set(0)

        threading.Thread(target=self.start_download, daemon=True).start()

    def start_download(self):
        try:
            r = requests.get(self.url, stream=True)
            total_size = int(r.headers.get('content-length', 0))
            block_size = 1024
            wrote = 0

            temp_dir = tempfile.gettempdir()
            save_name = "update_pkg.zip" if self.filename.endswith(".zip") else "update_new.exe"
            self.full_save_path = os.path.join(temp_dir, save_name)

            with open(self.full_save_path, 'wb') as f:
                for data in r.iter_content(block_size):
                    wrote = wrote + len(data)
                    f.write(data)
                    if total_size > 0:
                        prog = wrote / total_size
                        self.progress.set(prog)
                        self.lbl.configure(text=f"{int(prog * 100)}%")

            self.lbl.configure(text=self.txt.get("upd_installing", "Installing..."))
            self.install_update()

        except Exception as e:
            messagebox.showerror(self.txt.get("msg_error", "Error"),
                                 f"{self.txt.get('upd_err_download', 'Download error')}: {e}")
            self.destroy()

    def install_update(self):
        current_exe = sys.executable
        system = platform.system()
        temp_file = self.full_save_path

        if system == "Windows":
            temp_dir = tempfile.gettempdir()
            bat_path = os.path.join(temp_dir, "updater.bat")

            bat_script = f"""
@echo off
timeout /t 2 /nobreak > NUL
del "{current_exe}"
move "{temp_file}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
"""
            with open(bat_path, "w") as f:
                f.write(bat_script)

            subprocess.Popen(bat_path, shell=True)
            os._exit(0)

        elif system == "Darwin":
            app_path = os.path.abspath(current_exe)
            while ".app" not in os.path.basename(app_path):
                app_path = os.path.dirname(app_path)
                if app_path == "/" or not app_path:
                    messagebox.showerror(self.txt.get("msg_error", "Error"),
                                         self.txt.get("upd_err_app", "Cannot locate .app"))
                    return

            install_dir = os.path.dirname(app_path)
            temp_dir = tempfile.gettempdir()
            sh_path = os.path.join(temp_dir, "updater.sh")

            sh_script = f"""
#!/bin/bash
sleep 2
rm -rf "{app_path}"
unzip -o "{temp_file}" -d "{install_dir}"
xattr -cr "{app_path}"
open "{app_path}"
rm "{temp_file}"
rm "$0"
"""
            with open(sh_path, "w") as f:
                f.write(sh_script)

            subprocess.Popen(["/bin/bash", sh_path])
            os._exit(0)