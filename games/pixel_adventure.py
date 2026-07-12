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
    "99999999",
    "96699669",
    "96699669",
    "99999999",
    "69966996",
    "69966996",
    "99999999",
    "96699669"
]

player = [
    "00011000",
    "00111100",
    "00166100",
    "00111100",
    "00011000",
    "00111100",
    "01111110",
    "01000010"
]

ground = [
    "22222222",
    "22222222",
    "22322222",
    "22222222",
    "22222232",
    "22222222",
    "22232222",
    "22222222"
]
TILE_SIZE = 8
player_speed = 2

walls = []

player_x = 0
player_y = 0


def load_map():
    global player_x, player_y

    walls.clear()

    for tile_y, row in enumerate(map):
        for tile_x, tile in enumerate(row):
            world_x = tile_x * TILE_SIZE
            world_y = tile_y * TILE_SIZE

            if tile == "w":
                walls.append([world_x, world_y])

            elif tile == "@":
                player_x = world_x
                player_y = world_y


def touches_wall(test_x, test_y):
    for wall_x, wall_y in walls:
        if (
            test_x < wall_x + TILE_SIZE and
            test_x + TILE_SIZE > wall_x and
            test_y < wall_y + TILE_SIZE and
            test_y + TILE_SIZE > wall_y
        ):
            return True

    return False


def main(oled, controls, settings):
    global player_x, player_y

    load_map()

    while True:
        left, right, up, down = controls["joystick"]()

        new_x = player_x
        new_y = player_y

        if left:
            new_x -= player_speed
        elif right:
            new_x += player_speed

        if up:
            new_y -= player_speed
        elif down:
            new_y += player_speed

        if not touches_wall(new_x, player_y):
            player_x = new_x

        if not touches_wall(player_x, new_y):
            player_y = new_y

        oled.fill(BLACK)

        for tile_y, row in enumerate(map):
            for tile_x, tile in enumerate(row):
                world_x = tile_x * TILE_SIZE
                world_y = tile_y * TILE_SIZE

                if tile == "w":
                    draw_color_sprite(
                        oled,
                        wall,
                        world_x,
                        world_y
                    )

                else:
                    draw_color_sprite(
                        oled,
                        ground,
                        world_x,
                        world_y
                    )

        draw_color_sprite(
            oled,
            player,
            player_x,
            player_y
        )

        show_display(oled)
        time.sleep(0.02)



