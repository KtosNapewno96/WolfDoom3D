import os
import sys
import json
import urllib.request
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk
import zipfile
import time

# --- KONFIGURACJA ---
CURRENT_VERSION = "v0.1.0"
REPO_OWNER = "KtosNapewno96"
REPO_NAME = "WolfDoom3D"
# API GitHub do pobierania najnowszego wydania
API_URL = f"https://github.com{REPO_OWNER}/{REPO_NAME}/releases/latest"
# Nazwa pliku wykonywalnego gry
GAME_EXE_NAME = "wolfdoom3d.exe"

# Ścieżka bazowa (tam gdzie jest updater.exe)
BASE_DIR = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
# Plik wersji w AppData, aby uniknąć problemów z uprawnieniami zapisu
VERSION_FILE = os.path.join(os.getenv('LOCALAPPDATA'), 'WolfDoom3D', 'version.json')

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
        headers = {'User-Agent': 'WolfDoom3D-Updater'}
        req = urllib.request.Request(API_URL, headers=headers)
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            latest_version = data['tag_name']
            
            if latest_version != local_ver:
                download_url = None
                for asset in data.get('assets', []):
                    # Szukamy konkretnie pliku bin_.zip
                    if asset['name'] == "bin_.zip":
                        download_url = asset['browser_download_url']
                        break
                
                if download_url:
                    root = tk.Tk()
                    root.withdraw()
                    if messagebox.askyesno("Aktualizacja", f"Dostępna nowa wersja: {latest_version}\nCzy chcesz zaktualizować grę?"):
                        perform_update(download_url, latest_version)
                    root.destroy()
                else:
                    print("Błąd: Nie znaleziono pliku bin_.zip w wydaniu na GitHubie.")
            else:
                print("Gra jest aktualna.")
    except Exception as e:
        print(f"Błąd połączenia z serwerem aktualizacji: {e}")

def perform_update(url, new_ver):
    upd_win = tk.Tk()
    upd_win.title("WolfDoom3D - Aktualizacja")
    upd_win.geometry("400x150")
    
    # Centrowanie okna na ekranie
    upd_win.update_idletasks()
    width = upd_win.winfo_width()
    height = upd_win.winfo_height()
    x = (upd_win.winfo_screenwidth() // 2) - (width // 2)
    y = (upd_win.winfo_screenheight() // 2) - (height // 2)
    upd_win.geometry(f'{width}x{height}+{x}+{y}')
    
    tk.Label(upd_win, text=f"Pobieranie wersji {new_ver}...", font=("Arial", 10, "bold")).pack(pady=10)
    progress = ttk.Progressbar(upd_win, length=300, mode='determinate')
    progress.pack(pady=10)
    upd_win.update()

    try:
        # 1. Zamknij proces gry, jeśli działa
        os.system(f"taskkill /f /im {GAME_EXE_NAME} >nul 2>&1")
        time.sleep(1.5) # Czekamy chwilę, aż system odblokuje pliki

        temp_zip = os.path.join(BASE_DIR, "temp_update.zip")
        
        # 2. Pobieranie z raportowaniem postępu
        def reporthook(blocknum, blocksize, totalsize):
            readsofar = blocknum * blocksize
            if totalsize > 0:
                percent = readsofar * 1e2 / totalsize
                progress['value'] = percent
                upd_win.update()

        urllib.request.urlretrieve(url, temp_zip, reporthook)

        # 3. Wypakowanie plików (nadpisuje wszystko w folderze gry)
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(BASE_DIR)

        # 4. Sprzątanie i zapis wersji
        os.remove(temp_zip)
        
        if not os.path.exists(os.path.dirname(VERSION_FILE)):
            os.makedirs(os.path.dirname(VERSION_FILE))
        with open(VERSION_FILE, 'w') as f:
            json.dump({"version": new_ver}, f)

        messagebox.showinfo("Sukces", "Aktualizacja zakończona pomyślnie!")
        
        # 5. Uruchomienie nowej wersji
        game_exe = os.path.join(BASE_DIR, GAME_EXE_NAME)
        if os.path.exists(game_exe):
            subprocess.Popen([game_exe], shell=True)
        
        upd_win.destroy()
        os._exit(0)

    except Exception as e:
        messagebox.showerror("Błąd", f"Nie udało się zaktualizować plików:\n{str(e)}")
        upd_win.destroy()

if __name__ == "__main__":
    check_for_updates()
