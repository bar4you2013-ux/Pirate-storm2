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

        self.fish_cargo = 0
        self.fish_capacity = 30
        self.fish_price = 12
        self.fishing_timer = 0.0
        self.fishing_active = False
        self.fishing_interval = 4.5
        self.sea_night_layer = None
        self.ship_lantern_glow = None
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
            "fish_cargo": self.fish_cargo,
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
            self.fish_cargo = max(0, min(self.fish_capacity, int(data.get("fish_cargo",0))))
            self.fishing_active = False
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
                "[3] 100 ядер — 240 зол.",
                f"[4] Продать рыбу: {self.fish_cargo} шт. по {self.fish_price} зол."
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
        self.city_minutes = (self.city_minutes + dt * 1.5) % 1440
        if self.fishing_active:
            if abs(self.ship.speed) > 18:
                self.fishing_active = False
                self.fishing_timer = 0
                self.show_message("Рыбалка остановлена: корабль движется слишком быстро.")
            elif self.fish_cargo >= self.fish_capacity:
                self.fishing_active = False
                self.show_message("Трюм с рыбой заполнен. Продайте улов в лавке.")
            else:
                self.fishing_timer += dt
                if self.fishing_timer >= self.fishing_interval:
                    self.fishing_timer = 0
                    # Небольшая случайность: иногда рыба не клюёт.
                    if random.random() < 0.78:
                        amount = min(random.randint(1, 3),
                                     self.fish_capacity-self.fish_cargo)
                        self.fish_cargo += amount
                        self.show_message(f"Поймано рыбы: +{amount}. В трюме: {self.fish_cargo}/{self.fish_capacity}")
                    else:
                        self.show_message("Поклёвки нет. Ждём...")
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

    def draw_sea_night(self):
        """Ночь затемняет море, фонари остаются яркими в обоих режимах."""
        hour = self.city_minutes / 60
        if 6 <= hour < 18:
            alpha = 0
        elif 18 <= hour < 21:
            alpha = int((hour-18)/3*165)
        elif 4 <= hour < 6:
            alpha = int((6-hour)/2*165)
        else:
            alpha = 165
        if alpha <= 0:
            return
        if self.sea_night_layer is None:
            self.sea_night_layer = pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
        self.sea_night_layer.fill((4, 12, 37, alpha))
        screen.blit(self.sea_night_layer,(0,0))
        # Корабль в центре камеры; для второго режима точка также в центре.
        lights = [(self.ship.x,self.ship.y)]
        lights.extend((npc.x,npc.y) for npc in self.npc_ships if npc.alive)
        for i,(wx,wy) in enumerate(lights):
            if self.ship_view:
                dx,dy=wx-self.ship.x,wy-self.ship.y
                ang=self.ship.angle+math.pi/2
                # Pygame rotate: positive angle counterclockwise on screen.
                sx=WIDTH//2 + dx*math.cos(ang)+dy*math.sin(ang)
                sy=HEIGHT//2 - dx*math.sin(ang)+dy*math.cos(ang)
            else:
                sx,sy=self.camera.world_to_screen(wx,wy)
            if not (-60<sx<WIDTH+60 and -60<sy<HEIGHT+60):
                continue
            if self.ship_lantern_glow is None:
                glow=pygame.Surface((116,116),pygame.SRCALPHA)
                for r in range(54,4,-3):
                    pygame.draw.circle(glow,(255,177,62, max(1,int(13*(1-r/58)))),
                                       (58,58),r)
                self.ship_lantern_glow=glow
            screen.blit(self.ship_lantern_glow,(int(sx)-58,int(sy)-58),
                        special_flags=pygame.BLEND_RGBA_ADD)
            for ox,oy in ((-14,-10),(14,-10),(-12,16),(12,16)):
                pygame.draw.circle(screen,(255,190,87),(int(sx+ox),int(sy+oy)),3)
                pygame.draw.circle(screen,(255,236,161),(int(sx+ox),int(sy+oy)),1)

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

        self.draw_sea_night()

        self.draw_hud()

        self.draw_ship_panel()

        self.draw_wind_indicator()

        self.draw_minimap()

        self.draw_compass()
        fish_info = f"Рыба: {self.fish_cargo}/{self.fish_capacity} | {'РЫБАЛКА' if self.fishing_active else 'T - ловить рыбу'} | {int(self.city_minutes//60):02d}:{int(self.city_minutes%60):02d}"
        fish_img = small_font.render(fish_info, True, (255, 225, 157))
        screen.blit(fish_img, (18, HEIGHT-91))

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
            if key == pygame.K_t:
                if self.fishing_active:
                    self.fishing_active = False
                    self.show_message("Удочка убрана.")
                elif abs(self.ship.speed) > 18:
                    self.show_message("Убавьте паруса: для рыбалки скорость должна быть меньше 18.")
                elif self.fish_cargo >= self.fish_capacity:
                    self.show_message("Трюм полон рыбы.")
                else:
                    self.fishing_active = True
                    self.fishing_timer = 0
                    self.show_message("Рыбалка началась! Держите корабль почти неподвижным.")
                return
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
            if key == pygame.K_4:
                if self.fish_cargo:
                    earned = self.fish_cargo * self.fish_price
                    self.player.gold += earned
                    self.show_message(f"Продано {self.fish_cargo} рыб за {earned} зол.")
                    self.fish_cargo = 0
                else:
                    self.show_message("В трюме нет рыбы.")
                return

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