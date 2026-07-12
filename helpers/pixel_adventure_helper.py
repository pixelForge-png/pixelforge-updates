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
    "B": BLACK,
}

def show_display(display):
    if hasattr(display, "show"):
        display.show()

def draw_text(display, text, x, y, color=WHITE):
    try:
        display.text(text, x, y, color)
    except TypeError:
        display.text(text, x, y)

def center_text_x(display, text, y, color=WHITE, screen_w=SCREEN_W):
    x = (screen_w - len(text) * 8) // 2
    draw_text(display, text, x, y, color)

def safe_pixel(display, x, y, color, screen_w=SCREEN_W, screen_h=SCREEN_H):
    if 0 <= x < screen_w and 0 <= y < screen_h:
        display.pixel(x, y, color)

def draw_sprite(display, sprite, x, y, color=WHITE, screen_w=SCREEN_W, screen_h=SCREEN_H):
    for row_index, row in enumerate(sprite):
        for col_index, pixel in enumerate(row):
            if pixel == "1":
                safe_pixel(display, x + col_index, y + row_index, color, screen_w, screen_h)

def draw_color_sprite(display, sprite, x, y, palette=GAME_PALETTE, transparent="0", screen_w=SCREEN_W, screen_h=SCREEN_H):
    for row_index, row in enumerate(sprite):
        for col_index, pixel in enumerate(row):
            if pixel != transparent and pixel in palette:
                color = palette[pixel]
                if color is not None:
                    safe_pixel(display, x + col_index, y + row_index, color, screen_w, screen_h)

# -----------------------------
# Tiny text
# -----------------------------
tiny_font = {
    "A": ["010", "101", "111", "101", "101"],
    "B": ["110", "101", "110", "101", "110"],
    "C": ["011", "100", "100", "100", "011"],
    "D": ["110", "101", "101", "101", "110"],
    "E": ["111", "100", "110", "100", "111"],
    "F": ["111", "100", "110", "100", "100"],
    "G": ["011", "100", "101", "101", "011"],
    "H": ["101", "101", "111", "101", "101"],
    "I": ["111", "010", "010", "010", "111"],
    "J": ["001", "001", "001", "101", "010"],
    "K": ["101", "101", "110", "101", "101"],
    "L": ["100", "100", "100", "100", "111"],
    "M": ["101", "111", "111", "101", "101"],
    "N": ["101", "111", "111", "111", "101"],
    "O": ["111", "101", "101", "101", "111"],
    "P": ["110", "101", "110", "100", "100"],
    "Q": ["111", "101", "101", "111", "001"],
    "R": ["110", "101", "110", "101", "101"],
    "S": ["011", "100", "111", "001", "110"],
    "T": ["111", "010", "010", "010", "010"],
    "U": ["101", "101", "101", "101", "111"],
    "V": ["101", "101", "101", "101", "010"],
    "W": ["101", "101", "111", "111", "101"],
    "X": ["101", "101", "010", "101", "101"],
    "Y": ["101", "101", "010", "010", "010"],
    "Z": ["111", "001", "010", "100", "111"],
    "0": ["111", "101", "101", "101", "111"],
    "1": ["010", "110", "010", "010", "111"],
    "2": ["111", "001", "111", "100", "111"],
    "3": ["111", "001", "111", "001", "111"],
    "4": ["101", "101", "111", "001", "001"],
    "5": ["111", "100", "111", "001", "111"],
    "6": ["111", "100", "111", "101", "111"],
    "7": ["111", "001", "010", "010", "010"],
    "8": ["111", "101", "111", "101", "111"],
    "9": ["111", "101", "111", "001", "111"],
    " ": ["000", "000", "000", "000", "000"],
    "/": ["001", "001", "010", "100", "100"],
    "-": ["000", "000", "111", "000", "000"],
    ":": ["000", "010", "000", "010", "000"],
    "!": ["010", "010", "010", "000", "010"],
    "?": ["111", "001", "010", "000", "010"],
    "=": ["000", "111", "000", "111", "000"],
}

def draw_tiny_char(display, char, x, y, color=WHITE):
    char = char.upper()
    if char in tiny_font:
        draw_sprite(display, tiny_font[char], x, y, color)
    else:
        draw_sprite(display, tiny_font["?"], x, y, color)

def draw_tiny_text(display, text, x, y, color=WHITE):
    for i in range(len(text)):
        draw_tiny_char(display, text[i], x + i * 4, y, color)

def joystick_direction(joy_x, joy_y, low=22000, high=43000):
    x = joy_x.read_u16()
    y = joy_y.read_u16()
    right = x < low
    left = x > high
    down = y > high
    up = y < low
    return left, right, up, down, x, y

def joystick_pressed(joy_sw):
    return joy_sw.value() == 0

def wait_for_joystick_release(joy_sw):
    while joy_sw.value() == 0:
        time.sleep(0.01)
