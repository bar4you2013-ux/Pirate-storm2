import json
import pygame
import math
import random
import sys
import os
import base64

pygame.init()

# ============================================================
# ЗВУКОВАЯ СИСТЕМА v0.8
# ============================================================
# Создай рядом с игрой папку sounds и положи туда:
# cannon.wav, cannon_hit.wav, collision.wav, shore_hit.wav,
# coins.wav, footsteps.wav, sea.wav, wind.wav,
# city_music.ogg, sea_music.ogg
#
# Отсутствующий файл не ломает игру.

class SoundManager:
    """Звуковой движок v0.8.1. Все MP3 лежат рядом с файлом игры."""

    def __init__(self):
        self.enabled = True
        self.master = 0.85
        self.effects = 0.78
        self.music = 0.26
        self.ambient = 0.30
        self.current_music = None
        self.sounds = {}
        self.last_step = 0

        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(24)
            self.sea_channel = pygame.mixer.Channel(20)
            self.wind_channel = pygame.mixer.Channel(21)
            self.step_channel = pygame.mixer.Channel(22)
        except pygame.error:
            self.enabled = False
            return

        base = os.path.dirname(os.path.abspath(__file__))

        files = {
            "cannon": "cannon.mp3",
            "cannon2": "cannon2.mp3",
            "cannon_hit": "cannon_hit.mp3",
            "collision": "collision.mp3",
            "coins": "coins.mp3",
            "footsteps": "steps.mp3",
            "sea": "sea sound.mp3",
            "wind": "wind.mp3",
        }

        for key, filename in files.items():
            try:
                self.sounds[key] = pygame.mixer.Sound(os.path.join(base, filename))
            except (pygame.error, FileNotFoundError):
                self.sounds[key] = None

        self.music_files = {
            "city": os.path.join(base, "pirat music.mp3"),
        }

    def play(self, name, volume=1.0):
        if not self.enabled:
            return
        sound = self.sounds.get(name)
        if sound:
            sound.set_volume(max(0.0, min(1.0, volume * self.effects * self.master)))
            sound.play()

    def play_cannon(self):
        choices = [name for name in ("cannon", "cannon2") if self.sounds.get(name)]
        if choices:
            self.play(random.choice(choices), random.uniform(0.88, 1.0))

    def play_spatial(self, name, x, y, listener_x, listener_y,
                     max_distance=1000, volume=1.0):
        if not self.enabled:
            return
        sound = self.sounds.get(name)
        if not sound:
            return
        dx, dy = x-listener_x, y-listener_y
        dist = math.hypot(dx, dy)
        if dist >= max_distance:
            return
        gain = (1.0-dist/max_distance) ** 1.3
        pan = max(-1.0, min(1.0, dx/(max_distance*0.55)))
        base = gain * volume * self.effects * self.master
        left = base * (1.0-max(0.0, pan)*0.72)
        right = base * (1.0+min(0.0, pan)*0.72)
        ch = pygame.mixer.find_channel(True)
        if ch:
            ch.set_volume(max(0.0, min(1.0, left)),
                          max(0.0, min(1.0, right)))
            ch.play(sound)

    def update_ambient(self, mode, wind_strength):
        if not self.enabled:
            return
        sea = self.sounds.get("sea")
        wind = self.sounds.get("wind")
        if mode == "sea":
            if sea and not self.sea_channel.get_busy():
                self.sea_channel.play(sea, loops=-1)
            if wind and not self.wind_channel.get_busy():
                self.wind_channel.play(wind, loops=-1)
            self.sea_channel.set_volume(self.ambient*self.master)
            self.wind_channel.set_volume(
                min(0.55, self.ambient*(0.35+wind_strength*0.75)*self.master)
            )
        else:
            self.sea_channel.set_volume(0.035*self.master)
            self.wind_channel.set_volume(0.015*self.master)

    def step(self):
        if not self.enabled:
            return
        sound = self.sounds.get("footsteps")
        if not sound:
            return
        now = pygame.time.get_ticks()
        if now-self.last_step >= 300:
            self.last_step = now
            self.step_channel.set_volume(0.23*self.effects*self.master)
            self.step_channel.play(sound)

    def play_music(self, mode):
        if not self.enabled:
            return

        # В море оставляем только море и ветер.
        if mode == "sea":
            if self.current_music is not None:
                pygame.mixer.music.fadeout(700)
                self.current_music = None
            return

        if self.current_music == mode:
            return

        path = self.music_files.get(mode)
        if not path or not os.path.exists(path):
            return
        try:
            pygame.mixer.music.fadeout(400)
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.music*self.master)
            pygame.mixer.music.play(-1, fade_ms=600)
            self.current_music = mode
        except pygame.error:
            pass

    def toggle(self):
        self.enabled = not self.enabled
        if self.enabled:
            pygame.mixer.music.unpause()
            self.sea_channel.unpause()
            self.wind_channel.unpause()
            self.step_channel.unpause()
        else:
            pygame.mixer.music.pause()
            self.sea_channel.pause()
            self.wind_channel.pause()
            self.step_channel.pause()

# ============================================================
# ГРОЗА МОРЕЙ v0.8.1
# КРАСИВЫЙ ПОРТ-РОЙАЛ, ПИРАТ И ПРИЧАЛИВАНИЕ
# ============================================================

WIDTH = 1100
HEIGHT = 650
FPS = 60

HUD_HEIGHT = 65
BOTTOM_PANEL = 50

WORLD_WIDTH = 5000
WORLD_HEIGHT = 5000

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Гроза морей v0.9 — Звуки")

clock = pygame.time.Clock()

font = pygame.font.SysFont("arial", 20)
small_font = pygame.font.SysFont("arial", 15)
tiny_font = pygame.font.SysFont("arial", 13)
big_font = pygame.font.SysFont("arial", 32, bold=True)

# ============================================================
# ЦВЕТА
# ============================================================

WHITE = (245, 245, 235)
BLACK = (20, 20, 22)

SEA = (27, 116, 165)
SEA_DARK = (17, 88, 132)
SEA_LIGHT = (65, 155, 195)
FOAM = (200, 235, 235)

SAND = (220, 194, 132)
SAND_DARK = (190, 157, 98)

ROAD = (151, 133, 105)

GREEN = (55, 145, 68)
DARK_GREEN = (34, 102, 51)

BROWN = (115, 72, 38)
DARK_BROWN = (62, 38, 23)
WOOD = (142, 88, 43)
LIGHT_WOOD = (174, 116, 62)

RED = (190, 45, 38)
DARK_RED = (105, 27, 25)

GOLD = (240, 190, 48)
GRAY = (110, 110, 110)
DARK_GRAY = (44, 48, 53)

LIGHT_BLUE = (105, 190, 220)

SAIL_WHITE = (225, 215, 185)
SAIL_PIRATE = (75, 68, 62)
SAIL_BOSS = (125, 30, 28)

SMOKE = (175, 175, 170)


# ============================================================
# ФУНКЦИИ
# ============================================================

def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


def distance(a, b):
    return math.hypot(
        a[0] - b[0],
        a[1] - b[1]
    )


def angle_difference(target, current):
    return (
        target - current + math.pi
    ) % (math.pi * 2) - math.pi


def rotate_point(px, py, angle):
    return (
        px * math.cos(angle) - py * math.sin(angle),
        px * math.sin(angle) + py * math.cos(angle)
    )


def draw_text(text, x, y, color=WHITE, used_font=None):

    if used_font is None:
        used_font = font

    image = used_font.render(
        text,
        True,
        color
    )

    screen.blit(
        image,
        (int(x), int(y))
    )


def draw_centered(text, x, y, color=WHITE, used_font=None):

    if used_font is None:
        used_font = font

    image = used_font.render(
        text,
        True,
        color
    )

    screen.blit(
        image,
        (
            int(x - image.get_width() / 2),
            int(y)
        )
    )


def draw_panel(rect, color=(28, 34, 38), border=GOLD):

    pygame.draw.rect(
        screen,
        color,
        rect,
        border_radius=7
    )

    pygame.draw.rect(
        screen,
        border,
        rect,
        2,
        border_radius=7
    )


# ============================================================
# ЧАСТИЦЫ
# ============================================================

class Particle:

    def __init__(
        self,
        x,
        y,
        dx,
        dy,
        life,
        color,
        size,
        kind="circle"
    ):

        self.x = x
        self.y = y

        self.dx = dx
        self.dy = dy

        self.life = life
        self.max_life = life

        self.color = color
        self.size = size

        self.kind = kind

    def update(self, dt):

        self.x += self.dx * dt
        self.y += self.dy * dt

        self.dx *= 0.985
        self.dy *= 0.985

        self.life -= dt

    def draw(self, camera):

        if self.life <= 0:
            return

        sx, sy = camera.world_to_screen(
            self.x,
            self.y
        )

        ratio = self.life / self.max_life

        size = max(
            1,
            int(self.size * ratio)
        )

        if self.kind == "wood":

            pygame.draw.line(
                screen,
                self.color,
                (
                    int(sx - size),
                    int(sy - size)
                ),
                (
                    int(sx + size),
                    int(sy + size)
                ),
                2
            )

        else:

            pygame.draw.circle(
                screen,
                self.color,
                (
                    int(sx),
                    int(sy)
                ),
                size
            )


# ============================================================
# ВЕТЕР
# ============================================================

class Wind:

    def __init__(self):

        self.angle = random.uniform(
            0,
            math.pi * 2
        )

        self.strength = 0.75

        self.target_angle = self.angle
        self.target_strength = self.strength

        self.change_timer = 18

    def update(self, dt):

        self.change_timer -= dt

        if self.change_timer <= 0:

            self.change_timer = random.uniform(
                15,
                30
            )

            self.target_angle += random.uniform(
                -math.radians(60),
                math.radians(60)
            )

            self.target_angle %= (
                math.pi * 2
            )

            self.target_strength = random.uniform(
                0.55,
                1.0
            )

        diff = angle_difference(
            self.target_angle,
            self.angle
        )

        self.angle += (
            diff * dt * 0.08
        )

        self.angle %= (
            math.pi * 2
        )

        self.strength += (
            self.target_strength
            - self.strength
        ) * dt * 0.08

    def efficiency(self, ship_angle):

        diff = abs(
            angle_difference(
                self.angle,
                ship_angle
            )
        )

        deg = math.degrees(diff)

        if deg <= 30:
            value = 1.00

        elif deg <= 60:
            value = 0.90

        elif deg <= 100:
            value = 0.75

        elif deg <= 130:
            value = 0.52

        elif deg <= 155:
            value = 0.32

        else:
            value = 0.12

        return value * (
            0.55
            + self.strength * 0.45
        )

    def description(self, ship_angle):

        diff = abs(
            angle_difference(
                self.angle,
                ship_angle
            )
        )

        deg = math.degrees(diff)

        if deg <= 30:
            return "ПОПУТНЫЙ"

        if deg <= 60:
            return "ХОРОШИЙ"

        if deg <= 100:
            return "БОКОВОЙ"

        if deg <= 130:
            return "ВСТРЕЧНЫЙ"

        if deg <= 155:
            return "ПЛОХОЙ"

        return "ПРОТИВ ВЕТРА"


# ============================================================
# КАМЕРА
# ============================================================

class Camera:

    def __init__(self):

        self.x = 0
        self.y = 0

    def update(self, x, y):

        self.x = clamp(
            x - WIDTH / 2,
            0,
            WORLD_WIDTH - WIDTH
        )

        self.y = clamp(
            y - HEIGHT / 2,
            0,
            WORLD_HEIGHT - HEIGHT
        )

    def world_to_screen(self, x, y):

        return (
            x - self.x,
            y - self.y
        )


# ============================================================
# ИГРОК В ГОРОДЕ
# ============================================================

class Player:

    def __init__(self):

        self.x = 530
        self.y = 450

        self.w = 26
        self.h = 34

        self.speed = 210

        self.gold = 600
        self.bank_gold = 0

        self.cannonballs = 100
        self.food = 20

        # Анимация пирата
        self.walk_time = 0.0
        self.facing = 1
        self.is_moving = False

    @property
    def rect(self):

        return pygame.Rect(
            int(self.x),
            int(self.y),
            self.w,
            self.h
        )

    def update(self, dt, obstacles):

        keys = pygame.key.get_pressed()

        dx = 0
        dy = 0

        if keys[pygame.K_w]:
            dy -= self.speed * dt

        if keys[pygame.K_s]:
            dy += self.speed * dt

        if keys[pygame.K_a]:
            dx -= self.speed * dt

        if keys[pygame.K_d]:
            dx += self.speed * dt

        self.is_moving = abs(dx) > 0.01 or abs(dy) > 0.01
        if self.is_moving:
            self.walk_time += dt * 10.0
        if dx < 0:
            self.facing = -1
        elif dx > 0:
            self.facing = 1

        self.x += dx

        for obstacle in obstacles:

            if self.rect.colliderect(
                obstacle
            ):

                self.x -= dx
                break

        self.y += dy

        for obstacle in obstacles:

            if self.rect.colliderect(
                obstacle
            ):

                self.y -= dy
                break

        self.x = clamp(
            self.x,
            0,
            WIDTH - self.w
        )

        self.y = clamp(
            self.y,
            HUD_HEIGHT,
            HEIGHT - BOTTOM_PANEL - self.h
        )

    def draw(self):

        # Более детальный пират с простой анимацией ходьбы.
        cx = int(self.x + self.w / 2)
        top = int(self.y)

        bob = int(math.sin(self.walk_time) * 2) if self.is_moving else 0
        step = int(math.sin(self.walk_time) * 5) if self.is_moving else 0

        # Тень.
        pygame.draw.ellipse(
            screen, (80, 65, 48),
            (cx - 12, int(self.y + 28), 24, 9)
        )

        # Сапоги и ноги.
        pygame.draw.line(
            screen, (47, 31, 23),
            (cx - 5, int(self.y + 24 + bob)),
            (cx - 7 - step, int(self.y + 34)),
            5
        )
        pygame.draw.line(
            screen, (47, 31, 23),
            (cx + 5, int(self.y + 24 + bob)),
            (cx + 7 + step, int(self.y + 34)),
            5
        )

        # Камзол.
        body = pygame.Rect(cx - 10, top + 10 + bob, 20, 19)
        pygame.draw.rect(screen, DARK_RED, body, border_radius=5)
        pygame.draw.line(screen, GOLD, (cx, top + 12 + bob), (cx, top + 27 + bob), 2)

        # Ремень и пряжка.
        pygame.draw.rect(screen, DARK_BROWN, (cx - 11, top + 21 + bob, 22, 4))
        pygame.draw.rect(screen, GOLD, (cx - 3, top + 20 + bob, 6, 6), 1)

        # Руки.
        arm = int(math.sin(self.walk_time) * 3) if self.is_moving else 0
        pygame.draw.line(screen, (224, 180, 140),
                         (cx - 9, top + 14 + bob),
                         (cx - 14, top + 23 + bob + arm), 4)
        pygame.draw.line(screen, (224, 180, 140),
                         (cx + 9, top + 14 + bob),
                         (cx + 14, top + 23 + bob - arm), 4)

        # Сабля на боку.
        sword_side = self.facing
        pygame.draw.line(
            screen, (205, 210, 215),
            (cx + 9 * sword_side, top + 23 + bob),
            (cx + 18 * sword_side, top + 32 + bob), 2
        )
        pygame.draw.line(
            screen, GOLD,
            (cx + 6 * sword_side, top + 22 + bob),
            (cx + 12 * sword_side, top + 26 + bob), 2
        )

        # Голова.
        pygame.draw.circle(screen, (224, 180, 140), (cx, top + 7 + bob), 8)

        # Волосы.
        pygame.draw.arc(screen, DARK_BROWN,
                        (cx - 9, top - 1 + bob, 18, 17),
                        math.pi, math.pi * 2, 4)

        # Глаз и повязка.
        eye_x = cx + 3 * self.facing
        pygame.draw.circle(screen, BLACK, (eye_x, top + 6 + bob), 2)
        pygame.draw.line(screen, BLACK,
                         (cx - 7, top + 4 + bob),
                         (cx + 7, top + 8 + bob), 2)

        # Борода.
        pygame.draw.arc(screen, DARK_BROWN,
                        (cx - 6, top + 6 + bob, 12, 10),
                        0, math.pi, 3)

        # Треуголка.
        hat_y = top - 2 + bob
        pygame.draw.polygon(
            screen, BLACK,
            [(cx - 13, hat_y + 3), (cx + 13, hat_y + 3),
             (cx + 7, hat_y - 5), (cx, hat_y - 1),
             (cx - 7, hat_y - 5)]
        )
        pygame.draw.line(screen, GOLD, (cx - 9, hat_y + 1), (cx + 9, hat_y + 1), 1)


