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
    "wwwwwwwwwwwwwwwwwwww",
    "w@.......w.........w",
    "w..ccc...w..ccc....w",
    "w........w.........w",
    "wwww..wwww....wwwwww",
    "w..................w",
    "w..wwww..m...cccc..w",
    "w..w............w..w",
    "w.......ccc........w",
    "wwwwwwwwwwwwwwwwwwww"
]

wall = [
    "999D999D",
    "9DD99DD9",
    "999D999D",
    "DDDDDDDD",
    "D999D999",
    "99DD99DD",
    "D999D999",
    "DDDDDDDD"
]

cracked_wall = [
    "999D999D",
    "9DD99DD9",
    "999D199D",
    "DDDD1DDD",
    "D991D999",
    "99D199DD",
    "D999D999",
    "DDDDDDDD"
]

player = [
    "00DDDD00",
    "0D2222D0",
    "D211112D",
    "D116611D",
    "0D3333D0",
    "D333333D",
    "03300330",
    "0DD00DD0"
]

ground = [
    "DDDDDDDD",
    "DD9DDDDD",
    "DDDDDDDD",
    "DDDDD9DD",
    "DDDDDDDD",
    "D9DDDDDD",
    "DDDDDDD9",
    "DDDDDDDD"
]

monster = [
    "11111111",
    "11111111",
    "11111111",
    "11111111",
    "11111111",
    "11111111",
    "11111111",
    "11111111"
]
facing_up = [
    "010",
    "101",
    "101"
]
facing_down = [
    "101",
    "101",
    "010"
]
facing_left = [
    "011",
    "100",
    "011"
]
facing_right = [
    "110",
    "001",
    "110"
]
TILE_SIZE = 8
player_speed = 2

walls = []
enemise = []

player_x = 0
player_y = 0
monsters = []



def load_map():
    global player_x, player_y

    walls.clear()

    for tile_y, row in enumerate(map):
        for tile_x, tile in enumerate(row):
            world_x = tile_x * TILE_SIZE
            world_y = tile_y * TILE_SIZE

            if tile == "w":
                walls.append([world_x, world_y])

            elif tile == "c":
                walls.append([world_x, world_y])

            elif tile == "m":
                monsters.append([world_x, world_y, 3])

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

def draw_map_tile(oled, tile_x, tile_y):
    tile = map[tile_y][tile_x]

    screen_x = tile_x * TILE_SIZE
    screen_y = tile_y * TILE_SIZE

    if tile == "w":
        draw_color_sprite(
            oled,
            wall,
            screen_x,
            screen_y
        )

    elif tile == "c":
        draw_color_sprite(
            oled,
            cracked_wall,
            screen_x,
            screen_y
        )

    elif tile == "m":
        draw_color_sprite(
            oled,
            monster,
            screen_x,
            screen_y
        )

    else:
        # Both "." and "@" have ground underneath.
        draw_color_sprite(
            oled,
            ground,
            screen_x,
            screen_y
        )

def draw_full_map(oled):
    for tile_y, row in enumerate(map):
        for tile_x, tile in enumerate(row):
            draw_map_tile(oled, tile_x, tile_y)

def restore_player_area(oled, x, y):
    left_tile = x // TILE_SIZE
    right_tile = (x + TILE_SIZE - 1) // TILE_SIZE

    top_tile = y // TILE_SIZE
    bottom_tile = (y + TILE_SIZE - 1) // TILE_SIZE

    for tile_y in range(top_tile, bottom_tile + 1):
        for tile_x in range(left_tile, right_tile + 1):
            if (
                0 <= tile_y < len(map) and
                0 <= tile_x < len(map[tile_y])
            ):
                draw_map_tile(oled, tile_x, tile_y)

facing = up


def main(oled, controls, settings):
    global player_x, player_y

    load_map()

    oled.fill(BLACK)
    draw_full_map(oled)

    draw_color_sprite(
        oled,
        player,
        player_x,
        player_y
    )

    show_display(oled)

    while True:
        left, right, up, down = controls["joystick"]()

        old_x = player_x
        old_y = player_y

        new_x = player_x
        new_y = player_y

        if left:
            new_x -= player_speed
            facing = left
        elif right:
            new_x += player_speed
            facing = right

        if up:
            new_y -= player_speed
            facing = up
        elif down:
            new_y += player_speed
            facing = down

        if not touches_wall(new_x, player_y):
            player_x = new_x

        if not touches_wall(player_x, new_y):
            player_y = new_y

        if facing == left:
            draw_color_sprite(oled, facing_left, player_x - 4, player_y + 2)

        if facing == right:
            draw_color_sprite(oled, facing_left, player_x + 9, player_y + 2)

        if facing == up:
            draw_color_sprite(oled, facing_left, player_x + 2, player_y - 4)

        if facing == down:
            draw_color_sprite(oled, facing_left, player_x + 2, player_y + 9)

        # Only redraw if the player actually moved.
        if player_x != old_x or player_y != old_y:
            restore_player_area(
                oled,
                old_x,
                old_y
            )

            draw_color_sprite(
                oled,
                player,
                player_x,
                player_y
            )

            show_display(oled)

        time.sleep(0.01)



