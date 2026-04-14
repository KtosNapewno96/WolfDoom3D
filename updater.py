import os
import sys
import json
import urllib.request
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk

# --- KONFIGURACJA ---
CURRENT_VERSION = "v0.1.0"
REPO_OWNER = "TWOJ_NICK"
REPO_NAME = "WolfDoom3D"
API_URL = f"https://github.com{REPO_OWNER}/{REPO_NAME}/releases/latest"

# Ścieżka do folderu z grą i pliku wersji
BASE_DIR = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
VERSION_FILE = os.path.join(os.getenv('LOCALAPPDATA'), 'Programs', 'WolfDoom3D', 'version.json')

def get_local_version():
    try:
        if os.path.exists(VERSION_FILE):
            with open(VERSION_FILE, 'r') as f:
                return json.load(f).get("version", CURRENT_VERSION)
    except:
        pass
    return CURRENT_VERSION

def check_for_updates():
    local_ver = get_local_version()
    try:
        # Pobieranie info o najnowszej wersji
        headers = {'User-Agent': 'WolfDoom3D-Updater'}
        req = urllib.request.Request(API_URL, headers=headers)
        
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            latest_version = data['tag_name']
            
            if latest_version != local_ver:
                # Szukamy linku do pliku EXE w assets
                download_url = None
                for asset in data.get('assets', []):
                    if asset['name'].endswith('.exe'):
                        download_url = asset['browser_download_url']
                        break
                
                if download_url:
                    root = tk.Tk()
                    root.withdraw()
                    if messagebox.askyesno("Update Available", f"A new version ({latest_version}) is ready!\nUpdate now?"):
                        perform_update(download_url, latest_version)
                    root.destroy()
    except Exception as e:
        print(f"Update check skipped (offline or error): {e}")

def perform_update(url, new_ver):
    upd_win = tk.Tk()
    upd_win.title("WolfDoom3D Updater")
    upd_win.geometry("400x150")
    upd_win.eval('centralize') # Proste centrowanie (opcjonalne)
    
    tk.Label(upd_win, text=f"Downloading update {new_ver}...", font=("Arial", 10, "bold")).pack(pady=10)
    progress = ttk.Progressbar(upd_win, length=300, mode='determinate')
    progress.pack(pady=10)
    upd_win.update()

    try:
        temp_exe = os.path.join(BASE_DIR, "WolfDoom3D_new.exe")
        
        # Pobieranie z raportowaniem postępu
        def reporthook(blocknum, blocksize, totalsize):
            readsofar = blocknum * blocksize
            if totalsize > 0:
                percent = readsofar * 1e2 / totalsize
                progress['value'] = percent
                upd_win.update()

        urllib.request.urlretrieve(url, temp_exe, reporthook)

        # Zaktualizuj lokalny plik wersji
        if not os.path.exists(os.path.dirname(VERSION_FILE)):
            os.makedirs(os.path.dirname(VERSION_FILE))
        with open(VERSION_FILE, 'w') as f:
            json.dump({"version": new_ver}, f)

        # Skrypt CMD do podmiany plików po zamknięciu procesów
        game_exe = os.path.join(BASE_DIR, "WolfDoom3D.exe")
        
        # Tworzymy batcha, który podmieni pliki
        batch_script = f"""
        @echo off
        timeout /t 1 /nobreak > nul
        del "{game_exe}"
        move "{temp_exe}" "{game_exe}"
        start "" "{game_exe}"
        exit
        """
        batch_path = os.path.join(BASE_DIR, "finish_update.bat")
        with open(batch_path, "w") as f:
            f.write(batch_script)

        # Uruchom bat i zamknij wszystko
        subprocess.Popen([batch_path], shell=True)
        os._exit(0)

    except Exception as e:
        messagebox.showerror("Update Error", f"Failed to apply update:\n{str(e)}")
        upd_win.destroy()

if __name__ == "__main__":
    check_for_updates()