# ============================================================
# ЗДАНИЯ
# ============================================================


# Загружаем художественные спрайты один раз, без затрат на каждом кадре.
_EMBEDDED_SPRITES = {'ship_player.png': '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', 'ship_pirate.png': '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', 'ship_trader.png': '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', 'tavern.png': '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', 'bank.png': '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', 'shop.png': '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', 'shipyard.png': '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', 'house.png': 'iVBORw0KGgoAAAANSUhEUgAAAeAAAAKACAYAAABEyKtSAAAABmJLR0QA/wD/AP+gvaeTAAAgAElEQVR4nOydedwkVXnvf+fU0nu/y7yzsgwwMwwww6wuGcXr4BpgQE2CiRqIMTcQvYLXRLMbRrPcxOTeTyIKot6bRIkRMUEFMWqiKCgiDMMyLAEM4MAw+7v023tVnftHv/2+vdTWXae6q7uf7+ejvFNnqVNdVed3nueceg5AEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEBFCiL28320Ig7Cv6/JduxKXbN/86Uu2bvro7t271TDP1Qjdr8FiWK9r2GD9bgAxWuzdu5f/7muxxhB8baaaeIi9+cP5frdJBr24rp/fsmWjwq1bAGxdOPQTS8E7v7nvwE9ln6sO3a/BYliva1jp2QiaIOb+/S+WqTFjvWlYCcYs5LXiegAP97tdQenFdV28ffMVTFg3AEg3HH4FN/Hgnm3nv++Ohx79J5nnA+h+DRrDel3DDFnAROiIe/4qM2POr1ctZaw1zYrhkbFX7T3Zj3YFpRfXdfmuXYliIfeXguFat3xM4AsJQ7zv1scemw96Trpfg8WwXtcoQPMERGiIOz8RK9299+ySVd5h1zkAAIpYL4QIdSAoez6sV9d1yY7N5xZKufucxJfxpeoFwxUFjT2yZ/v5u7o9H90vuq6u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'}
_SPRITES = {}
_ROTATED = {}
def get_sprite(name):
    if name not in _SPRITES:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "groza_sprites", name)
        try:
            _SPRITES[name] = pygame.image.load(path).convert_alpha()
        except (pygame.error, FileNotFoundError):
            try:
                import io
                raw = base64.b64decode(_EMBEDDED_SPRITES[name])
                _SPRITES[name] = pygame.image.load(io.BytesIO(raw),
                                                    name).convert_alpha()
            except (KeyError, pygame.error):
                _SPRITES[name] = None
    return _SPRITES[name]

def draw_ship_sprite(camera, x, y, angle, scale, name):
    source = get_sprite(name)
    if source is None:
        return False
    # Исходный спрайт смотрит вверх; угол 0 в физике означает вправо.
    # Квантование угла и кэш вращений защищают FPS.
    degrees = round((-math.degrees(angle)-90)/3)*3
    size = max(1,round(scale*100))
    key = (name,degrees,size)
    if key not in _ROTATED:
        if len(_ROTATED) > 450:
            _ROTATED.clear()
        small = pygame.transform.smoothscale(source,
                    (max(1,int(64*scale)),max(1,int(86*scale))))
        _ROTATED[key] = pygame.transform.rotate(small,degrees)
    sx,sy=camera.world_to_screen(x,y)
    image=_ROTATED[key]
    screen.blit(image,image.get_rect(center=(int(sx),int(sy))))
    return True

class Building:

    def __init__(
        self,
        x,
        y,
        w,
        h,
        name,
        color
    ):

        self.rect = pygame.Rect(
            x,
            y,
            w,
            h
        )

        self.name = name
        self.color = color

    def draw(self):
        sprite_names = {
            "Таверна": "tavern.png",
            "Банк": "bank.png",
            "Магазин": "shop.png",
            "Верфь": "shipyard.png"
        }
        sprite = get_sprite(sprite_names.get(self.name, "house.png"))
        if sprite:
            w,h=self.rect.width+30,self.rect.height+40
            key=(sprite_names.get(self.name,"house.png"),w,h)
            if not hasattr(self,"building_sprite"):
                self.building_sprite=pygame.transform.smoothscale(sprite,(w,h))
            screen.blit(self.building_sprite,(self.rect.x-15,self.rect.y-28))
            draw_centered(self.name,self.rect.centerx,self.rect.y+77,
                          WHITE,small_font)
            return

        # тень
        shadow = self.rect.move(
            7,
            7
        )

        pygame.draw.rect(
            screen,
            (95, 78, 60),
            shadow,
            border_radius=5
        )

        # стены
        pygame.draw.rect(
            screen,
            self.color,
            self.rect,
            border_radius=5
        )

        # деревянные балки
        pygame.draw.line(
            screen,
            DARK_BROWN,
            (
                self.rect.x + 12,
                self.rect.y
            ),
            (
                self.rect.x + 12,
                self.rect.bottom
            ),
            5
        )

        pygame.draw.line(
            screen,
            DARK_BROWN,
            (
                self.rect.right - 12,
                self.rect.y
            ),
            (
                self.rect.right - 12,
                self.rect.bottom
            ),
            5
        )

        # крыша
        pygame.draw.polygon(
            screen,
            DARK_BROWN,
            [
                (
                    self.rect.x - 12,
                    self.rect.y + 5
                ),
                (
                    self.rect.centerx,
                    self.rect.y - 35
                ),
                (
                    self.rect.right + 12,
                    self.rect.y + 5
                )
            ]
        )

        # дверь
        pygame.draw.rect(
            screen,
            BROWN,
            (
                self.rect.centerx - 14,
                self.rect.bottom - 42,
                28,
                42
            )
        )

        # окна
        for wx in (
            self.rect.x + 30,
            self.rect.right - 55
        ):

            pygame.draw.rect(
                screen,
                LIGHT_BLUE,
                (
                    wx,
                    self.rect.y + 42,
                    25,
                    24
                )
            )

            pygame.draw.line(
                screen,
                WHITE,
                (
                    wx + 12,
                    self.rect.y + 42
                ),
                (
                    wx + 12,
                    self.rect.y + 66
                ),
                2
            )

        draw_centered(
            self.name,
            self.rect.centerx,
            self.rect.y + 77,
            WHITE,
            small_font
        )


# ============================================================
# ОСТРОВА
# ============================================================


