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
_EMBEDDED_SPRITES = {'house.png': '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', 'ship_trader.png': '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', 'ship_player.png': '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', 'shipyard.png': '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', 'ship_pirate.png': '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', 'shop.png': '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', 'tavern.png': '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', 'bank.png': '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'}
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

        self.sound.update_ambient("city", self.wind.strength)
        self.sound.play_music("city")

        if self.message_timer > 0:
            self.message_timer -= dt

    def interact_city(self):

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
                self.mode = "tavern"

            elif building.name == "Банк":
                self.mode = "bank"

            elif building.name == "Лавка":
                self.mode = "shop"

            elif building.name == "Верфь":
                self.mode = "shipyard"

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

        self.player.draw()

        self.draw_hud()
        self.draw_bottom("WASD - движение     E - войти / выйти в море")
        self.draw_message()

    # ========================================================
    # ЗДАНИЯ
    # ========================================================

    def draw_building_screen(
        self,
        title,
        lines
    ):

        screen.fill(
            (69, 54, 42)
        )

        # доски стены
        for y in range(
            70,
            HEIGHT,
            35
        ):

            pygame.draw.line(
                screen,
                (82, 63, 47),
                (
                    0,
                    y
                ),
                (
                    WIDTH,
                    y
                ),
                3
            )

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

        if self.mode == "city":

            if key == pygame.K_e:

                self.interact_city()

        elif self.mode == "tavern":

            if key == pygame.K_1:

                if self.boss_killed:

                    self.player.gold += 500
                    self.boss_killed = False

                    self.show_message(
                        "Получено 500 зол."
                    )

                elif not self.quest_active:

                    self.quest_active = True

                    self.show_message(
                        "Контракт принят."
                    )

            elif key == pygame.K_ESCAPE:

                self.mode = "city"

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

                self.mode = "city"

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

                self.mode = "city"

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

                self.mode = "city"

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

            else:

                if self.message_timer > 0:
                    self.message_timer -= dt

            if self.mode == "city":

                self.draw_city()

            elif self.mode == "sea":

                self.draw_sea()

            elif self.mode == "tavern":

                self.draw_tavern()

            elif self.mode == "shop":

                self.draw_shop()

            elif self.mode == "bank":

                self.draw_bank()

            elif self.mode == "shipyard":

                self.draw_shipyard()

            pygame.display.flip()

        pygame.quit()
        sys.exit()


# ============================================================
# ЗАПУСК
# ============================================================

if __name__ == "__main__":

    game = Game()
    game.run()