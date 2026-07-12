from machine import Pin
import random
import time
from helpers.buzzer_sounds import sound


# -----------------------------
# RGB565 colors
# -----------------------------
def color565(r, g, b):
    # Byte-swapped RGB565 for st7735_fb framebuffer driver.
    c = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return ((c & 0xFF) << 8) | (c >> 8)

# Use this instead if red and blue are swapped on your display.
def color565_bgr(r, g, b):
    c = ((b & 0xF8) << 8) | ((g & 0xFC) << 3) | (r >> 3)
    return ((c & 0xFF) << 8) | (c >> 8)

BLACK = color565(0, 0, 0)
WHITE = color565(255, 255, 255)
GRAY = color565(128, 128, 128)
DARK_GRAY = color565(40, 40, 40)
RED = color565(255, 0, 0)
GREEN = color565(0, 255, 0)
BLUE = color565(0, 0, 255)
YELLOW = color565(255, 255, 0)
CYAN = color565(0, 255, 255)
MAGENTA = color565(255, 0, 255)
ORANGE = color565(255, 128, 0)
PURPLE = color565(128, 0, 255)
PINK = color565(255, 80, 160)
HEALTH_GREEN = color565(0, 255, 80)
DANGER_RED = color565(255, 40, 40)
SHIELD_BLUE = color565(80, 180, 255)
SPACE_BLACK = color565(0, 0, 8)
STAR_WHITE = color565(240, 240, 255)
ENEMY_BULLET = color565(255, 80, 0)
PLAYER_BULLET = color565(0, 255, 255)
LASER_COLOR = color565(255, 0, 0)
FREEZE_COLOR = color565(120, 220, 255)
BOMB_COLOR = color565(255, 180, 0)
BOSS_GHOST = color565(180, 220, 255)
BOSS_CORE = color565(255, 0, 80)

# Color sprite palette:
# 0 = transparent. Other characters become colors.
GAME_PALETTE = {
    "0": None,
    "1": WHITE,
    "2": CYAN,
    "3": BLUE,
    "4": RED,
    "5": GREEN,
    "6": YELLOW,
    "7": ORANGE,
    "8": PURPLE,
    "9": GRAY,
    "A": MAGENTA,
    "B": SHIELD_BLUE,
    "C": BOSS_CORE,
    "D": DARK_GRAY,
    "E": color565(80, 255, 80),
    "F": color565(255, 120, 0),
    "G": BOSS_GHOST,
    "H": HEALTH_GREEN,
}
