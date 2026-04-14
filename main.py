import subprocess
import os
import sys

def run_updater():
    # Pobieramy ścieżkę do folderu, w którym jest nasza gra
    base_path = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
    updater_path = os.path.join(base_path, "updater.py")

    if os.path.exists(updater_path):
        try:
            # Uruchamiamy updater i czekamy aż skończy (check_call)
            # Jeśli klikniesz "Ignore", updater się zamknie i gra ruszy dalej.
            # Jeśli klikniesz "Update", updater zamknie grę sam.
            subprocess.check_call([updater_path])
        except Exception as e:
            print(f"Updater start error!: {e}")
    else:
        print("Updater not detected!")

import tkinter as tk
from tkinter import messagebox

# --- 1. INTEGRALNOŚĆ I OCHRONA ---
def integrity_fail():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    messagebox.showerror("SECURITY ERROR", "DoomGuard module (doomguard) not detected!")
    sys.exit()

try:
    from doomguard import AntiCheat
except (ImportError, ModuleNotFoundError):
    integrity_fail()

# --- 2. AUDIO I SILNIK ---
import pygame as pg
pg.mixer.pre_init(96000, -32, 2, 4096)
pg.init()

from settings import *
from map import *
from player import *
from raycasting import *
from object_renderer import *
from sprite_object import *
from object_handler import *
from weapon import *
from sound import *
from pathfinding import *

class Game:
    def __init__(self):
        pg.mouse.set_visible(False)
        pg.display.set_caption("DOOM_ULTIMATE_ENGINE_PRO_X")
        self.screen = pg.display.set_mode(RES, pg.SCALED | pg.DOUBLEBUF)
        pg.event.set_grab(True)
        self.clock = pg.time.Clock()
        
        # --- LOGIKA CZASU ---
        self.raw_delta_time = 1
        self.delta_time = 1
        self.time_scale = 1.0  # 1.0 = normalny, 0.3 = Matrix
        
        self.global_trigger = False
        self.global_event = pg.USEREVENT + 0
        pg.time.set_timer(self.global_event, 40)
        
        self.bullet_holes = []
        self.new_game()
        self.anticheat = AntiCheat(self)

    def new_game(self):
        self.map = Map(self)
        self.player = Player(self)
        self.object_renderer = ObjectRenderer(self)
        self.raycasting = RayCasting(self)
        self.object_handler = ObjectHandler(self)
        self.weapon = Weapon(self)
        self.sound = Sound(self)
        self.pathfinding = PathFinding(self)
        self.bullet_holes = []
        self.time_scale = 1.0 
        pg.mixer.music.play(-1)

    def update(self):
        self.anticheat.update()
        self.player.update()
        self.raycasting.update()
        self.object_handler.update()
        self.weapon.update()
        [hole.update() for hole in self.bullet_holes]
        
        pg.display.flip()
        
        # OBLICZANIE DELTA TIME Z UWZGLĘDNIENIEM SPOWOLNIENIA
        self.raw_delta_time = self.clock.tick(FPS)
        self.delta_time = self.raw_delta_time * self.time_scale

    def draw(self):
        self.object_renderer.draw()
        self.weapon.draw()

    def check_events(self):
        self.global_trigger = False
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                pg.quit()
                sys.exit()
            elif event.type == self.global_event:
                self.global_trigger = True
            self.player.single_fire_event(event)

    def run(self):
        while True:
            self.check_events()
            self.draw()
            self.update()

if __name__ == '__main__':
    game = Game()
    game.run()
