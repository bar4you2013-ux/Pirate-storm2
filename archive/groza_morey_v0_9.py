import pygame
import math
import random
import sys
import os

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

        self.travelled += self.speed * dt
        self.life -= dt
        if self.travelled >= self.max_range:
            self.life = 0

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

    def draw(self, camera):

        sx, sy = camera.world_to_screen(
            self.x,
            self.y
        )

        if (
            sx < -self.radius * 2
            or sx > WIDTH + self.radius * 2
            or sy < -self.radius * 2
            or sy > HEIGHT + self.radius * 2
        ):
            return

        # тёмная вода возле берега
        pygame.draw.ellipse(
            screen,
            SEA_DARK,
            (
                int(sx - self.radius - 10),
                int(sy - self.radius * 0.68 - 10),
                int(self.radius * 2 + 20),
                int(self.radius * 1.36 + 20)
            )
        )

        # берег
        pygame.draw.ellipse(
            screen,
            SAND,
            (
                int(sx - self.radius),
                int(sy - self.radius * 0.65),
                int(self.radius * 2),
                int(self.radius * 1.3)
            )
        )

        # внутренняя часть
        pygame.draw.ellipse(
            screen,
            GREEN,
            (
                int(sx - self.radius * 0.72),
                int(sy - self.radius * 0.43),
                int(self.radius * 1.44),
                int(self.radius * 0.86)
            )
        )

        # более тёмная растительность
        pygame.draw.ellipse(
            screen,
            DARK_GREEN,
            (
                int(sx - self.radius * 0.46),
                int(sy - self.radius * 0.30),
                int(self.radius * 0.92),
                int(self.radius * 0.60)
            )
        )

        # пальмы
        for px, py in self.palms:

            self.draw_palm(
                sx + px,
                sy + py
            )

        if self.has_port:

            port_x = (
                sx
                + self.radius * 0.65
            )

            # маленький склад
            pygame.draw.rect(
                screen,
                BROWN,
                (
                    int(port_x - 25),
                    int(sy - 50),
                    38,
                    30
                )
            )

            pygame.draw.polygon(
                screen,
                DARK_BROWN,
                [
                    (
                        port_x - 30,
                        sy - 50
                    ),
                    (
                        port_x - 6,
                        sy - 67
                    ),
                    (
                        port_x + 18,
                        sy - 50
                    )
                ]
            )

            # пирс
            pygame.draw.rect(
                screen,
                WOOD,
                (
                    int(port_x),
                    int(sy - 10),
                    75,
                    20
                )
            )

            for i in range(5):

                pygame.draw.line(
                    screen,
                    DARK_BROWN,
                    (
                        int(port_x + i * 15),
                        int(sy - 10)
                    ),
                    (
                        int(port_x + i * 15),
                        int(sy + 10)
                    ),
                    2
                )

        draw_centered(
            self.name,
            sx,
            sy - self.radius * 0.78,
            WHITE,
            small_font
        )


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
        self.max_range = 320.0

    def update(self, dt):

        self.x += self.dx * dt
        self.y += self.dy * dt

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
            balls[-1].max_range = (180, 320, 480)[self.gun_type]


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
            or sx > WIDTH + 100
            or sy < -100
            or sy > HEIGHT + 100
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

    def draw_ocean(self):

        screen.fill(SEA)

        # крупные полосы воды
        band = 180

        start_y = int(
            self.camera.y // band
        ) * band

        for wy in range(
            start_y,
            int(
                self.camera.y
                + HEIGHT
                + band
            ),
            band
        ):

            sy = (
                wy - self.camera.y
            )

            pygame.draw.rect(
                screen,
                SEA_LIGHT,
                (
                    0,
                    int(sy),
                    WIDTH,
                    2
                )
            )

        # мелкие волны
        grid = 80

        start_x = (
            int(
                self.camera.x // grid
            )
            * grid
        )

        start_y = (
            int(
                self.camera.y // grid
            )
            * grid
        )

        for wx in range(
            start_x,
            int(
                self.camera.x
                + WIDTH
                + grid
            ),
            grid
        ):

            for wy in range(
                start_y,
                int(
                    self.camera.y
                    + HEIGHT
                    + grid
                ),
                grid
            ):

                sx, sy = (
                    self.camera.world_to_screen(
                        wx,
                        wy
                    )
                )

                variation = (
                    int(wx / grid)
                    + int(wy / grid)
                ) % 3

                length = (
                    18
                    + variation * 6
                )

                pygame.draw.arc(
                    screen,
                    SEA_LIGHT,
                    (
                        int(sx),
                        int(sy),
                        length,
                        8
                    ),
                    0,
                    math.pi,
                    2
                )

    def draw_sea(self):

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

        self.ship.draw(
            self.camera
        )

        # Тактический круг дальности вокруг корабля.
        if self.show_range:
            r = (180, 320, 480)[self.ship.gun_type]
            sx, sy = self.camera.world_to_screen(self.ship.x, self.ship.y)
            pygame.draw.circle(screen, (245, 214, 117),
                               (int(sx), int(sy)), int(r), 1)
            for a in range(0, 360, 45):
                ang = math.radians(a)
                px = sx + math.cos(ang) * r
                py = sy + math.sin(ang) * r
                pygame.draw.circle(screen, (245, 214, 117),
                                   (int(px), int(py)), 3)

        self.draw_hud()

        self.draw_ship_panel()

        self.draw_wind_indicator()

        self.draw_minimap()

        self.draw_bottom(
            "W/S - паруса  A/D - руль  ЛКМ/ПКМ - огонь  1/2/3 - пушки  R - радиус  M - звук"
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
            if key in (pygame.K_1, pygame.K_2, pygame.K_3):
                self.ship.gun_type = key - pygame.K_1
                names = ("Карронада", "Обычная пушка", "Дальнобойная пушка")
                ranges = (180, 320, 480)
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