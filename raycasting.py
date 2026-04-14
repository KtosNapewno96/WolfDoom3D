import pygame as pg
import math
from settings import *
from sprite_object import SpriteObject

class RayCasting:
    def __init__(self, game):
        self.game = game
        self.ray_casting_result = []
        self.objects_to_render = []
        self.textures = self.game.object_renderer.wall_textures

    def get_objects_to_render(self):
        self.objects_to_render = []
        for ray, values in enumerate(self.ray_casting_result):
            depth, proj_height, texture, offset, shadow = values # Dodano shadow

            if proj_height < HEIGHT:
                wall_column = self.textures[texture].subsurface(
                    offset * (TEXTURE_SIZE - SCALE), 0, SCALE, TEXTURE_SIZE
                )
                wall_column = pg.transform.scale(wall_column, (SCALE, int(proj_height)))
                wall_pos = (ray * SCALE, HALF_HEIGHT - int(proj_height) // 2)
            else:
                texture_height = TEXTURE_SIZE * HEIGHT / proj_height
                wall_column = self.textures[texture].subsurface(
                    offset * (TEXTURE_SIZE - SCALE), HALF_TEXTURE_SIZE - texture_height // 2,
                    SCALE, texture_height
                )
                wall_column = pg.transform.scale(wall_column, (SCALE, HEIGHT))
                wall_pos = (ray * SCALE, 0)

            # --- EFEKT CIENIOWANIA (GPU Friendly) ---
            # Tworzymy ciemną nakładkę o intensywności zależnej od dystansu i typu ściany
            # Im większy depth, tym ciemniej. 'shadow' to 0.75 dla pionowych ścian.
            color_v = 255 * (1 / (1 + depth * depth * 0.0001)) # Mgła dystansu
            if shadow < 1.0: color_v *= shadow # Przyciemnienie ścian pionowych
            
            # Nakładamy cień bezpośrednio na wyciętą kolumnę
            # Używamy BLEND_RGBA_MULT dla najlepszego efektu cieni
            darkness = int(max(0, min(255, color_v)))
            wall_column.fill((darkness, darkness, darkness), special_flags=pg.BLEND_RGBA_MULT)

            self.objects_to_render.append((depth, wall_column, wall_pos))

    def add_bullet_hole(self, pos):
        if len(self.game.bullet_holes) > 100:
            self.game.bullet_holes.pop(0)
        new_hole = SpriteObject(self.game, 
                                path='resources/sprites/static_sprites/bullet_hole.png',
                                pos=pos, scale=0.06, shift=0.0)
        new_hole.image = new_hole.image.convert_alpha()
        self.game.bullet_holes.append(new_hole)

    def ray_cast(self):
        self.ray_casting_result = []
        ox, oy = self.game.player.pos
        x_map, y_map = self.game.player.map_pos
        ray_angle = self.game.player.angle - HALF_FOV + 0.0001

        for ray in range(NUM_RAYS):
            sin_a = math.sin(ray_angle)
            cos_a = math.cos(ray_angle)

            # Horizontals (DDA)
            y_hor, dy = (y_map + 1, 1) if sin_a > 0 else (y_map - 1e-6, -1)
            depth_hor = (y_hor - oy) / sin_a
            x_hor = ox + depth_hor * cos_a
            delta_depth = dy / sin_a
            dx = delta_depth * cos_a
            for i in range(MAX_DEPTH):
                tile_hor = int(x_hor), int(y_hor)
                if tile_hor in self.game.map.world_map:
                    texture_hor = self.game.map.world_map[tile_hor]
                    break
                x_hor += dx
                y_hor += dy
                depth_hor += delta_depth

            # Verticals (DDA)
            x_vert, dx = (x_map + 1, 1) if cos_a > 0 else (x_map - 1e-6, -1)
            depth_vert = (x_vert - ox) / cos_a
            y_vert = oy + depth_vert * sin_a
            delta_depth = dx / cos_a
            dy = delta_depth * sin_a
            for i in range(MAX_DEPTH):
                tile_vert = int(x_vert), int(y_vert)
                if tile_vert in self.game.map.world_map:
                    texture_vert = self.game.map.world_map[tile_vert]
                    break
                x_vert += dx
                y_vert += dy
                depth_vert += delta_depth

            # Wybór uderzenia i ustawienie shadow_factor
            if depth_vert < depth_hor:
                depth, texture = depth_vert, texture_vert
                y_vert %= 1
                offset = y_vert if cos_a > 0 else (1 - y_vert)
                shadow = 0.75 # Ściana boczna jest ciemniejsza
            else:
                depth, texture = depth_hor, texture_hor
                x_hor %= 1
                offset = (1 - x_hor) if sin_a > 0 else x_hor
                shadow = 1.0 # Ściana frontalna jest jasna

            # LOGIKA STRZAŁU
            if ray == NUM_RAYS // 2 and self.game.player.shot:
                margin = 0.03
                hit_pos = (ox + (depth - margin) * cos_a, oy + (depth - margin) * sin_a)
                self.add_bullet_hole(hit_pos)

            depth *= math.cos(self.game.player.angle - ray_angle)
            proj_height = SCREEN_DIST / (depth + 0.0001)
            
            # Przekazujemy shadow do result, by get_objects_to_render go użył
            self.ray_casting_result.append((depth, proj_height, texture, offset, shadow))
            ray_angle += DELTA_ANGLE

    def update(self):
        self.ray_cast()
        self.get_objects_to_render()