def draw_game_house(surface, x, y, scale=1.0, roof=(151, 70, 45)):
    """Небольшой дом с черепичной крышей, окнами и тенью."""
    x, y = int(x), int(y)
    w, h = int(32*scale), int(24*scale)
    if w < 5 or h < 5:
        return
    pygame.draw.ellipse(surface, (43, 77, 48), (x-4, y+h-2, w+11, max(4,h//3)))
    pygame.draw.rect(surface, (210, 184, 133), (x, y, w, h))
    pygame.draw.rect(surface, (112, 83, 61), (x, y, w, h), 2)
    pygame.draw.polygon(surface, (91, 50, 40),
                        [(x-5,y+2),(x+w//2,y-int(14*scale)),(x+w+5,y+2)])
    pygame.draw.polygon(surface, roof,
                        [(x-3,y),(x+w//2,y-int(12*scale)),(x+w+3,y)])
    for k in range(3):
        yy = y-int(2*scale)-k*int(3*scale)
        pygame.draw.line(surface, (189, 103, 63),
                         (x+int(4*scale)+k*2,yy),
                         (x+w-int(4*scale)-k*2,yy),1)
    pygame.draw.rect(surface, (78, 55, 39),
                     (x+w//2-int(3*scale),y+h-int(12*scale),
                      max(3,int(7*scale)),max(5,int(12*scale))))
    pygame.draw.rect(surface, (67, 99, 108),
                     (x+int(5*scale),y+int(5*scale),
                      max(3,int(5*scale)),max(3,int(6*scale))))


def draw_game_palm(surface, x, y, scale=1.0):
    x,y=int(x),int(y)
    h=max(9,int(25*scale))
    crown=(x+int(4*scale),y-h)
    pygame.draw.line(surface,(99,65,39),(x,y),crown,max(2,int(4*scale)))
    for a in (-3.0,-2.5,-2.0,-1.4,-0.9,-0.4,0.2):
        end=(int(crown[0]+math.cos(a)*20*scale),
             int(crown[1]+math.sin(a)*13*scale))
        pygame.draw.line(surface,(26,95,52),crown,end,max(2,int(5*scale)))
        pygame.draw.line(surface,(76,143,61),crown,end,1)


def draw_game_rock(surface, x, y, r):
    x,y,r=int(x),int(y),max(3,int(r))
    pygame.draw.ellipse(surface,(52,105,110),(x-r,y-r//2,r*2,r))
    pygame.draw.polygon(surface,(100,104,99),
                        [(x-r,y),(x-r//3,y-r),(x+r//2,y-r//2),(x+r,y+r//3)])
    pygame.draw.line(surface,(160,158,140),(x-r//3,y-r),
                     (x+r//2,y-r//2),2)

class Island:

    def __init__(
        self,
        x,
        y,
        radius,
        name,
        has_port=False
    ):

        self.x = x
        self.y = y

        self.radius = radius

        self.name = name
        self.has_port = has_port

        # декоративные пальмы
        self.palms = []

        rng = random.Random(
            int(x + y)
        )

        for i in range(
            max(3, int(radius / 60))
        ):

            angle = rng.uniform(
                0,
                math.pi * 2
            )

            r = rng.uniform(
                radius * 0.15,
                radius * 0.55
            )

            self.palms.append(
                (
                    math.cos(angle) * r,
                    math.sin(angle) * r * 0.55
                )
            )

    def draw_details(self, sx, sy):
        r = self.radius
        rng = random.Random(int(self.x*3+self.y*7))
        # Мелководье и прибой на отдельных участках береговой линии.
        for i in range(40):
            a = i*math.tau/40
            px = sx + math.cos(a)*(r+4)
            py = sy + math.sin(a)*(r*.65+4)
            pygame.draw.circle(screen, (148,216,206),
                               (int(px),int(py)), 2 if i%3 else 4, 1)
        # Скалы вдоль побережья.
        for _ in range(max(8,int(r/16))):
            a=rng.random()*math.tau
            rr=rng.uniform(.77,.96)
            draw_game_rock(screen,sx+math.cos(a)*r*rr,
                           sy+math.sin(a)*r*.65*rr,rng.randint(4,10))
        # Деревня на крупных островах; рядом с портом больше построек.
        count=(8 if self.has_port else 3) if r>=170 else 1
        for i in range(count):
            a=math.tau*i/count+.2
            rr=.40 if self.has_port else .28
            hx=sx+math.cos(a)*r*rr
            hy=sy+math.sin(a)*r*rr*.6
            draw_game_house(screen,hx-12,hy-6,.62 if r<230 else .8,
                            (157,72,43) if i%2 else (134,76,50))
        # Пальмы и небольшие тропы.
        for i in range(max(5,int(r/30))):
            a=rng.random()*math.tau
            rr=rng.uniform(.48,.70)
            draw_game_palm(screen,sx+math.cos(a)*r*rr,
                           sy+math.sin(a)*r*.65*rr,.65)
        if self.has_port:
            # Сторожевая башня возле гавани.
            tx=int(sx+r*.43)
            ty=int(sy-r*.31)
            pygame.draw.rect(screen,(169,158,135),(tx,ty,20,32))
            pygame.draw.polygon(screen,(93,69,61),
                                [(tx-4,ty),(tx+10,ty-17),(tx+24,ty)])
            pygame.draw.rect(screen,(45,48,50),(tx+7,ty+8,6,9))
            # Причальные склады.
            draw_game_house(screen,sx+r*.53-24,sy+16,.8,(116,65,47))

    def draw_palm(self, x, y):

        pygame.draw.line(
            screen,
            DARK_BROWN,
            (
                int(x),
                int(y + 14)
            ),
            (
                int(x + 2),
                int(y - 10)
            ),
            4
        )

        for angle in [
            -2.8,
            -2.2,
            -1.55,
            -0.9,
            -0.3
        ]:

            pygame.draw.line(
                screen,
                DARK_GREEN,
                (
                    int(x + 2),
                    int(y - 10)
                ),
                (
                    int(
                        x + 2
                        + math.cos(angle) * 16
                    ),
                    int(
                        y - 10
                        + math.sin(angle) * 10
                    )
                ),
                4
            )

    def make_hd_sprite(self):
        """Кэшируем детализированный остров в двойном разрешении."""
        r = int(self.radius)
        margin = 35
        w, h = 2*(r+margin), int(1.45*r)+2*margin
        factor = 2
        surf = pygame.Surface((w*factor,h*factor),pygame.SRCALPHA)
        rng = random.Random(int(self.x*19+self.y*7))
        cx,cy=w//2,h//2
        def P(x,y): return (int(x*factor),int(y*factor))
        def ellipse(col,rect,width=0):
            pygame.draw.ellipse(surf,col,tuple(int(v*factor) for v in rect),width*factor)
        def polygon(col,pts):
            pygame.draw.polygon(surf,col,[P(x,y) for x,y in pts])
        def circle(col,x,y,rad):
            pygame.draw.circle(surf,col,P(x,y),max(1,int(rad*factor)))
        # Прозрачные рифы, полосы прибоя и песок.
        for k,col in ((23,(21,158,164,55)),(15,(56,196,187,90)),
                      (8,(157,239,215,125)),(3,(226,247,226,190))):
            ellipse(col,(cx-r-k,cy-r*.65-k*.7,2*(r+k),2*(r*.65+k*.7)))
        ellipse((215,192,131),(cx-r,cy-r*.65,2*r,1.3*r))
        ellipse((233,215,163),(cx-r*.92,cy-r*.60,1.84*r,1.2*r))
        ellipse((62,117,66),(cx-r*.78,cy-r*.47,1.56*r,.94*r))
        ellipse((41,91,58),(cx-r*.63,cy-r*.38,1.26*r,.76*r))
        ellipse((32,75,50),(cx-r*.39,cy-r*.24,.78*r,.48*r))
        # Множество камней по краям острова.
        for i in range(int(r*.36)):
            t=rng.random()*math.tau
            d=rng.uniform(.72,.99)
            x=cx+math.cos(t)*r*d
            y=cy+math.sin(t)*r*.65*d
            rad=rng.uniform(2.5,8)
            polygon((70,78,75),[(x-rad,y+rad*.5),(x-rad*.4,y-rad),
                                 (x+rad*.7,y-rad*.65),(x+rad,y+rad*.6)])
            polygon((152,154,137),[(x-rad*.4,y-rad),
                                    (x+rad*.7,y-rad*.65),(x,y)])
        # Мелкие кусты и разнообразная растительность.
        for i in range(int(r*1.7)):
            t=rng.random()*math.tau
            d=math.sqrt(rng.random())*.69
            x=cx+math.cos(t)*r*d
            y=cy+math.sin(t)*r*.58*d
            rad=rng.uniform(1.5,5.5)
            circle(rng.choice(((33,102,53),(53,128,60),
                               (91,144,67),(26,83,49))),x,y,rad)
        # Домики, расположенные вокруг центра.
        count=10 if self.has_port else (3 if r>150 else 1)
        for i in range(count):
            t=i*math.tau/count+.4
            d=.40 if self.has_port else .29
            x=cx+math.cos(t)*r*d
            y=cy+math.sin(t)*r*.52*d
            ww=rng.randint(14,23); hh=rng.randint(10,17)
            polygon((30,53,42),[(x-ww/2+4,y+hh),(x+ww/2+9,y+hh),
                                (x+ww/2+7,y+hh+7),(x-ww/2+4,y+hh+7)])
            pygame.draw.rect(surf,(226,201,159),
                             (*P(x-ww/2,y),int(ww*factor),int(hh*factor)))
            polygon((126,58,43),[(x-ww/2-3,y+1),(x,y-hh*.75),
                                 (x+ww/2+3,y+1)])
            polygon((183,99,60),[(x-ww/2-2,y),(x,y-hh*.75),
                                 (x+ww/2+2,y)])
            pygame.draw.rect(surf,(73,66,50),
                             (*P(x-2,y+hh*.45),int(4*factor),int(hh*.55*factor)))
        # Пальмы: стволы, тени, многолопастные кроны.
        for i in range(max(13,int(r/8))):
            t=rng.random()*math.tau
            d=rng.uniform(.43,.73)
            x=cx+math.cos(t)*r*d
            y=cy+math.sin(t)*r*.6*d
            height=rng.uniform(13,25)
            pygame.draw.line(surf,(45,68,47),P(x+5,y+3),P(x+19,y+9),4*factor)
            pygame.draw.line(surf,(109,75,46),P(x,y),P(x+3,y-height),3*factor)
            tx,ty=x+3,y-height
            for j in range(7):
                aa=j*math.tau/7
                reach=rng.uniform(10,17)
                ex=tx+math.cos(aa)*reach
                ey=ty+math.sin(aa)*reach*.65
                pygame.draw.line(surf,(24,91,49),P(tx,ty),P(ex,ey),5*factor)
                pygame.draw.line(surf,(76,157,67),P(tx,ty-1),P(ex,ey-1),2*factor)
        if self.has_port:
            # Каменная крепость, зубцы и башни.
            x,y=cx+r*.22,cy-r*.27
            pygame.draw.rect(surf,(157,154,133),
                             (*P(x-22,y-12),int(44*factor),int(32*factor)))
            pygame.draw.rect(surf,(110,113,107),
                             (*P(x-22,y+13),int(44*factor),int(7*factor)))
            for xx in (-24,-12,0,12,24):
                pygame.draw.rect(surf,(195,189,160),
                                 (*P(x+xx-4,y-18),int(8*factor),int(9*factor)))
            for xx in (-27,20):
                pygame.draw.rect(surf,(176,172,148),
                                 (*P(x+xx,y-23),int(13*factor),int(43*factor)))
                polygon((109,63,53),[(x+xx-3,y-23),(x+xx+6,y-35),
                                      (x+xx+16,y-23)])
            # Деревянный пирс с досками.
            px=cx+r*.65
            pygame.draw.rect(surf,(102,70,44),
                             (*P(px,cy-11),int(79*factor),int(22*factor)))
            for dx in range(0,79,8):
                pygame.draw.line(surf,(177,127,76),P(px+dx,cy-10),
                                 P(px+dx,cy+10),factor)
            for dx in (5,69):
                circle((59,43,32),px+dx,cy-12,4)
                circle((59,43,32),px+dx,cy+12,4)
        return pygame.transform.smoothscale(surf,(w,h))

    def draw(self, camera):
        sx,sy=camera.world_to_screen(self.x,self.y)
        r=self.radius
        if sx < -r*2 or sx > screen.get_width()+r*2 or sy < -r*2 or sy > screen.get_height()+r*2:
            return
        if not hasattr(self,"hd_sprite"):
            self.hd_sprite=self.make_hd_sprite()
        rect=self.hd_sprite.get_rect(center=(int(sx),int(sy)))
        screen.blit(self.hd_sprite,rect)
        draw_centered(self.name,sx,sy-r*.82,WHITE,small_font)


# ============================================================
# ЯДРА
# ============================================================

class Cannonball:

    def __init__(
        self,
        x,
        y,
        angle,
        owner,
        damage
    ):

        self.x = x
        self.y = y

        self.speed = 420

        self.dx = (
            math.cos(angle)
            * self.speed
        )

        self.dy = (
            math.sin(angle)
            * self.speed
        )

        self.owner = owner
        self.damage = damage

        self.life = 2.2
        self.travelled = 0.0
        self.max_range = 160.0

    def update(self, dt):

        self.x += self.dx * dt
        self.y += self.dy * dt
        self.travelled += self.speed * dt
        if self.travelled >= self.max_range:
            self.life = 0

        self.life -= dt

    def draw(self, camera):

        sx, sy = camera.world_to_screen(
            self.x,
            self.y
        )

        # маленькая тень
        pygame.draw.circle(
            screen,
            SEA_DARK,
            (
                int(sx + 3),
                int(sy + 4)
            ),
            5
        )

        pygame.draw.circle(
            screen,
            BLACK,
            (
                int(sx),
                int(sy)
            ),
            5
        )

        pygame.draw.circle(
            screen,
            GRAY,
            (
                int(sx - 1),
                int(sy - 1)
            ),
            2
        )


# ============================================================
# ДОБЫЧА
# ============================================================

class Loot:

    def __init__(self, x, y):

        self.x = x
        self.y = y

        self.gold = random.randint(
            20,
            70
        )

        self.ammo = random.randint(
            3,
            10
        )

        self.life = 35

    def update(self, dt):
        self.life -= dt

    def draw(self, camera):

        sx, sy = camera.world_to_screen(
            self.x,
            self.y
        )

        pygame.draw.rect(
            screen,
            DARK_BROWN,
            (
                int(sx - 11),
                int(sy - 8),
                22,
                16
            ),
            border_radius=3
        )

        pygame.draw.rect(
            screen,
            GOLD,
            (
                int(sx - 11),
                int(sy - 8),
                22,
                16
            ),
            2,
            border_radius=3
        )

        pygame.draw.line(
            screen,
            GOLD,
            (
                int(sx),
                int(sy - 7)
            ),
            (
                int(sx),
                int(sy + 7)
            ),
            2
        )


# ============================================================
# ФИЗИКА КОРАБЛЕЙ
# ============================================================

class ShipPhysics:

    def __init__(
        self,
        x,
        y,
        cannon_count
    ):

        self.x = x
        self.y = y

        self.angle = -math.pi / 2

        self.speed = 0

        self.cannon_count = cannon_count

        # Физика столкновений
        self.collision_radius = 34 + min(cannon_count, 20) * 0.45
        self.collision_cooldown = 0.0

    def ship_mass(self):

        # Больше пушек — тяжелее корабль и сильнее таран.
        return 1.0 + self.cannon_count * 0.075

    def velocity(self):

        return (
            math.cos(self.angle) * self.speed,
            math.sin(self.angle) * self.speed
        )

    def calculate_base_speed(self):

        return clamp(
            106 - self.cannon_count * 3,
            45,
            100
        )

    def calculate_acceleration(self):

        return clamp(
            48 - self.cannon_count * 0.8,
            22,
            46
        )

    def calculate_rotation(self):

        return clamp(
            1.35 - self.cannon_count * 0.025,
            0.65,
            1.25
        )

    def wind_speed(self, wind):

        return (
            self.calculate_base_speed()
            * wind.efficiency(
                self.angle
            )
        )


# ============================================================
# РИСОВАНИЕ КОРАБЛЯ
# ============================================================

def draw_detailed_ship(
    camera,
    x,
    y,
    angle,
    cannon_count,
    hull_color,
    sail_color,
    flag_color,
    scale=1.0
):

    sprite_name = ("ship_player.png" if flag_color == RED
                   else "ship_pirate.png" if flag_color == BLACK
                   else "ship_trader.png")
    if draw_ship_sprite(camera,x,y,angle,scale,sprite_name):
        return

    sx, sy = camera.world_to_screen(
        x,
        y
    )

    def transform(px, py):

        rx, ry = rotate_point(
            px * scale,
            py * scale,
            angle
        )

        return (
            sx + rx,
            sy + ry
        )

    # ========================================================
    # ТЕНЬ
    # ========================================================

    shadow_points = []

    for p in [
        (38, 4),
        (22, 20),
        (-30, 18),
        (-43, 4),
        (-30, -10),
        (22, -12)
    ]:

        px, py = transform(
            p[0] + 5,
            p[1] + 5
        )

        shadow_points.append(
            (px, py)
        )

    pygame.draw.polygon(
        screen,
        SEA_DARK,
        shadow_points
    )

    # ========================================================
    # КОРПУС
    # ========================================================

    hull = []

    for p in [
        (42, 0),
        (25, 18),
        (-28, 17),
        (-43, 0),
        (-28, -17),
        (25, -18)
    ]:

        hull.append(
            transform(
                p[0],
                p[1]
            )
        )

    pygame.draw.polygon(
        screen,
        hull_color,
        hull
    )

    pygame.draw.polygon(
        screen,
        BLACK,
        hull,
        2
    )

    # ========================================================
    # ПАЛУБА
    # ========================================================

    deck = []

    for p in [
        (27, 0),
        (16, 11),
        (-24, 10),
        (-31, 0),
        (-24, -10),
        (16, -11)
    ]:

        deck.append(
            transform(
                p[0],
                p[1]
            )
        )

    pygame.draw.polygon(
        screen,
        LIGHT_WOOD,
        deck
    )

    # продольные доски
    for offset in [-5, 0, 5]:

        p1 = transform(
            -22,
            offset
        )

        p2 = transform(
            22,
            offset
        )

        pygame.draw.line(
            screen,
            BROWN,
            p1,
            p2,
            1
        )

    # ========================================================
    # ПУШКИ
    # ========================================================

    guns_side = min(
        cannon_count // 2,
        6
    )

    if guns_side > 0:

        for i in range(guns_side):

            position = (
                -18
                + i * (
                    34 / max(
                        1,
                        guns_side - 1
                    )
                )
                if guns_side > 1
                else 0
            )

            for side in [-1, 1]:

                base = transform(
                    position,
                    side * 14
                )

                end = transform(
                    position,
                    side * 21
                )

                pygame.draw.line(
                    screen,
                    BLACK,
                    base,
                    end,
                    max(
                        2,
                        int(3 * scale)
                    )
                )

    # ========================================================
    # МАЧТА
    # ========================================================

    mast_back = transform(
        -5,
        0
    )

    mast_front = transform(
        16,
        0
    )

    pygame.draw.circle(
        screen,
        DARK_BROWN,
        (
            int(mast_back[0]),
            int(mast_back[1])
        ),
        max(
            3,
            int(4 * scale)
        )
    )

    pygame.draw.circle(
        screen,
        DARK_BROWN,
        (
            int(mast_front[0]),
            int(mast_front[1])
        ),
        max(
            2,
            int(3 * scale)
        )
    )

    # ========================================================
    # ПАРУС
    #
    # Вид сверху: парус изображается
    # как светлая полоска поперёк корпуса.
    # ========================================================

    sail_a = transform(
        -7,
        -20
    )

    sail_b = transform(
        -7,
        20
    )

    pygame.draw.line(
        screen,
        DARK_BROWN,
        sail_a,
        sail_b,
        max(
            2,
            int(3 * scale)
        )
    )

    sail_points = [
        transform(-10, -18),
        transform(-2, -13),
        transform(-2, 13),
        transform(-10, 18)
    ]

    pygame.draw.polygon(
        screen,
        sail_color,
        sail_points
    )

    pygame.draw.polygon(
        screen,
        DARK_BROWN,
        sail_points,
        1
    )

    # второй парус
    sail2_points = [
        transform(12, -12),
        transform(19, -8),
        transform(19, 8),
        transform(12, 12)
    ]

    pygame.draw.polygon(
        screen,
        sail_color,
        sail2_points
    )

    # ========================================================
    # ФЛАГ НА КОРМЕ
    # ========================================================

    flag_base = transform(
        -35,
        0
    )

    flag_end = transform(
        -48,
        -8
    )

    flag_tip = transform(
        -48,
        0
    )

    pygame.draw.line(
        screen,
        BLACK,
        flag_base,
        flag_end,
        2
    )

    pygame.draw.polygon(
        screen,
        flag_color,
        [
            flag_end,
            transform(-60, -6),
            flag_tip
        ]
    )

    # носовая точка
    bow = transform(
        43,
        0
    )

    pygame.draw.circle(
        screen,
        GOLD,
        (
            int(bow[0]),
            int(bow[1])
        ),
        max(
            2,
            int(3 * scale)
        )
    )


# ============================================================
# КОРАБЛЬ ИГРОКА
# ============================================================

class PlayerShip(ShipPhysics):

    def __init__(self, x, y):

        super().__init__(
            x,
            y,
            4
        )

        self.health = 100
        self.max_health = 100

        # Раздельная перезарядка бортов
        self.left_reload = 0
        self.right_reload = 0

        self.wake_timer = 0
        self.gun_type = 1

    @property
    def damage(self):
        return 18

    @property
    def cannons_per_side(self):

        return max(
            1,
            self.cannon_count // 2
        )

    def update(
        self,
        dt,
        wind,
        particles
    ):

        keys = pygame.key.get_pressed()

        self.collision_cooldown = max(
            0.0,
            self.collision_cooldown - dt
        )

        base_speed = (
            self.calculate_base_speed()
        )

        max_wind_speed = (
            self.wind_speed(
                wind
            )
        )

        acceleration = (
            self.calculate_acceleration()
        )

        rotation = (
            self.calculate_rotation()
        )

        efficiency = (
            wind.efficiency(
                self.angle
            )
        )

        # ====================================================
        # ПАРУСА
        # ====================================================

        if keys[pygame.K_w]:

            self.speed += (
                acceleration
                * max(
                    0.20,
                    efficiency
                )
                * dt
            )

        elif keys[pygame.K_s]:

            self.speed -= (
                acceleration
                * 0.7
                * dt
            )

        else:

            self.speed *= 0.997

        # Если корабль идёт быстрее,
        # чем позволяет текущий ветер,
        # постепенно теряем скорость.
        if self.speed > max_wind_speed:

            self.speed -= (
                acceleration
                * 0.25
                * dt
            )

        self.speed = clamp(
            self.speed,
            -base_speed * 0.08,
            base_speed
        )

        # ====================================================
        # РУЛЬ
        # ====================================================

        movement_factor = clamp(
            abs(self.speed) / 22,
            0.12,
            1
        )

        if keys[pygame.K_a]:

            self.angle -= (
                rotation
                * movement_factor
                * dt
            )

        if keys[pygame.K_d]:

            self.angle += (
                rotation
                * movement_factor
                * dt
            )

        self.angle %= (
            math.pi * 2
        )

        # ====================================================
        # ДВИЖЕНИЕ
        # ====================================================

        self.x += (
            math.cos(self.angle)
            * self.speed
            * dt
        )

        self.y += (
            math.sin(self.angle)
            * self.speed
            * dt
        )

        self.x = clamp(
            self.x,
            45,
            WORLD_WIDTH - 45
        )

        self.y = clamp(
            self.y,
            45,
            WORLD_HEIGHT - 45
        )

        self.left_reload = max(
            0,
            self.left_reload - dt
        )

        self.right_reload = max(
            0,
            self.right_reload - dt
        )

        # ====================================================
        # КИЛЬВАТЕРНЫЙ СЛЕД
        # ====================================================

        if abs(self.speed) > 12:

            self.wake_timer -= dt

            if self.wake_timer <= 0:

                self.wake_timer = 0.07

                stern_x = (
                    self.x
                    - math.cos(
                        self.angle
                    ) * 36
                )

                stern_y = (
                    self.y
                    - math.sin(
                        self.angle
                    ) * 36
                )

                for side in [-1, 1]:

                    side_angle = (
                        self.angle
                        + side
                        * math.pi / 2
                    )

                    px = (
                        stern_x
                        + math.cos(
                            side_angle
                        ) * 10
                    )

                    py = (
                        stern_y
                        + math.sin(
                            side_angle
                        ) * 10
                    )

                    particles.append(
                        Particle(
                            px,
                            py,
                            -math.cos(
                                self.angle
                            ) * 8
                            + random.uniform(
                                -4,
                                4
                            ),
                            -math.sin(
                                self.angle
                            ) * 8
                            + random.uniform(
                                -4,
                                4
                            ),
                            1.2,
                            FOAM,
                            random.randint(
                                3,
                                6
                            )
                        )
                    )

    def fire(
        self,
        balls,
        particles,
        side,
        player
    ):

        if side == "left":

            if self.left_reload > 0:
                return False, "reload"

        else:

            if self.right_reload > 0:
                return False, "reload"

        count = (
            self.cannons_per_side
        )

        if player.cannonballs < count:

            return False, "ammo"

        player.cannonballs -= count

        if side == "left":

            fire_angle = (
                self.angle
                - math.pi / 2
            )

        else:

            fire_angle = (
                self.angle
                + math.pi / 2
            )

        spacing = 14

        start = -(
            (count - 1)
            * spacing
            / 2
        )

        for i in range(count):

            offset = (
                start
                + i * spacing
            )

            bx = (
                self.x
                + math.cos(
                    self.angle
                ) * offset
                + math.cos(
                    fire_angle
                ) * 20
            )

            by = (
                self.y
                + math.sin(
                    self.angle
                ) * offset
                + math.sin(
                    fire_angle
                ) * 20
            )

            shot_angle = (
                fire_angle
                + random.uniform(
                    -0.035,
                    0.035
                )
            )

            balls.append(
                Cannonball(
                    bx,
                    by,
                    shot_angle,
                    "player",
                    (28, 18, 12)[self.gun_type]
                )
            )
            balls[-1].max_range = (90, 160, 240)[self.gun_type]


            # дым
            for j in range(5):

                particles.append(
                    Particle(
                        bx,
                        by,
                        math.cos(
                            fire_angle
                        ) * random.uniform(
                            10,
                            35
                        )
                        + random.uniform(
                            -10,
                            10
                        ),
                        math.sin(
                            fire_angle
                        ) * random.uniform(
                            10,
                            35
                        )
                        + random.uniform(
                            -10,
                            10
                        ),
                        random.uniform(
                            0.5,
                            1.1
                        ),
                        SMOKE,
                        random.randint(
                            5,
                            10
                        )
                    )
                )

            # вспышка
            particles.append(
                Particle(
                    bx,
                    by,
                    math.cos(
                        fire_angle
                    ) * 15,
                    math.sin(
                        fire_angle
                    ) * 15,
                    0.18,
                    GOLD,
                    9
                )
            )

        if side == "left":

            self.left_reload = 1.7

        else:

            self.right_reload = 1.7

        return True, "ok"

    def draw(self, camera):

        # Чем больше пушек,
        # тем немного крупнее корабль.
        scale = (
            1.12
            + min(
                self.cannon_count,
                20
            ) * 0.012
        )

        draw_detailed_ship(
            camera,
            self.x,
            self.y,
            self.angle,
            self.cannon_count,
            DARK_BROWN,
            SAIL_WHITE,
            RED,
            scale
        )

        sx, sy = camera.world_to_screen(
            self.x,
            self.y
        )

        # здоровье
        pygame.draw.rect(
            screen,
            BLACK,
            (
                int(sx - 35),
                int(sy - 50),
                70,
                7
            )
        )

        pygame.draw.rect(
            screen,
            RED,
            (
                int(sx - 34),
                int(sy - 49),
                68,
                5
            )
        )

        pygame.draw.rect(
            screen,
            GREEN,
            (
                int(sx - 34),
                int(sy - 49),
                int(
                    68
                    * self.health
                    / self.max_health
                ),
                5
            )
        )


# ============================================================
# NPC
# ============================================================

class NPCShip(ShipPhysics):

    def __init__(
        self,
        x,
        y,
        ship_type,
        cannon_count
    ):

        super().__init__(
            x,
            y,
            cannon_count
        )

        self.ship_type = ship_type

        self.target_x = x
        self.target_y = y

        self.reload = random.uniform(
            1,
            4
        )

        self.alive = True

        self.combat_side = random.choice(
            [-1, 1]
        )

        if ship_type == "trader":

            self.name = "Торговец"

            self.health = (
                80
                + cannon_count * 4
            )

            self.hull_color = BROWN
            self.sail_color = SAIL_WHITE
            self.flag_color = GOLD

        elif ship_type == "pirate":

            self.name = "Пират"

            self.health = (
                75
                + cannon_count * 5
            )

            self.hull_color = DARK_BROWN
            self.sail_color = SAIL_PIRATE
            self.flag_color = BLACK

        else:

            self.name = "Красный Джек"

            self.health = 220

            self.hull_color = DARK_RED
            self.sail_color = SAIL_BOSS
            self.flag_color = RED

        self.max_health = (
            self.health
        )

        self.choose_target()

    @property
    def cannons_per_side(self):

        return max(
            1,
            self.cannon_count // 2
        )

    def choose_target(self):

        self.target_x = random.randint(
            250,
            WORLD_WIDTH - 250
        )

        self.target_y = random.randint(
            250,
            WORLD_HEIGHT - 250
        )

    def fire_broadside(
        self,
        balls,
        particles,
        side
    ):

        if self.reload > 0:
            return

        if side == "left":

            fire_angle = (
                self.angle
                - math.pi / 2
            )

        else:

            fire_angle = (
                self.angle
                + math.pi / 2
            )

        count = min(
            self.cannons_per_side,
            5
        )

        spacing = 12

        start = -(
            (count - 1)
            * spacing
            / 2
        )

        for i in range(count):

            offset = (
                start
                + i * spacing
            )

            bx = (
                self.x
                + math.cos(
                    self.angle
                ) * offset
                + math.cos(
                    fire_angle
                ) * 18
            )

            by = (
                self.y
                + math.sin(
                    self.angle
                ) * offset
                + math.sin(
                    fire_angle
                ) * 18
            )

            shot_angle = (
                fire_angle
                + random.uniform(
                    -0.05,
                    0.05
                )
            )

            damage = 7

            if self.ship_type == "boss":
                damage = 10

            balls.append(
                Cannonball(
                    bx,
                    by,
                    shot_angle,
                    "enemy",
                    damage
                )
            )

            for j in range(3):

                particles.append(
                    Particle(
                        bx,
                        by,
                        math.cos(
                            fire_angle
                        ) * random.uniform(
                            10,
                            25
                        )
                        + random.uniform(
                            -8,
                            8
                        ),
                        math.sin(
                            fire_angle
                        ) * random.uniform(
                            10,
                            25
                        )
                        + random.uniform(
                            -8,
                            8
                        ),
                        random.uniform(
                            0.4,
                            0.9
                        ),
                        SMOKE,
                        random.randint(
                            4,
                            8
                        )
                    )
                )

        self.reload = random.uniform(
            2.5,
            3.8
        )

    def update(
        self,
        dt,
        player_ship,
        balls,
        particles,
        wind
    ):

        if not self.alive:
            return

        self.collision_cooldown = max(
            0.0,
            self.collision_cooldown - dt
        )

        self.reload -= dt

        dx = (
            player_ship.x
            - self.x
        )

        dy = (
            player_ship.y
            - self.y
        )

        dist_player = math.hypot(
            dx,
            dy
        )

        aggressive = (
            self.ship_type
            in ("pirate", "boss")
            and dist_player < 700
        )

        if not aggressive:

            if (
                self.ship_type == "trader"
                and dist_player < 260
            ):

                target_angle = math.atan2(
                    self.y - player_ship.y,
                    self.x - player_ship.x
                )

            else:

                if distance(
                    (
                        self.x,
                        self.y
                    ),
                    (
                        self.target_x,
                        self.target_y
                    )
                ) < 100:

                    self.choose_target()

                target_angle = math.atan2(
                    self.target_y - self.y,
                    self.target_x - self.x
                )

        else:

            angle_to_player = math.atan2(
                dy,
                dx
            )

            if dist_player > 370:

                target_angle = (
                    angle_to_player
                )

            elif dist_player < 150:

                target_angle = (
                    angle_to_player
                    + math.pi
                )

            else:

                target_angle = (
                    angle_to_player
                    + self.combat_side
                    * math.pi / 2
                )

        diff = angle_difference(
            target_angle,
            self.angle
        )

        rotation = (
            self.calculate_rotation()
        )

        self.angle += clamp(
            diff,
            -rotation * dt,
            rotation * dt
        )

        self.angle %= (
            math.pi * 2
        )

        max_speed = (
            self.wind_speed(
                wind
            )
        )

        wanted_speed = (
            max_speed * 0.84
        )

        if aggressive:

            wanted_speed = (
                max_speed * 0.95
            )

        acceleration = (
            self.calculate_acceleration()
        )

        if self.speed < wanted_speed:

            self.speed += (
                acceleration * dt
            )

        else:

            self.speed -= (
                acceleration
                * 0.3
                * dt
            )

        self.speed = clamp(
            self.speed,
            0,
            self.calculate_base_speed()
        )

        self.x += (
            math.cos(
                self.angle
            )
            * self.speed
            * dt
        )

        self.y += (
            math.sin(
                self.angle
            )
            * self.speed
            * dt
        )

        self.x = clamp(
            self.x,
            45,
            WORLD_WIDTH - 45
        )

        self.y = clamp(
            self.y,
            45,
            WORLD_HEIGHT - 45
        )

        # стрельба
        if (
            aggressive
            and dist_player < 430
            and self.reload <= 0
        ):

            angle_to_player = math.atan2(
                player_ship.y - self.y,
                player_ship.x - self.x
            )

            left_angle = (
                self.angle
                - math.pi / 2
            )

            right_angle = (
                self.angle
                + math.pi / 2
            )

            left_error = abs(
                angle_difference(
                    angle_to_player,
                    left_angle
                )
            )

            right_error = abs(
                angle_difference(
                    angle_to_player,
                    right_angle
                )
            )

            firing_arc = math.radians(
                30
            )

            if left_error < firing_arc:

                self.fire_broadside(
                    balls,
                    particles,
                    "left"
                )

            elif right_error < firing_arc:

                self.fire_broadside(
                    balls,
                    particles,
                    "right"
                )

    def draw(self, camera):

        sx, sy = camera.world_to_screen(
            self.x,
            self.y
        )

        if (
            sx < -100
            or sx > screen.get_width() + 100
            or sy < -100
            or sy > screen.get_height() + 100
        ):
            return

        scale = 0.95

        if self.ship_type == "boss":
            scale = 1.28

        draw_detailed_ship(
            camera,
            self.x,
            self.y,
            self.angle,
            self.cannon_count,
            self.hull_color,
            self.sail_color,
            self.flag_color,
            scale
        )

        # здоровье
        width = 54

        if self.ship_type == "boss":
            width = 75

        pygame.draw.rect(
            screen,
            BLACK,
            (
                int(sx - width / 2),
                int(sy - 48),
                width,
                6
            )
        )

        pygame.draw.rect(
            screen,
            GREEN,
            (
                int(sx - width / 2 + 1),
                int(sy - 47),
                int(
                    (width - 2)
                    * self.health
                    / self.max_health
                ),
                4
            )
        )

        if self.ship_type == "boss":

            draw_centered(
                "КРАСНЫЙ ДЖЕК",
                sx,
                sy - 68,
                GOLD,
                tiny_font
            )


# ============================================================
# ИГРА
# ============================================================

class Game:

    def __init__(self):

        self.mode = "city"

        self.sound = SoundManager()
        self.sound.play_music("city")

        self.player = Player()

        # v0.16-0.18: полноценные комнаты, жители и диалоги.
        self.quest_rewarded = False
        self.room_kind = None
        self.room_return = (530, 450)
        self.town_time = 0.0
        self.dialogue = None
        self.town_people = [
            {"name": "Матрос", "x": 255.0, "y": 354.0, "base": 255, "phase": 0.0,
             "speech": "Слыхал? У острова Черепа видели чёрные паруса."},
            {"name": "Рыбак", "x": 812.0, "y": 359.0, "base": 812, "phase": 1.7,
             "speech": "Рыба сегодня не клюёт. Ветер переменился."},
            {"name": "Торговка", "x": 385.0, "y": 452.0, "base": 385, "phase": 3.0,
             "speech": "На рынке лучшие припасы во всём Карибском море!"},
            {"name": "Старый пират", "x": 725.0, "y": 362.0, "base": 725, "phase": 4.4,
             "speech": "Не доверяй спокойной воде, капитан."},
        ]
        self.room_people = {
            "tavern": ("Трактирщик", "Контракт на Красного Джека ждёт смельчака."),
            "bank": ("Банкир", "Ваше золото в безопасности."),
            "shop": ("Торговец", "Ядра и припасы по честной цене!"),
            "shipyard": ("Корабел", "Проверим корпус и орудия?"),
        }

        self.city_minutes = 8 * 60
        self.journal_visible = False
        self.room_objects = {
            "tavern": [(320, 470, "Бочка", "Пахнет ромом и дубовой древесиной."),
                       (760, 480, "Стол", "На столе лежит морская карта.")],
            "bank": [(112, 435, "Сейф", "Массивный сейф с надёжным замком."),
                     (925, 475, "Золото", "Слитки аккуратно сложены на полке.")],
            "shop": [(140, 435, "Припасы", "Здесь продают провизию и ядра."),
                     (945, 435, "Сундук", "Заперт на крепкий замок.")],
            "shipyard": [(135, 440, "Верстак", "Инструменты корабельного мастера."),
                         (955, 440, "Канаты", "Прочные корабельные тросы.")]
        }
        self.conversations = {}
        self.save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "groza_morey_save.json")

        self.home_port_x = 900
        self.home_port_y = 900

        self.ship = PlayerShip(
            self.home_port_x,
            self.home_port_y + 300
        )

        self.camera = Camera()
        self.show_range = True
        self.ship_view = False  # F: обычный вид / корабль носом вверх
        self.rotating_world_surface = None

        self.wind = Wind()

        self.particles = []

        # ====================================================
        # ГОРОД
        # ====================================================

        self.buildings = [

            Building(
                65,
                125,
                175,
                120,
                "Таверна",
                (147, 89, 52)
            ),

            Building(
                300,
                125,
                160,
                120,
                "Банк",
                (112, 110, 105)
            ),

            Building(
                630,
                125,
                170,
                120,
                "Лавка",
                (151, 103, 59)
            ),

            Building(
                860,
                125,
                170,
                120,
                "Верфь",
                (93, 104, 105)
            )
        ]

        # ====================================================
        # ОСТРОВА
        # ====================================================

        self.islands = [

            Island(
                900,
                900,
                230,
                "Порт-Ройал",
                True
            ),

            Island(
                3900,
                950,
                260,
                "Тортуга",
                True
            ),

            Island(
                4050,
                3850,
                320,
                "Гавана",
                True
            ),

            Island(
                1100,
                3950,
                250,
                "Санта-Лючия",
                True
            ),

            Island(
                2500,
                2300,
                180,
                "Остров Черепа",
                False
            ),

            Island(
                3100,
                1500,
                130,
                "Змеиный остров",
                False
            ),

            Island(
                1800,
                3100,
                150,
                "Коралловый остров",
                False
            )
        ]

        self.npc_ships = []

        self.create_npc_fleet()

        self.balls = []
        self.loot = []

        self.message = ""
        self.message_timer = 0

        self.quest_active = False
        self.boss_killed = False

        # Порт, в котором сейчас находится игрок.
        self.current_port = "Порт-Ройал"

    # ========================================================
    # NPC
    # ========================================================

    def create_npc_fleet(self):

        for i in range(9):

            self.npc_ships.append(
                NPCShip(
                    random.randint(
                        400,
                        4600
                    ),
                    random.randint(
                        400,
                        4600
                    ),
                    "trader",
                    random.choice(
                        [2, 4, 6]
                    )
                )
            )

        for i in range(7):

            self.npc_ships.append(
                NPCShip(
                    random.randint(
                        500,
                        4500
                    ),
                    random.randint(
                        500,
                        4500
                    ),
                    "pirate",
                    random.choice(
                        [4, 6, 8, 10]
                    )
                )
            )

        self.npc_ships.append(
            NPCShip(
                3200,
                2600,
                "boss",
                12
            )
        )

    # ========================================================
    # СООБЩЕНИЯ
    # ========================================================

    def show_message(
        self,
        text,
        duration=2.5
    ):

        self.message = text
        self.message_timer = duration

    # ========================================================
    # ГОРОД
    # ========================================================

    def enter_room(self, kind):
        self.room_return = (self.player.x, self.player.y)
        self.room_kind = kind
        self.player.x, self.player.y = WIDTH / 2, HEIGHT - 175
        self.dialogue = None
        self.mode = "room"
        self.show_message("Подойдите к персонажу и нажмите E.")

    def leave_room(self):
        self.mode = "city"
        self.player.x, self.player.y = self.room_return
        self.dialogue = None
        self.room_kind = None

    def update_room(self, dt):
        self.city_minutes = (self.city_minutes + dt * 1.5) % 1440
        # Не даём игроку выходить за стены и проходить через стойку.
        walls = [
            pygame.Rect(0, 0, WIDTH, 240),
            pygame.Rect(0, 0, 48, HEIGHT),
            pygame.Rect(WIDTH - 48, 0, 48, HEIGHT),
            pygame.Rect(0, HEIGHT - 85, WIDTH, 85),
        ]
        self.player.update(dt, walls)
        if self.player.is_moving:
            self.sound.step()
        if self.message_timer > 0:
            self.message_timer -= dt

    def interact_room(self):
        px = self.player.x + self.player.w / 2
        py = self.player.y + self.player.h / 2
        for x, y, label, description in self.room_objects.get(self.room_kind, []):
            if math.hypot(px-x, py-y) < 68:
                self.show_message(label + ": " + description, 5)
                return
        # NPC стоит перед стойкой, поэтому к нему можно подойти.
        target_x, target_y = WIDTH // 2, 320
        dist = math.hypot(self.player.x + self.player.w / 2 - target_x,
                          self.player.y + self.player.h / 2 - target_y)
        if dist < 100:
            self.dialogue = self.room_people[self.room_kind][1]
            self.mode = self.room_kind  # Существующее функциональное меню.
        else:
            self.show_message("Подойдите к хозяину помещения (в центре).")

    def draw_person(self, x, y, color, name=None, scale=1):
        x, y = int(x), int(y)
        pygame.draw.ellipse(screen, (31, 30, 29),
                            (x-14, y+17, 28, 8))
        pygame.draw.line(screen, (46, 38, 36), (x-6, y+6),
                         (x-8, y+21), 5)
        pygame.draw.line(screen, (46, 38, 36), (x+6, y+6),
                         (x+8, y+21), 5)
        pygame.draw.rect(screen, color, (x-11, y-19, 22, 28),
                         border_radius=5)
        pygame.draw.circle(screen, (215, 167, 121), (x, y-27), 11)
        pygame.draw.ellipse(screen, (47, 36, 32), (x-14, y-39, 28, 12))
        pygame.draw.rect(screen, (77, 53, 34), (x-9, y-44, 18, 10))
        if name:
            draw_centered(name, x, y-67, WHITE, small_font)

    def draw_day_night(self):
        hour = self.city_minutes / 60
        # Вечер и ночь затемняют город; фонари остаются видимыми.
        darkness = 0
        if hour >= 19:
            darkness = min(115, int((hour-19)*29))
        elif hour < 6:
            darkness = 105
        elif hour < 8:
            darkness = int((8-hour)*52)
        if darkness:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((12, 24, 56, darkness))
            screen.blit(overlay, (0, 0))
        clock_text = f"{int(hour):02d}:{int(self.city_minutes)%60:02d}"
        draw_centered(clock_text, WIDTH-64, HUD_HEIGHT+12, GOLD, small_font)

    def draw_journal(self):
        if not self.journal_visible:
            return
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((7, 13, 23, 194))
        screen.blit(overlay, (0, 0))
        panel = pygame.Rect(190, 100, WIDTH-380, HEIGHT-200)
        pygame.draw.rect(screen, (64, 47, 34), panel, border_radius=14)
        pygame.draw.rect(screen, GOLD, panel, 3, border_radius=14)
        draw_centered("СУДОВОЙ ЖУРНАЛ", WIDTH//2, 132, GOLD, big_font)
        if self.quest_rewarded:
            quest = "Красный Джек побеждён. Награда получена."
        elif self.boss_killed:
            quest = "Красный Джек побеждён. Вернитесь в таверну."
        elif self.quest_active:
            quest = "Контракт: уничтожить корабль Красного Джека."
        else:
            quest = "Посетите таверну и узнайте о контрактах."
        entries = [
            "Задание: " + quest,
            "Текущий порт: " + self.current_port,
            f"Золото: {self.player.gold} | В банке: {self.player.bank_gold}",
            f"Пушечных ядер: {self.player.cannonballs}",
            "F5 - сохранить игру, F9 - загрузить.",
            "J / ESC - закрыть журнал."
        ]
        for i, line in enumerate(entries):
            img = small_font.render(line, True, WHITE)
            screen.blit(img, (225, 212+i*48))

    def save_game(self):
        data = {
            "version": 23, "gold": self.player.gold,
            "bank_gold": self.player.bank_gold,
            "cannonballs": self.player.cannonballs,
            "player_x": self.player.x, "player_y": self.player.y,
            "ship_x": self.ship.x, "ship_y": self.ship.y,
            "ship_angle": self.ship.angle,
            "current_port": self.current_port,
            "quest_active": self.quest_active,
            "boss_killed": self.boss_killed,
            "quest_rewarded": self.quest_rewarded,
            "city_minutes": self.city_minutes,
            "mode": self.mode if self.mode in ("city", "sea") else "city"
        }
        try:
            with open(self.save_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.show_message("Игра сохранена (F5).", 4)
        except (OSError, TypeError) as exc:
            self.show_message("Ошибка сохранения: " + str(exc), 5)

    def load_game(self):
        try:
            with open(self.save_path, encoding="utf-8") as f:
                data = json.load(f)
            if data.get("version") != 23:
                raise ValueError("Неподдерживаемая версия сохранения")
            for key in ("gold", "bank_gold", "cannonballs"):
                setattr(self.player, key, max(0, int(data[key])))
            self.player.x = float(data["player_x"])
            self.player.y = float(data["player_y"])
            self.ship.x = float(data["ship_x"])
            self.ship.y = float(data["ship_y"])
            self.ship.angle = float(data["ship_angle"])
            self.ship.speed = 0
            self.current_port = str(data["current_port"])
            for key in ("quest_active", "boss_killed", "quest_rewarded"):
                setattr(self, key, bool(data[key]))
            self.city_minutes = float(data["city_minutes"]) % 1440
            self.mode = data["mode"] if data["mode"] in ("sea","city") else "city"
            self.room_kind = None
            self.journal_visible = False
            self.show_message("Игра загружена (F9).", 4)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            self.show_message("Ошибка загрузки: " + str(exc), 5)

    def draw_room(self):
        title = {
            "tavern": "ТАВЕРНА", "bank": "БАНК",
            "shop": "ТОРГОВАЯ ЛАВКА", "shipyard": "КОРОЛЕВСКАЯ ВЕРФЬ"
        }[self.room_kind]
        self.draw_room_art(title)
        # Пол и предметы переднего плана, с которыми можно ориентироваться.
        for x in range(55, WIDTH-50, 85):
            pygame.draw.line(screen, (125, 90, 61),
                             (x, 404), (x-35, HEIGHT-87), 2)
        # Небольшая стойка по бокам, оставляем проход к NPC.
        for x in (240, 665):
            pygame.draw.rect(screen, (78, 48, 31), (x, 324, 190, 45),
                             border_radius=7)
            pygame.draw.rect(screen, (162, 111, 64), (x, 319, 190, 14),
                             border_radius=4)
        who = self.room_people[self.room_kind][0]
        self.draw_person(WIDTH//2, 320, (83, 110, 95), who)
        if self.room_kind == "tavern":
            self.draw_person(345, 472, (127, 68, 57), "Моряк")
            self.draw_person(765, 483, (64, 94, 119), "Посетитель")
        for x, y, label, _ in self.room_objects.get(self.room_kind, []):
            pygame.draw.circle(screen, (224, 184, 88), (x, y-24), 5)
            draw_centered(label, x, y-48, WHITE, small_font)
        self.player.draw()
        self.draw_hud()
        draw_centered(title, WIDTH//2, 94, GOLD, big_font)
        self.draw_bottom("WASD - ходить   E - поговорить / открыть услуги   ESC - выйти")
        self.draw_message()

    def interact_town_person(self):
        px, py = self.player.x + self.player.w/2, self.player.y + self.player.h/2
        for person in self.town_people:
            if math.hypot(px-person["x"], py-person["y"]) < 65:
                name = person["name"]
                count = self.conversations.get(name, 0)
                variants = {
                    "Матрос": ["Слыхал? У острова Черепа видели чёрные паруса.",
                               "Пушки ближнего боя хороши в тесной бухте."],
                    "Рыбак": ["Рыба сегодня не клюёт. Ветер переменился.",
                               "Берегись рифов у островов!"],
                    "Торговка": ["На рынке лучшие припасы во всём Карибском море!",
                                "Купи ядра перед долгим плаванием."],
                    "Старый пират": ["Не доверяй спокойной воде, капитан.",
                                    "Тот, кто знает ветер, побеждает в море."]
                }
                self.show_message(name + ": " + variants[name][count % 2], 5)
                self.conversations[name] = count + 1
                return True
        return False

    def update_city(self, dt):

        obstacles = [
            b.rect
            for b in self.buildings
        ]

        self.player.update(
            dt,
            obstacles
        )

        if self.player.is_moving:
            self.sound.step()

        self.town_time += dt
        self.city_minutes = (self.city_minutes + dt * 1.5) % 1440
        for person in self.town_people:
            person["x"] = person["base"] + 35 * math.sin(
                self.town_time * .55 + person["phase"])

        self.sound.update_ambient("city", self.wind.strength)
        self.sound.play_music("city")

        if self.message_timer > 0:
            self.message_timer -= dt

    def interact_city(self):

        if self.interact_town_person():
            return

        for building in self.buildings:

            area = building.rect.inflate(
                60,
                60
            )

            if not area.colliderect(
                self.player.rect
            ):
                continue

            if building.name == "Таверна":
                self.enter_room("tavern")

            elif building.name == "Банк":
                self.enter_room("bank")

            elif building.name == "Лавка":
                self.enter_room("shop")

            elif building.name == "Верфь":
                self.enter_room("shipyard")

            return

        port = pygame.Rect(
            WIDTH // 2 - 90,
            HEIGHT - 155,
            180,
            110
        )

        if self.player.rect.colliderect(
            port
        ):

            self.mode = "sea"
            self.sound.play_music("sea")

            port_island = next(
                (i for i in self.islands if i.name == self.current_port),
                self.islands[0]
            )

            self.ship.x = port_island.x + port_island.radius + 125
            self.ship.y = port_island.y
            self.ship.angle = math.pi
            self.ship.speed = 0

    def draw_city(self):

        # Небо/земля Порт-Ройала.
        screen.fill((210, 188, 139))

        # Зелёные окраины.
        pygame.draw.rect(screen, (80, 130, 67), (0, HUD_HEIGHT, WIDTH, 78))
        pygame.draw.rect(screen, (99, 145, 76), (0, 405, WIDTH, 95))

        # Главная мощёная улица.
        pygame.draw.rect(screen, ROAD, (0, 292, WIDTH, 118))
        pygame.draw.rect(screen, ROAD, (WIDTH // 2 - 62, HUD_HEIGHT, 124, HEIGHT - HUD_HEIGHT))

        # Каменная мостовая.
        for yy in range(302, 400, 24):
            offset = 0 if (yy // 24) % 2 == 0 else 24
            for xx in range(-20 + offset, WIDTH, 48):
                pygame.draw.ellipse(screen, (126, 113, 91), (xx, yy, 34, 13), 1)

        for yy in range(HUD_HEIGHT + 10, HEIGHT - 115, 30):
            for xx in range(WIDTH // 2 - 50, WIDTH // 2 + 50, 34):
                pygame.draw.ellipse(screen, (128, 113, 91), (xx, yy, 25, 11), 1)

        # Мелкие дома на заднем плане.
        small_houses = [
            (18, 76, 38, 45, (168, 128, 78)),
            (250, 82, 42, 42, (191, 155, 99)),
            (475, 80, 48, 44, (159, 116, 74)),
            (810, 82, 42, 43, (188, 148, 91)),
            (1040, 77, 45, 48, (155, 111, 72)),
        ]
        for hx, hy, hw, hh, hc in small_houses:
            pygame.draw.rect(screen, hc, (hx, hy, hw, hh))
            pygame.draw.polygon(screen, DARK_BROWN,
                                [(hx - 4, hy), (hx + hw // 2, hy - 18), (hx + hw + 4, hy)])
            pygame.draw.rect(screen, (92, 62, 38), (hx + hw // 2 - 5, hy + hh - 18, 10, 18))

        # Бочки, ящики и портовый груз.
        for bx, by in [(85, 445), (120, 462), (915, 448), (955, 465), (1000, 440)]:
            pygame.draw.ellipse(screen, DARK_BROWN, (bx, by, 22, 9))
            pygame.draw.rect(screen, BROWN, (bx, by + 4, 22, 20))
            pygame.draw.ellipse(screen, LIGHT_WOOD, (bx, by + 18, 22, 9), 2)

        for bx, by in [(170, 438), (198, 451), (850, 444)]:
            pygame.draw.rect(screen, LIGHT_WOOD, (bx, by, 27, 25))
            pygame.draw.rect(screen, DARK_BROWN, (bx, by, 27, 25), 2)
            pygame.draw.line(screen, DARK_BROWN, (bx, by), (bx + 27, by + 25), 1)

        # Фонари вдоль дороги.
        for lx in [270, 470, 630, 830]:
            pygame.draw.line(screen, DARK_BROWN, (lx, 278), (lx, 320), 4)
            pygame.draw.rect(screen, GOLD, (lx - 5, 274, 10, 10))
            pygame.draw.rect(screen, BLACK, (lx - 6, 273, 12, 12), 1)

        # Пальмы.
        for px, py in [(35, 470), (1040, 470)]:
            pygame.draw.line(screen, DARK_BROWN, (px, py + 55), (px + 5, py), 7)
            for a in [-2.8, -2.2, -1.5, -0.8, -0.2]:
                pygame.draw.line(screen, DARK_GREEN, (px + 5, py),
                                 (int(px + 5 + math.cos(a) * 28),
                                  int(py + math.sin(a) * 17)), 6)

        # Море и берег.
        pygame.draw.rect(screen, SAND, (0, HEIGHT - 128, WIDTH, 22))
        pygame.draw.rect(screen, SEA, (0, HEIGHT - 106, WIDTH, 56))
        for x in range(0, WIDTH, 70):
            pygame.draw.arc(screen, SEA_LIGHT, (x, HEIGHT - 96, 45, 18), 0, math.pi, 2)

        # Большой деревянный пирс.
        pier = pygame.Rect(WIDTH // 2 - 82, HEIGHT - 176, 164, 126)
        pygame.draw.rect(screen, WOOD, pier)
        pygame.draw.rect(screen, DARK_BROWN, pier, 4)
        for y in range(pier.top + 8, pier.bottom, 16):
            pygame.draw.line(screen, DARK_BROWN, (pier.left, y), (pier.right, y), 2)
        for x in [pier.left + 10, pier.right - 10]:
            pygame.draw.line(screen, DARK_BROWN, (x, pier.top), (x, pier.bottom + 15), 6)

        # Портовая вывеска.
        pygame.draw.rect(screen, DARK_BROWN, (WIDTH // 2 - 92, 255, 184, 34), border_radius=4)
        draw_centered(self.current_port.upper(), WIDTH // 2, 261, GOLD, small_font)

        # Архитектурные детали города: мощёные переулки, зелень и декор.
        for x in range(18, WIDTH, 42):
            for y in (302, 337, 374):
                pygame.draw.line(screen,(178,163,134),
                                 (x+(y%3)*6,y),(x+24+(y%3)*6,y),1)

        for x,y in ((25,253),(220,258),(490,252),(745,254),
                    (1038,257),(190,475),(830,476)):
            draw_game_palm(screen,x,y,.9)

        # Портовые домики вдоль побережья.
        for x,y,k in ((18,417,.85),(250,418,.72),
                      (735,417,.72),(1010,412,.85)):
            draw_game_house(screen,x,y,k)

        # Флагштоки, рыбацкие сети и груз на пристани.
        for x in (350,740):
            pygame.draw.line(screen,(80,55,35),(x,457),(x,400),3)
            pygame.draw.polygon(screen,(165,51,41),
                                [(x,401),(x+23,408),(x,416)])
        for x,y in ((408,463),(650,462),(455,478)):
            pygame.draw.rect(screen,(139,102,63),(x,y,25,19))
            pygame.draw.rect(screen,(78,57,39),(x,y,25,19),2)
            pygame.draw.line(screen,(78,57,39),(x,y),(x+25,y+19),1)

        for building in self.buildings:
            building.draw()
        for person in self.town_people:
            self.draw_person(person["x"], person["y"], (85, 109, 120),
                             person["name"])
        self.player.draw()
        self.draw_hud()
        self.draw_bottom("WASD - ходить    E - здания / разговор / море")
        self.draw_message()

    # ========================================================
    # ЗДАНИЯ
    # ========================================================

    def draw_room_art(self, title):
        """Тематический интерьер, создаётся один раз на каждый тип помещения."""
        if not hasattr(self, "_room_art_cache"):
            self._room_art_cache = {}
        if title not in self._room_art_cache:
            surf = pygame.Surface((WIDTH, HEIGHT)).convert()
            rng = random.Random(sum(ord(c) for c in title))
            tavern = "ТАВЕРНА" in title
            bank = "БАНК" in title
            shop = "ЛАВКА" in title
            yard = "ВЕРФЬ" in title
            wall = (103, 71, 51) if tavern else ((108, 101, 86) if bank else
                   ((126, 96, 66) if shop else (83, 97, 101)))
            surf.fill(wall)
            # Перспектива: задняя стена, балки и дощатый пол.
            pygame.draw.rect(surf, (38, 35, 33), (0, 0, WIDTH, 76))
            for x in range(0, WIDTH, 118):
                pygame.draw.rect(surf, (59, 40, 30), (x, 48, 15, 400))
                pygame.draw.line(surf, (155, 113, 75), (x+4, 75), (x+4, 440), 2)
            pygame.draw.polygon(surf, (80, 56, 39) if not yard else (72, 79, 77),
                                [(0, 400), (WIDTH, 400), (WIDTH, HEIGHT), (0, HEIGHT)])
            for y in range(409, HEIGHT, 27):
                pygame.draw.line(surf, (39, 35, 33), (0, y), (WIDTH, y), 3)
            for x in range(0, WIDTH, 95):
                pygame.draw.line(surf, (139, 99, 61), (x, 402), (x-55, HEIGHT), 2)
            # Окна и золотистый свет.
            for x in (58, WIDTH-177):
                pygame.draw.rect(surf, (57, 40, 32), (x, 119, 117, 177), border_radius=8)
                pygame.draw.rect(surf, (85, 155, 164), (x+11, 130, 95, 152))
                pygame.draw.line(surf, (239, 204, 141), (x+58, 130), (x+58, 282), 8)
                pygame.draw.line(surf, (239, 204, 141), (x+10, 208), (x+105, 208), 7)
                pygame.draw.rect(surf, (180, 135, 84), (x, 286, 117, 14))
            # Настенные фонари.
            for x in (206, WIDTH-216):
                pygame.draw.circle(surf, (169, 116, 59), (x, 135), 31)
                pygame.draw.polygon(surf, (53, 40, 34),
                                    [(x-12, 118), (x+12, 118), (x+16, 161), (x-16, 161)])
                pygame.draw.ellipse(surf, (255, 207, 96), (x-7, 129, 14, 22))
            if tavern:
                # Бочки, стойка, бутылки, вывеска.
                pygame.draw.rect(surf, (93, 52, 33), (0, 334, WIDTH, 79))
                for x in (18, 84, WIDTH-113, WIDTH-48):
                    pygame.draw.ellipse(surf, (103, 58, 34), (x, 465, 47, 80))
                    for y in (477, 528):
                        pygame.draw.line(surf, (175, 151, 105), (x, y), (x+46, y), 5)
                for x in range(16, 195, 34):
                    pygame.draw.rect(surf, (38, 92, 67), (x, 310, 15, 32))
                    pygame.draw.ellipse(surf, (170, 126, 70), (x+2, 307, 11, 5))
            elif bank:
                # Сейф, золотые слитки, весы.
                pygame.draw.rect(surf, (57, 62, 64), (22, 339, 160, 172), border_radius=8)
                pygame.draw.rect(surf, (143, 148, 143), (37, 354, 130, 138), 6)
                pygame.draw.circle(surf, (191, 166, 94), (102, 422), 35, 6)
                for x in (866, 917, 968):
                    for y in (445, 462):
                        pygame.draw.polygon(surf, (232, 185, 64),
                                            [(x, y+15), (x+45, y+15),
                                             (x+36, y), (x+8, y)])
            elif shop:
                # Стеллажи с товарами, мешки, сундуки.
                for x in (7, 875):
                    pygame.draw.rect(surf, (92, 55, 34), (x, 310, 213, 200))
                    for y in (337, 402, 469):
                        pygame.draw.rect(surf, (166, 115, 66), (x, y, 213, 12))
                    for i in range(7):
                        bx=x+13+i*27
                        pygame.draw.rect(surf, rng.choice([(111, 68, 44),
                                         (61, 100, 73), (144, 104, 52)]),
                                         (bx, 361+(i%2)*66, 20, 33))
                pygame.draw.rect(surf, (114, 79, 46), (50, 520, 125, 64))
            elif yard:
                # Верфь: верстаки, канаты, инструмент, якоря.
                pygame.draw.rect(surf, (95, 60, 37), (10, 455, 210, 35))
                pygame.draw.rect(surf, (95, 60, 37), (880, 455, 210, 35))
                for x in (44, 102, 927, 993):
                    pygame.draw.circle(surf, (151, 112, 67), (x, 390), 28, 7)
                    pygame.draw.circle(surf, (151, 112, 67), (x, 390), 7)
                for x in (72, 953):
                    pygame.draw.line(surf, (180, 188, 184), (x, 296), (x, 360), 7)
                    pygame.draw.arc(surf, (180, 188, 184), (x-26, 333, 52, 49),
                                    0, math.pi, 6)
            self._room_art_cache[title] = surf
        screen.blit(self._room_art_cache[title], (0, 0))

    def draw_building_screen(
        self,
        title,
        lines
    ):

        self.draw_room_art(title)

        self.draw_hud()

        draw_centered(
            title,
            WIDTH // 2,
            105,
            GOLD,
            big_font
        )

        draw_panel(
            pygame.Rect(
                180,
                165,
                740,
                345
            ),
            (52, 42, 34),
            LIGHT_WOOD
        )

        for i, line in enumerate(lines):

            draw_text(
                line,
                240,
                205 + i * 45,
                WHITE
            )

        self.draw_bottom(
            "Цифры - действие     ESC - выйти"
        )

        self.draw_message()

    def draw_tavern(self):

        if self.boss_killed:

            lines = [
                "Трактирщик:",
                "Красный Джек отправился на дно!",
                "Сегодня весь порт пьёт за ваш счёт.",
                "[1] Получить награду 500 зол."
            ]

        elif self.quest_rewarded:

            lines = [
                "Трактирщик:",
                "Красный Джек побеждён. Награда выплачена.",
                "Спасибо за помощь торговым путям!"
            ]

        elif self.quest_active:

            lines = [
                "Трактирщик:",
                "Красный Джек всё ещё где-то в море.",
                "Ищи его далеко к юго-востоку.",
                "За его голову обещано 500 зол."
            ]

        else:

            lines = [
                "Трактирщик:",
                "Красный Джек терроризирует торговые пути.",
                "Говорят, на его корабле двенадцать пушек.",
                "[1] Взять контракт — награда 500 зол."
            ]

        self.draw_building_screen(
            "ТАВЕРНА",
            lines
        )

    def draw_shop(self):

        self.draw_building_screen(
            "ТОРГОВАЯ ЛАВКА",
            [
                f"В трюме: {self.player.cannonballs} ядер",
                "[1] 10 ядер — 30 зол.",
                "[2] 30 ядер — 80 зол.",
                "[3] 100 ядер — 240 зол."
            ]
        )

    def draw_bank(self):

        self.draw_building_screen(
            "БАНК",
            [
                f"При себе: {self.player.gold} зол.",
                f"В банке: {self.player.bank_gold} зол.",
                "[1] Положить 100 зол.",
                "[2] Снять 100 зол."
            ]
        )

    def draw_shipyard(self):

        next_speed = clamp(
            106
            - (
                self.ship.cannon_count + 2
            ) * 3,
            45,
            100
        )

        self.draw_building_screen(
            "КОРОЛЕВСКАЯ ВЕРФЬ",
            [
                f"Орудий: {self.ship.cannon_count} ({self.ship.cannons_per_side} на борт)",
                f"Базовая скорость: {self.ship.calculate_base_speed():.0f}",
                f"После +2 пушек: {next_speed:.0f}",
                "[1] Установить 2 пушки — 250 зол.",
                "[2] Снять 2 пушки",
                "[3] Полностью отремонтировать корабль"
            ]
        )

    # ========================================================
    # ЭФФЕКТ ПОПАДАНИЯ
    # ========================================================

    def hit_effect(self, x, y):

        for i in range(10):

            angle = random.uniform(
                0,
                math.pi * 2
            )

            speed = random.uniform(
                20,
                80
            )

            self.particles.append(
                Particle(
                    x,
                    y,
                    math.cos(angle) * speed,
                    math.sin(angle) * speed,
                    random.uniform(
                        0.4,
                        0.9
                    ),
                    LIGHT_WOOD,
                    random.randint(
                        3,
                        7
                    ),
                    "wood"
                )
            )

        for i in range(5):

            self.particles.append(
                Particle(
                    x,
                    y,
                    random.uniform(
                        -20,
                        20
                    ),
                    random.uniform(
                        -20,
                        20
                    ),
                    random.uniform(
                        0.4,
                        0.8
                    ),
                    SMOKE,
                    random.randint(
                        4,
                        8
                    )
                )
            )

    # ========================================================
    # СТОЛКНОВЕНИЯ
    # ========================================================

    def damage_npc_from_collision(self, npc, damage):

        if not npc.alive or damage <= 0:
            return

        npc.health -= damage
        self.hit_effect(npc.x, npc.y)

        if npc.health <= 0:
            npc.alive = False
            self.loot.append(Loot(npc.x, npc.y))

            if npc.ship_type == "boss":
                self.boss_killed = True
                self.quest_active = False
                self.show_message("КРАСНЫЙ ДЖЕК ПОТОПЛЕН!", 4)
            else:
                self.show_message(f"{npc.name} разбит при столкновении!", 2.5)

    def resolve_island_collision(self, ship, island, is_player=False):

        # Остров нарисован эллипсом, поэтому и физическая граница
        # повторяет форму берега. Радиус корабля расширяет эту границу.
        rx = island.radius + ship.collision_radius
        ry = island.radius * 0.65 + ship.collision_radius

        dx = ship.x - island.x
        dy = ship.y - island.y

        norm = (dx / rx) ** 2 + (dy / ry) ** 2

        if norm >= 1.0:
            return False

        old_speed = abs(ship.speed)

        # Если центры почти совпали, задаём безопасное направление наружу.
        if abs(dx) < 0.001 and abs(dy) < 0.001:
            dx = 1.0
            dy = 0.0

        scale = 1.0 / max(math.sqrt(norm), 0.001)
        ship.x = island.x + dx * scale
        ship.y = island.y + dy * scale

        # Удар о берег гасит ход и слегка отбрасывает корабль.
        ship.speed *= -0.18

        if old_speed > 24 and ship.collision_cooldown <= 0:
            damage = int(clamp((old_speed - 18) * 0.18, 2, 18))
            ship.health -= damage
            ship.collision_cooldown = 0.8
            self.sound.play_spatial(
                "collision", ship.x, ship.y,
                self.ship.x, self.ship.y, 800, 0.65
            )
            self.hit_effect(ship.x, ship.y)

            if is_player:
                self.show_message(
                    f"Удар о берег! Корпус -{damage}",
                    1.8
                )

        return True

    def resolve_ship_collision(self, ship_a, ship_b, player_a=False, player_b=False):

        dx = ship_b.x - ship_a.x
        dy = ship_b.y - ship_a.y
        dist = math.hypot(dx, dy)
        min_dist = ship_a.collision_radius + ship_b.collision_radius

        if dist >= min_dist:
            return False

        if dist < 0.001:
            nx, ny = 1.0, 0.0
            dist = 0.001
        else:
            nx, ny = dx / dist, dy / dist

        overlap = min_dist - dist
        mass_a = ship_a.ship_mass()
        mass_b = ship_b.ship_mass()
        total_mass = mass_a + mass_b

        # Более лёгкий корабль отталкивается сильнее.
        ship_a.x -= nx * overlap * (mass_b / total_mass)
        ship_a.y -= ny * overlap * (mass_b / total_mass)
        ship_b.x += nx * overlap * (mass_a / total_mass)
        ship_b.y += ny * overlap * (mass_a / total_mass)

        va_x, va_y = ship_a.velocity()
        vb_x, vb_y = ship_b.velocity()
        relative_normal_speed = abs(
            (va_x - vb_x) * nx + (va_y - vb_y) * ny
        )

        # После контакта корабли теряют часть скорости.
        ship_a.speed *= 0.45
        ship_b.speed *= 0.45

        can_damage = (
            relative_normal_speed > 22
            and ship_a.collision_cooldown <= 0
            and ship_b.collision_cooldown <= 0
        )

        if can_damage:
            base_damage = clamp((relative_normal_speed - 16) * 0.16, 2, 24)

            damage_a = int(max(1, base_damage * mass_b / mass_a))
            damage_b = int(max(1, base_damage * mass_a / mass_b))

            ship_a.collision_cooldown = 0.9
            ship_b.collision_cooldown = 0.9

            self.sound.play_spatial(
                "collision",
                (ship_a.x + ship_b.x) / 2,
                (ship_a.y + ship_b.y) / 2,
                self.ship.x, self.ship.y,
                900, 0.9
            )

            if isinstance(ship_a, NPCShip):
                self.damage_npc_from_collision(ship_a, damage_a)
            else:
                ship_a.health -= damage_a
                self.hit_effect(ship_a.x, ship_a.y)

            if isinstance(ship_b, NPCShip):
                self.damage_npc_from_collision(ship_b, damage_b)
            else:
                ship_b.health -= damage_b
                self.hit_effect(ship_b.x, ship_b.y)

            if player_a or player_b:
                player_damage = damage_a if player_a else damage_b
                self.show_message(
                    f"Столкновение! Корпус -{player_damage}",
                    1.8
                )

        return True

    def handle_sea_collisions(self):

        active_npcs = [npc for npc in self.npc_ships if npc.alive]

        # Игрок и NPC не могут проходить сквозь острова.
        for island in self.islands:
            self.resolve_island_collision(
                self.ship, island, True
            )

            for npc in active_npcs:
                self.resolve_island_collision(
                    npc, island, False
                )

        # Игрок сталкивается со всеми живыми кораблями.
        for npc in active_npcs:
            self.resolve_ship_collision(
                self.ship, npc, True, False
            )

        # NPC также сталкиваются друг с другом.
        for i in range(len(active_npcs)):
            for j in range(i + 1, len(active_npcs)):
                self.resolve_ship_collision(
                    active_npcs[i],
                    active_npcs[j]
                )

        self.ship.x = clamp(self.ship.x, 45, WORLD_WIDTH - 45)
        self.ship.y = clamp(self.ship.y, 45, WORLD_HEIGHT - 45)

        for npc in active_npcs:
            npc.x = clamp(npc.x, 45, WORLD_WIDTH - 45)
            npc.y = clamp(npc.y, 45, WORLD_HEIGHT - 45)

    # ========================================================
    # МОРЕ
    # ========================================================

    def nearest_port(self):

        best = None
        best_dist = 10**9

        for island in self.islands:
            if not island.has_port:
                continue

            # Пирс острова расположен справа от острова.
            dock_x = island.x + island.radius + 82
            dock_y = island.y

            d = distance((self.ship.x, self.ship.y), (dock_x, dock_y))

            if d < best_dist:
                best_dist = d
                best = (island, dock_x, dock_y)

        return best, best_dist

    def try_dock(self):

        result, d = self.nearest_port()

        if result is None:
            self.show_message("Поблизости нет порта.")
            return

        island, dock_x, dock_y = result

        if d > 105:
            self.show_message("Подойдите ближе к причалу.")
            return

        if abs(self.ship.speed) > 24:
            self.show_message("Слишком высокая скорость для причаливания.")
            return

        self.ship.speed = 0
        self.current_port = island.name

        # Пока полноценный город сделан для Порт-Ройала.
        # Остальные порты используют тот же городской экран,
        # но имя порта сохраняется для будущих отдельных городов.
        self.mode = "city"
        self.sound.play_music("city")
        self.player.x = 530
        self.player.y = 450

        self.show_message(f"Вы причалили: {island.name}")

    def update_sea(self, dt):

        self.sound.update_ambient("sea", self.wind.strength)
        self.sound.play_music("sea")

        self.wind.update(dt)

        self.ship.update(
            dt,
            self.wind,
            self.particles
        )

        self.camera.update(
            self.ship.x,
            self.ship.y
        )

        # NPC
        for npc in self.npc_ships:

            if npc.alive:

                npc.update(
                    dt,
                    self.ship,
                    self.balls,
                    self.particles,
                    self.wind
                )

        # Физические столкновения кораблей и берегов.
        self.handle_sea_collisions()

        # После отталкивания камера снова следует за игроком.
        self.camera.update(
            self.ship.x,
            self.ship.y
        )

        # частицы
        for particle in self.particles[:]:

            particle.update(dt)

            if particle.life <= 0:

                self.particles.remove(
                    particle
                )

        # ядра
        for ball in self.balls[:]:

            ball.update(dt)

            if ball.life <= 0:

                self.balls.remove(
                    ball
                )

                continue

            if ball.owner == "player":

                for npc in self.npc_ships:

                    if not npc.alive:
                        continue

                    if distance(
                        (
                            ball.x,
                            ball.y
                        ),
                        (
                            npc.x,
                            npc.y
                        )
                    ) < 36:

                        npc.health -= (
                            ball.damage
                        )

                        self.sound.play_spatial(
                            "cannon_hit", ball.x, ball.y,
                            self.ship.x, self.ship.y, 950, 0.82
                        )
                        self.hit_effect(
                            ball.x,
                            ball.y
                        )

                        if ball in self.balls:

                            self.balls.remove(
                                ball
                            )

                        if npc.health <= 0:

                            npc.alive = False

                            self.loot.append(
                                Loot(
                                    npc.x,
                                    npc.y
                                )
                            )

                            # большой эффект разрушения
                            for i in range(30):

                                self.hit_effect(
                                    npc.x
                                    + random.uniform(
                                        -20,
                                        20
                                    ),
                                    npc.y
                                    + random.uniform(
                                        -20,
                                        20
                                    )
                                )

                            if npc.ship_type == "boss":

                                self.boss_killed = True
                                self.quest_active = False

                                self.show_message(
                                    "КРАСНЫЙ ДЖЕК ПОТОПЛЕН!",
                                    4
                                )

                            else:

                                self.show_message(
                                    f"{npc.name} потоплен!"
                                )

                        break

            else:

                if distance(
                    (
                        ball.x,
                        ball.y
                    ),
                    (
                        self.ship.x,
                        self.ship.y
                    )
                ) < 38:

                    self.ship.health -= (
                        ball.damage
                    )

                    self.sound.play(
                        "cannon_hit", 0.88
                    )
                    self.hit_effect(
                        ball.x,
                        ball.y
                    )

                    if ball in self.balls:

                        self.balls.remove(
                            ball
                        )

        # добыча
        for loot in self.loot[:]:

            loot.update(dt)

            if loot.life <= 0:

                self.loot.remove(
                    loot
                )

                continue

            if distance(
                (
                    self.ship.x,
                    self.ship.y
                ),
                (
                    loot.x,
                    loot.y
                )
            ) < 50:

                self.player.gold += (
                    loot.gold
                )

                self.player.cannonballs += (
                    loot.ammo
                )

                self.show_message(
                    f"Добыча: +{loot.gold} зол.  +{loot.ammo} ядер"
                )

                self.loot.remove(
                    loot
                )

        # потопление игрока
        if self.ship.health <= 0:

            self.ship.health = (
                self.ship.max_health
            )

            self.player.gold = max(
                0,
                self.player.gold - 100
            )

            self.ship.speed = 0

            self.mode = "city"

            self.show_message(
                "Корабль спасён. Потеряно до 100 зол.",
                4
            )

        if self.message_timer > 0:

            self.message_timer -= dt

    # ========================================================
    # МОРЕ - ГРАФИКА
    # ========================================================

    def build_ocean_tile(self):
        """Однократно создаём детальную бесшовно повторяемую воду."""
        rng = random.Random(2037)
        size = 256
        tile = pygame.Surface((size, size)).convert()
        tile.fill((13, 65, 91))

        # Мягкие пятна глубины: многослойные полупрозрачные области.
        layer = pygame.Surface((size, size), pygame.SRCALPHA)
        for _ in range(260):
            x = rng.randrange(size)
            y = rng.randrange(size)
            radius = rng.randrange(10, 58)
            tint = rng.choice(((16, 109, 131, 9),
                               (2, 26, 56, 11),
                               (46, 145, 156, 7)))
            pygame.draw.circle(layer, tint, (x, y), radius)
        tile.blit(layer, (0, 0))

        # Волновая рябь и отражения.
        for _ in range(900):
            x, y = rng.randrange(size), rng.randrange(size)
            length = rng.randrange(3, 21)
            col = rng.choice(((36, 117, 140), (45, 131, 151),
                              (23, 92, 118), (60, 146, 157)))
            pygame.draw.line(tile, col, (x, y),
                             (min(size-1, x+length), y), 1)
        return tile

    def draw_ocean(self):
        if not hasattr(self, "ocean_tile"):
            asset_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "ocean_game_tile.png"
            )
            try:
                self.ocean_tile = pygame.image.load(asset_path).convert()
            except (pygame.error, FileNotFoundError):
                self.ocean_tile = self.build_ocean_tile()

        tile = self.ocean_tile
        tw, th = tile.get_size()
        width, height = screen.get_size()
        # Мировые координаты сохраняют текстуру на месте при движении камеры.
        ox = -int(self.camera.x) % tw - tw
        oy = -int(self.camera.y) % th - th
        for x in range(ox, width+tw, tw):
            for y in range(oy, height+th, th):
                screen.blit(tile, (x, y))

        # Живые гребешки: анимация не зависит от положения камеры.
        now = pygame.time.get_ticks() * 0.001
        spacing = 155
        minx = int(self.camera.x // spacing) * spacing
        miny = int(self.camera.y // spacing) * spacing
        for wx in range(minx, int(self.camera.x+width)+spacing, spacing):
            for wy in range(miny, int(self.camera.y+height)+spacing, spacing):
                phase = wx * 0.013 + wy * 0.027 + now * 0.85
                sx = int(wx - self.camera.x + math.sin(phase) * 8)
                sy = int(wy - self.camera.y + math.cos(phase) * 5)
                shimmer = int(125 + 40 * math.sin(phase))
                pygame.draw.arc(screen, (48, shimmer, 164),
                                (sx, sy, 26, 8), 0.12, 2.8, 1)

    def draw_ship_wake(self):
        """Пенный след позади корабля, усиливается со скоростью."""
        speed = abs(self.ship.speed)
        if speed < 6:
            return
        sx, sy = self.camera.world_to_screen(self.ship.x, self.ship.y)
        angle = self.ship.angle
        # Движение корабля вдоль (cos(angle), sin(angle)).
        dx, dy = math.cos(angle), math.sin(angle)
        side_x, side_y = -dy, dx
        length = min(165, 24 + speed * 0.65)
        t = pygame.time.get_ticks() * 0.001
        for i in range(24):
            k = i / 24
            back = 24 + k * length
            spread = 8 + 21 * k
            for sign in (-1, 1):
                wave = math.sin(i * 1.7 + t * 5 + sign) * 3
                px = int(sx - dx * back + side_x * sign * (spread + wave))
                py = int(sy - dy * back + side_y * sign * (spread + wave))
                col = (150, 212, 213) if i % 3 else (211, 238, 226)
                pygame.draw.circle(screen, col, (px, py), max(1, int(3*(1-k)+1)))
    def draw_sea_world(self):

        self.draw_ocean()

        for island in self.islands:

            island.draw(
                self.camera
            )

        # След и частицы рисуем
        # до кораблей.
        for particle in self.particles:

            particle.draw(
                self.camera
            )

        for loot in self.loot:

            loot.draw(
                self.camera
            )

        for npc in self.npc_ships:

            if npc.alive:

                npc.draw(
                    self.camera
                )

        for ball in self.balls:

            ball.draw(
                self.camera
            )

        self.draw_ship_wake()

        self.ship.draw(
            self.camera
        )

        # Тактический круг дальности вокруг корабля.
        if self.show_range:
            r = (90, 160, 240)[self.ship.gun_type]
            sx, sy = self.camera.world_to_screen(self.ship.x, self.ship.y)
            pygame.draw.circle(screen, (245, 214, 117),
                               (int(sx), int(sy)), int(r), 1)
            for a in range(0, 360, 45):
                ang = math.radians(a)
                px = sx + math.cos(ang) * r
                py = sy + math.sin(ang) * r
                pygame.draw.circle(screen, (245, 214, 117),
                                   (int(px), int(py)), 3)

    def draw_compass(self):
        """Неподвижный компас: показывает стороны света при любом виде камеры."""
        cx, cy = WIDTH - 77, 151
        radius = 48
        pygame.draw.circle(screen, (21, 37, 48), (cx, cy), radius + 9)
        pygame.draw.circle(screen, (184, 146, 78), (cx, cy), radius + 9, 3)
        pygame.draw.circle(screen, (42, 71, 83), (cx, cy), radius)
        pygame.draw.circle(screen, (216, 194, 135), (cx, cy), radius, 2)

        # В обычном виде север сверху; при виде с корабля мир вращается.
        theta = self.ship.angle + math.pi / 2 if self.ship_view else 0.0
        directions = (("С", 0), ("В", 90), ("Ю", 180), ("З", 270))
        for label, degrees in directions:
            a = math.radians(degrees) + theta
            dx, dy = -math.sin(a), -math.cos(a)
            x = int(cx + dx * 35)
            y = int(cy + dy * 35)
            glyph = small_font.render(label, True,
                (255, 215, 122) if label == "С" else (234, 235, 224))
            screen.blit(glyph, glyph.get_rect(center=(x, y)))
        pygame.draw.circle(screen, (244, 227, 172), (cx, cy), 4)
        bearing = (math.degrees(self.ship.angle) + 90) % 360
        label = small_font.render(f"Курс: {bearing:03.0f}°", True, (255, 233, 169))
        screen.blit(label, label.get_rect(center=(cx, cy + radius + 24)))

    def draw_sea(self):
        if not self.ship_view:
            self.draw_sea_world()
        else:
            # Рисуем мир на большом квадратном холсте и поворачиваем
            # его целиком. Корабль остаётся в центре носом вверх.
            global screen
            display_surface = screen
            old_x, old_y = self.camera.x, self.camera.y
            side = int(math.ceil(math.hypot(WIDTH, HEIGHT))) + 100
            if (self.rotating_world_surface is None or
                    self.rotating_world_surface.get_size() != (side, side)):
                self.rotating_world_surface = pygame.Surface((side, side)).convert()
            world_surface = self.rotating_world_surface
            try:
                screen = world_surface
                self.camera.x = self.ship.x - side / 2
                self.camera.y = self.ship.y - side / 2
                self.draw_sea_world()
                angle_deg = math.degrees(self.ship.angle + math.pi / 2)
                rotated = pygame.transform.rotate(world_surface, angle_deg)
            finally:
                screen = display_surface
                self.camera.x, self.camera.y = old_x, old_y

            rect = rotated.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(rotated, rect.topleft)

        self.draw_hud()

        self.draw_ship_panel()

        self.draw_wind_indicator()

        self.draw_minimap()

        self.draw_compass()

        self.draw_bottom(
            "W/S - паруса  A/D - руль  ЛКМ/ПКМ - огонь  1/2/3 - пушки  R - радиус  F - вид  M - звук"
        )

        self.draw_message()

    # ========================================================
    # ПАНЕЛЬ КОРАБЛЯ
    # ========================================================

    def draw_ship_panel(self):

        draw_panel(
            pygame.Rect(
                14,
                80,
                248,
                188
            ),
            (25, 39, 45),
            LIGHT_WOOD
        )

        wind_speed = (
            self.ship.wind_speed(
                self.wind
            )
        )

        draw_text(
            "КОРАБЛЬ",
            29,
            91,
            GOLD,
            small_font
        )

        draw_text(
            f"Ход: {abs(self.ship.speed):.0f}",
            29,
            119,
            WHITE,
            small_font
        )

        draw_text(
            f"Возможный ход: {wind_speed:.0f}",
            29,
            142,
            WHITE,
            small_font
        )

        draw_text(
            f"Ветер: {self.wind.description(self.ship.angle)}",
            29,
            165,
            GOLD,
            small_font
        )

        draw_text(
            f"Пушки: {self.ship.cannon_count}",
            29,
            188,
            WHITE,
            small_font
        )

        # левый борт
        if self.ship.left_reload <= 0:

            left = "Левый: ГОТОВ"
            left_color = GREEN

        else:

            left = (
                f"Левый: {self.ship.left_reload:.1f}"
            )

            left_color = GOLD

        # правый борт
        if self.ship.right_reload <= 0:

            right = "Правый: ГОТОВ"
            right_color = GREEN

        else:

            right = (
                f"Правый: {self.ship.right_reload:.1f}"
            )

            right_color = GOLD

        draw_text(
            left,
            29,
            215,
            left_color,
            small_font
        )

        draw_text(
            right,
            29,
            239,
            right_color,
            small_font
        )

    # ========================================================
    # ВЕТЕР
    # ========================================================

    def draw_wind_indicator(self):

        cx = 845
        cy = 130

        radius = 47

        pygame.draw.circle(
            screen,
            (23, 42, 50),
            (
                cx,
                cy
            ),
            radius
        )

        pygame.draw.circle(
            screen,
            LIGHT_WOOD,
            (
                cx,
                cy
            ),
            radius,
            3
        )

        # деления компаса
        for i in range(8):

            a = (
                i
                * math.pi
                / 4
            )

            x1 = (
                cx
                + math.cos(a)
                * 37
            )

            y1 = (
                cy
                + math.sin(a)
                * 37
            )

            x2 = (
                cx
                + math.cos(a)
                * 44
            )

            y2 = (
                cy
                + math.sin(a)
                * 44
            )

            pygame.draw.line(
                screen,
                WHITE,
                (
                    int(x1),
                    int(y1)
                ),
                (
                    int(x2),
                    int(y2)
                ),
                2
            )

        length = (
            25
            + self.wind.strength * 15
        )

        ex = (
            cx
            + math.cos(
                self.wind.angle
            ) * length
        )

        ey = (
            cy
            + math.sin(
                self.wind.angle
            ) * length
        )

        pygame.draw.line(
            screen,
            GOLD,
            (
                cx,
                cy
            ),
            (
                int(ex),
                int(ey)
            ),
            5
        )

        # стрелка
        a1 = (
            self.wind.angle
            + 2.55
        )

        a2 = (
            self.wind.angle
            - 2.55
        )

        pygame.draw.polygon(
            screen,
            GOLD,
            [
                (
                    int(ex),
                    int(ey)
                ),
                (
                    int(
                        ex
                        + math.cos(a1)
                        * 12
                    ),
                    int(
                        ey
                        + math.sin(a1)
                        * 12
                    )
                ),
                (
                    int(
                        ex
                        + math.cos(a2)
                        * 12
                    ),
                    int(
                        ey
                        + math.sin(a2)
                        * 12
                    )
                )
            ]
        )

        draw_centered(
            "ВЕТЕР",
            cx,
            73,
            WHITE,
            tiny_font
        )

        draw_centered(
            f"{int(self.wind.strength * 100)}%",
            cx,
            181,
            WHITE,
            tiny_font
        )

    # ========================================================
    # МИНИ-КАРТА
    # ========================================================

    def draw_minimap(self):

        map_w = 190
        map_h = 175

        map_x = (
            WIDTH
            - map_w
            - 15
        )

        map_y = 220

        pygame.draw.rect(
            screen,
            (12, 62, 86),
            (
                map_x,
                map_y,
                map_w,
                map_h
            ),
            border_radius=5
        )

        pygame.draw.rect(
            screen,
            LIGHT_WOOD,
            (
                map_x,
                map_y,
                map_w,
                map_h
            ),
            2,
            border_radius=5
        )

        for island in self.islands:

            mx = (
                map_x
                + island.x
                / WORLD_WIDTH
                * map_w
            )

            my = (
                map_y
                + island.y
                / WORLD_HEIGHT
                * map_h
            )

            pygame.draw.circle(
                screen,
                SAND,
                (
                    int(mx),
                    int(my)
                ),
                4
            )

        for npc in self.npc_ships:

            if not npc.alive:
                continue

            mx = (
                map_x
                + npc.x
                / WORLD_WIDTH
                * map_w
            )

            my = (
                map_y
                + npc.y
                / WORLD_HEIGHT
                * map_h
            )

            if npc.ship_type == "trader":
                color = WHITE

            elif npc.ship_type == "pirate":
                color = RED

            else:
                color = GOLD

            pygame.draw.circle(
                screen,
                color,
                (
                    int(mx),
                    int(my)
                ),
                2
            )

        px = (
            map_x
            + self.ship.x
            / WORLD_WIDTH
            * map_w
        )

        py = (
            map_y
            + self.ship.y
            / WORLD_HEIGHT
            * map_h
        )

        pygame.draw.circle(
            screen,
            GREEN,
            (
                int(px),
                int(py)
            ),
            5
        )

        draw_text(
            "КАРТА",
            map_x + 7,
            map_y + 5,
            WHITE,
            tiny_font
        )

    # ========================================================
    # HUD
    # ========================================================

    def draw_hud(self):

        pygame.draw.rect(
            screen,
            DARK_GRAY,
            (
                0,
                0,
                WIDTH,
                HUD_HEIGHT
            )
        )

        # деревянная линия
        pygame.draw.rect(
            screen,
            LIGHT_WOOD,
            (
                0,
                HUD_HEIGHT - 5,
                WIDTH,
                5
            )
        )

        draw_text(
            "ГРОЗА МОРЕЙ",
            15,
            12,
            GOLD,
            big_font
        )

        draw_text(
            f"Золото: {self.player.gold}",
            300,
            13,
            GOLD,
            small_font
        )

        draw_text(
            f"Ядра: {self.player.cannonballs}",
            300,
            38,
            WHITE,
            small_font
        )

        if self.mode == "sea":

            draw_text(
                f"Корпус: {self.ship.health}/{self.ship.max_health}",
                465,
                13,
                WHITE,
                small_font
            )

            draw_text(
                f"Координаты: {int(self.ship.x)} : {int(self.ship.y)}",
                465,
                38,
                WHITE,
                small_font
            )

    def draw_bottom(self, text):

        pygame.draw.rect(
            screen,
            (23, 25, 27),
            (
                0,
                HEIGHT - BOTTOM_PANEL,
                WIDTH,
                BOTTOM_PANEL
            )
        )

        pygame.draw.rect(
            screen,
            LIGHT_WOOD,
            (
                0,
                HEIGHT - BOTTOM_PANEL,
                WIDTH,
                4
            )
        )

        draw_centered(
            text,
            WIDTH // 2,
            HEIGHT - 32,
            WHITE,
            small_font
        )

    def draw_message(self):

        if self.message_timer <= 0:
            return

        draw_panel(
            pygame.Rect(
                WIDTH // 2 - 300,
                75,
                600,
                43
            ),
            (30, 32, 31),
            GOLD
        )

        draw_centered(
            self.message,
            WIDTH // 2,
            87,
            WHITE,
            small_font
        )

    # ========================================================
    # СТРЕЛЬБА
    # ========================================================

    def fire_player_side(self, side):

        success, reason = (
            self.ship.fire(
                self.balls,
                self.particles,
                side,
                self.player
            )
        )

        if success:
            self.sound.play_cannon()
            return

        if reason == "reload":

            self.show_message(
                "Этот борт ещё перезаряжается."
            )

        elif reason == "ammo":

            self.show_message(
                "Недостаточно ядер."
            )

    # ========================================================
    # МЫШЬ
    # ========================================================

    def handle_mouse(self, button):

        if self.mode != "sea":
            return

        if button == 1:

            self.fire_player_side(
                "left"
            )

        elif button == 3:

            self.fire_player_side(
                "right"
            )

    # ========================================================
    # КЛАВИАТУРА
    # ========================================================

    def handle_key(self, key):

        if key == pygame.K_F5:
            self.save_game()
            return
        if key == pygame.K_F9:
            self.load_game()
            return
        if key == pygame.K_j:
            self.journal_visible = not self.journal_visible
            return
        if self.journal_visible:
            if key == pygame.K_ESCAPE:
                self.journal_visible = False
            return

        if key == pygame.K_m:
            self.sound.toggle()
            self.show_message("Звук: " + ("ВКЛ" if self.sound.enabled else "ВЫКЛ"))
            return


        if self.mode == "sea":
            if key == pygame.K_f:
                self.ship_view = not self.ship_view
                self.show_message("Вид: с корабля (нос вверх)" if self.ship_view
                                  else "Вид: обычная карта")
                return
            if key in (pygame.K_1, pygame.K_2, pygame.K_3):
                self.ship.gun_type = key - pygame.K_1
                names = ("Карронада", "Обычная пушка", "Дальнобойная пушка")
                ranges = (90, 160, 240)
                self.show_message(f"{names[self.ship.gun_type]}: дальность {ranges[self.ship.gun_type]}")
                return
            if key == pygame.K_r:
                self.show_range = not self.show_range
                return

        if self.mode == "room":
            if key == pygame.K_e:
                self.interact_room()
            elif key == pygame.K_ESCAPE:
                self.leave_room()
            return

        if self.mode == "city":

            if key == pygame.K_e:

                self.interact_city()

        elif self.mode == "tavern":

            if key == pygame.K_1:

                if self.boss_killed:

                    self.player.gold += 500
                    self.boss_killed = False
                    self.quest_active = False
                    self.quest_rewarded = True

                    self.show_message(
                        "Получено 500 зол."
                    )

                elif not self.quest_active:

                    self.quest_active = True

                    self.show_message(
                        "Контракт принят."
                    )

            elif key == pygame.K_ESCAPE:

                self.mode = "room"

        elif self.mode == "shop":

            purchases = {
                pygame.K_1: (30, 10),
                pygame.K_2: (80, 30),
                pygame.K_3: (240, 100)
            }

            if key in purchases:

                cost, ammo = (
                    purchases[key]
                )

                if self.player.gold >= cost:

                    self.player.gold -= cost
                    self.player.cannonballs += ammo

                    self.show_message(
                        f"Куплено {ammo} ядер."
                    )

                else:

                    self.show_message(
                        "Недостаточно золота."
                    )

            elif key == pygame.K_ESCAPE:

                self.mode = "room"

        elif self.mode == "bank":

            if key == pygame.K_1:

                amount = min(
                    100,
                    self.player.gold
                )

                self.player.gold -= amount
                self.player.bank_gold += amount

            elif key == pygame.K_2:

                amount = min(
                    100,
                    self.player.bank_gold
                )

                self.player.bank_gold -= amount
                self.player.gold += amount

            elif key == pygame.K_ESCAPE:

                self.mode = "room"

        elif self.mode == "shipyard":

            if key == pygame.K_1:

                if self.ship.cannon_count >= 20:

                    self.show_message(
                        "Предел — 20 пушек."
                    )

                elif self.player.gold >= 250:

                    self.player.gold -= 250
                    self.ship.cannon_count += 2

                    self.show_message(
                        "Установлено две новые пушки."
                    )

                else:

                    self.show_message(
                        "Недостаточно золота."
                    )

            elif key == pygame.K_2:

                if self.ship.cannon_count > 2:

                    self.ship.cannon_count -= 2

                    self.show_message(
                        "Две пушки сняты."
                    )

            elif key == pygame.K_3:

                missing = (
                    self.ship.max_health
                    - self.ship.health
                )

                if missing <= 0:

                    self.show_message(
                        "Корпус не повреждён."
                    )

                elif self.player.gold >= missing:

                    self.player.gold -= missing
                    self.ship.health = self.ship.max_health

                    self.show_message(
                        "Ремонт завершён."
                    )

                else:

                    self.show_message(
                        "Недостаточно золота."
                    )

            elif key == pygame.K_ESCAPE:

                self.mode = "room"

        elif self.mode == "sea":

            # Q остаётся запасной клавишей левого борта.
            if key == pygame.K_q:

                self.fire_player_side(
                    "left"
                )

            # E теперь используется для настоящего причаливания.
            elif key == pygame.K_e:

                self.try_dock()

            elif key == pygame.K_ESCAPE:

                self.show_message(
                    "Чтобы вернуться в город, подойдите к причалу и нажмите E."
                )

    # ========================================================
    # ОСНОВНОЙ ЦИКЛ
    # ========================================================

    def run(self):

        running = True

        while running:

            dt = (
                clock.tick(FPS)
                / 1000.0
            )

            # Защита от огромного dt,
            # например при перетаскивании окна.
            dt = min(
                dt,
                0.05
            )

            for event in pygame.event.get():

                if event.type == pygame.QUIT:

                    running = False

                elif event.type == pygame.KEYDOWN:

                    self.handle_key(
                        event.key
                    )

                elif event.type == pygame.MOUSEBUTTONDOWN:

                    self.handle_mouse(
                        event.button
                    )

            if self.mode == "city":

                self.update_city(dt)

            elif self.mode == "sea":

                self.update_sea(dt)

            elif self.mode == "room":

                self.update_room(dt)

            else:

                if self.message_timer > 0:
                    self.message_timer -= dt

            if self.mode == "city":

                self.draw_city()

            elif self.mode == "sea":

                self.draw_sea()

            elif self.mode == "room":

                self.draw_room()

            elif self.mode == "tavern":

                self.draw_tavern()

            elif self.mode == "shop":

                self.draw_shop()

            elif self.mode == "bank":

                self.draw_bank()

            elif self.mode == "shipyard":

                self.draw_shipyard()

            self.draw_journal()
            pygame.display.flip()

        pygame.quit()
        sys.exit()


# ============================================================
# ЗАПУСК
# ============================================================

if __name__ == "__main__":

    game = Game()
    game.run()