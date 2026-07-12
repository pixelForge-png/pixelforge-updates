import time
import random
from helpers.buzzer_sounds import sound
from helpers.pixel_adventure_helper import (
    BLACK, WHITE, GRAY, DARK_GRAY, RED, GREEN, BLUE, YELLOW, CYAN, MAGENTA,
    ORANGE, PURPLE, HEALTH_GREEN, DANGER_RED, SHIELD_BLUE, SPACE_BLACK,
    ENEMY_BULLET, PLAYER_BULLET, LASER_COLOR, FREEZE_COLOR, BOMB_COLOR,
    GAME_PALETTE,
    center_text_x, draw_tiny_text, draw_color_sprite, draw_sprite, show_display,
    joystick_direction, joystick_pressed, wait_for_joystick_release
)


map = [
  ".......w",
  "@.....ww",
  ".......w"
]

wall = [
    "99999199",
    "99991199",
    "99111199",
    "99111999",
    "91191199",
    "11991119",
    "19911911",
    "99919991"
]
player = [
    "11111111",
    "11111111",
    "11111111",
    "11111111",
    "11111111",
    "11111111",
    "11111111",
    "11111111"
]

ground = [
    "00000000",
    "01000000",
    "00000100",
    "00001110",
    "00000100",
    "00000000",
    "01000000",
    "00000010",
]

TILE_SIZE = 8

for tile_y, row in enumerate(map):
    for tile_x, tile in enumerate(row):
        world_x = tile_x * TILE_SIZE
        world_y = tile_y * TILE_SIZE

        if tile == "w":
            draw_color_sprite(display, wall, world_x, world_y)
            pass

        elif tile == ".":
            draw_color_sprite(display, ground, world_x, world_y)
            pass

        elif tile == "@":
            draw_color_sprite(display, player, world_x, world_y)
            player_x = world_x
            player_y = world_y

show_display(oled)



