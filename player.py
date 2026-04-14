from settings import *
import pygame as pg
import math
import random

class Player:
    def __init__(self, game):
        self.game = game
        self.x, self.y = PLAYER_POS
        self.angle = PLAYER_ANGLE
        self.shot = False
        self.health = PLAYER_MAX_HEALTH
        self.rel = 0
        self.health_recovery_delay = 700
        self.time_prev = pg.time.get_ticks()
        self.diag_move_corr = 1 / math.sqrt(2)
        
        # EFEKTY
        self.stun_intensity = 0

    def recover_health(self):
        if self.check_health_recovery_delay() and self.health < PLAYER_MAX_HEALTH:
            self.health += 1
            self.game.anticheat.set_secure_val(self.health)

    def check_health_recovery_delay(self):
        time_now = pg.time.get_ticks()
        if time_now - self.time_prev > self.health_recovery_delay:
            self.time_prev = time_now
            return True

    def check_game_over(self):
        if self.health < 1:
            self.game.object_renderer.game_over()
            pg.display.flip()
            pg.time.delay(1500)
            self.game.new_game()
            self.game.anticheat.set_secure_val(self.game.player.health)

    def get_damage(self, damage):
        self.health -= damage
        self.game.anticheat.set_secure_val(self.health)
        
        # --- EFEKT TRAFIENIA ---
        self.stun_intensity = min(damage * 0.8, 15)
        self.game.time_scale = 0.2  # Błyskawiczne spowolnienie (Matrix!)
        
        self.game.object_renderer.player_damage()
        self.game.sound.player_pain.play()
        self.check_game_over()

    def single_fire_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1 and not self.shot and not self.game.weapon.reloading:
                self.game.sound.shotgun.play()
                self.shot = True
                self.game.weapon.reloading = True

    def movement(self):
        sin_a = math.sin(self.angle)
        cos_a = math.cos(self.angle)
        dx, dy = 0, 0
        
        # Używamy delta_time, więc ruch też zwalnia w Bullet Time
        speed = PLAYER_SPEED * self.game.delta_time
        speed_sin = speed * sin_a
        speed_cos = speed * cos_a

        keys = pg.key.get_pressed()
        num_key_pressed = -1
        if keys[pg.K_w]:
            num_key_pressed += 1
            dx += speed_cos
            dy += speed_sin
        if keys[pg.K_s]:
            num_key_pressed += 1
            dx += -speed_cos
            dy += -speed_sin
        if keys[pg.K_a]:
            num_key_pressed += 1
            dx += speed_sin
            dy += -speed_cos
        if keys[pg.K_d]:
            num_key_pressed += 1
            dx += -speed_sin
            dy += speed_cos

        if num_key_pressed > 0:
            dx *= self.diag_move_corr
            dy *= self.diag_move_corr

        self.check_wall_collision(dx, dy)
        self.angle %= math.tau

    def check_wall(self, x, y):
        return (x, y) not in self.game.map.world_map

    def check_wall_collision(self, dx, dy):
        # Kolizja skalowana przez raw_delta_time, żeby nie utknąć w ścianie przy slow-mo
        scale = PLAYER_SIZE_SCALE / self.game.raw_delta_time
        if self.check_wall(int(self.x + dx * scale), int(self.y)):
            self.x += dx
        if self.check_wall(int(self.x), int(self.y + dy * scale)):
            self.y += dy

    def mouse_control(self):
        mx, my = pg.mouse.get_pos()
        if mx < MOUSE_BORDER_LEFT or mx > MOUSE_BORDER_RIGHT:
            pg.mouse.set_pos([HALF_WIDTH, HALF_HEIGHT])
        
        self.rel = pg.mouse.get_rel()[0]
        self.rel = max(-MOUSE_MAX_REL, min(MOUSE_MAX_REL, self.rel))
        
        stun_drift = 0
        if self.stun_intensity > 0:
            stun_drift = random.uniform(-1, 1) * (self.stun_intensity * 0.005)
            
        # Myszka działa normalnie (raw_delta), żebyś mógł celować w slow-mo!
        self.angle += (self.rel * MOUSE_SENSITIVITY * self.game.raw_delta_time) + stun_drift

    def update(self):
        self.movement()
        self.mouse_control()
        self.recover_health()
        
        # POWRÓT DO NORMALNEGO CZASU
        if self.game.time_scale < 1.0:
            # Wartość 0.001 kontroluje jak długo trwa spowolnienie
            self.game.time_scale += 0.0008 * self.game.raw_delta_time
            if self.game.time_scale > 1.0:
                self.game.time_scale = 1.0

        if self.stun_intensity > 0:
            self.stun_intensity -= 0.1 * self.game.raw_delta_time

    @property
    def pos(self):
        return self.x, self.y

    @property
    def map_pos(self):
        return int(self.x), int(self.y)
