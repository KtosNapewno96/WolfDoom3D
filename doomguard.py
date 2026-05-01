import pygame as pg
import time
import random
import ctypes
import threading
import os
import sys
import tkinter as tk

class AntiCheat:
    def __init__(self, game):
        self.game = game
        self.is_detected = False
        self._window_launched = False

        self.safe_title = "DOOM_ULTIMATE_ENGINE_PRO_X"
        os.system(f"title {self.safe_title}")

        # 1. Szyfrowanie pamięci
        self._memory_vault = bytearray(os.urandom(1024))
        self._vault_offset = random.randint(0, 1000)
        self._vault_key = random.randint(1, 255)
        self.set_secure_val(100)

        # 2. Listy blokad
        self.kill_list = ["cheatengine", "x64dbg.exe", "ollydbg.exe", "scylla.exe"]
        self.blacklist = ["cheat engine", "debugger", "x64dbg", "process hacker", 
                          "minecraft cheats", "aimbot", "bomba atomowa", "fbi open up",
                          "memory", "mem"]

        # --- NOWOŚĆ: NATYCHMIASTOWY SKAN PRZED STARTEM ---
        self._initial_check()
        
        # Start pętli w tle
        threading.Thread(target=self._enforcement_loop, daemon=True).start()

    def set_secure_val(self, val):
        self._memory_vault[self._vault_offset] = random.randint(0, 255)
        self._vault_offset = random.randint(0, 1023)
        self._vault_key = random.randint(1, 255)
        self._memory_vault[self._vault_offset] = (val ^ self._vault_key) & 0xFF

    def get_secure_val(self):
        val = self._memory_vault[self._vault_offset] ^ self._vault_key
        self.set_secure_val(val)
        return val

    def _initial_check(self):
        """Sprawdza system zanim gra w ogóle ruszy."""
        self._check_processes()
        self._scan_windows()
        if self.is_detected:
            self._show_nuke_box()

    def _check_processes(self):
        tasklist = os.popen("tasklist /NH /FO CSV").read().lower()
        for process in self.kill_list:
            if process in tasklist:
                os.system(f"taskkill /F /IM {process} /T >nul 2>&1")
                self.is_detected = True

    def _scan_windows(self):
        enum_windows = ctypes.windll.user32.EnumWindows
        proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
        
        def check_window(hwnd, lParam):
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value.lower()
                if self.safe_title.lower() not in title:
                    for word in self.blacklist:
                        if word in title: self.is_detected = True
            return True
        enum_windows(proc(check_window), 0)

    def _show_nuke_box(self):
        if self._window_launched: return
        self._window_launched = True
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        top = tk.Toplevel(root)
        top.title("FEDERAL BUREAU OF INVESTIGATION")
        top.geometry("500x250")
        top.configure(bg="#1a0000")
        tk.Label(top, text="!!! CHEAT DETECTED !!!", fg="red", bg="#1a0000", font=("Consolas", 16, "bold")).pack(pady=10)
        tk.Label(top, text="FBI OPEN UP!!!", fg="white", bg="#1a0000", font=("Impact", 35, "italic")).pack(pady=10)
        msg = "UNAUTHORIZED TOOLS TERMINATED.\nBYTEARRAY VAULT LOCKED.\nALL SYSTEMS COMPROMISED."
        tk.Label(top, text=msg, fg="#808080", bg="#1a0000", font=("Consolas", 10)).pack(pady=10)
        top.protocol("WM_DELETE_WINDOW", lambda: None)
        top.after(10000, lambda: os._exit(1))
        top.mainloop()

    def _enforcement_loop(self):
        while not self.is_detected:
            self._check_processes()
            self._scan_windows()
            if self.is_detected: self._show_nuke_box()
            time.sleep(1.5)

    def apply_chaos(self):
        if self.is_detected:
            self.game.player.angle += 0.8
            self.game.screen.fill((180, 0, 0))
            pg.display.flip()

    def update(self):
        secure_health = self.get_secure_val()
        if hasattr(self.game.player, "health"):
            if self.game.player.health != secure_health: self.is_detected = True
        if self.is_detected:
            self.apply_chaos()
            self._show_nuke_box()
