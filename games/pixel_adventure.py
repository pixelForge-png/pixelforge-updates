import time
import random
from helpers.pixel_adventure_helper import (
    BLACK, WHITE, GRAY, DARK_GRAY, RED, GREEN, BLUE, YELLOW, CYAN, MAGENTA,
    ORANGE, PURPLE, HEALTH_GREEN, DANGER_RED, SHIELD_BLUE, SPACE_BLACK,
    ENEMY_BULLET, PLAYER_BULLET, LASER_COLOR, FREEZE_COLOR, BOMB_COLOR,
    GAME_PALETTE,
    center_text_x, draw_tiny_text, draw_color_sprite, draw_sprite, show_display,
    joystick_direction, joystick_pressed, wait_for_joystick_release, ButtonAdapter,
)


# ============================================================
# DISPLAY / WORLD SETTINGS
# ============================================================

SCREEN_WIDTH = 160
SCREEN_HEIGHT = 80
TILE_SIZE = 8

VIEW_TILES_X = SCREEN_WIDTH // TILE_SIZE
VIEW_TILES_Y = SCREEN_HEIGHT // TILE_SIZE

MAP_WIDTH = 48
MAP_HEIGHT = 32

PLAYER_SPEED = 2
MONSTER_SPEED = 1

TARGET_FRAME_MS = 35

PLAYER_MAX_HEALTH = 5
MONSTER_HEALTH = 3
MONSTER_COUNT = 9

MONSTER_VISION_DISTANCE = 56
MONSTER_ATTACK_DISTANCE = 10
MONSTER_ATTACK_COOLDOWN = 850
MONSTER_ATTACK_LENGTH = 180
MONSTER_MOVE_DELAY = 55

PLAYER_ATTACK_LENGTH = 120
PLAYER_ATTACK_COOLDOWN = 160


# ============================================================
# SPRITES
# ============================================================

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

player_down = [
    "00DDDD00",
    "0D2222D0",
    "D211112D",
    "D116611D",
    "0D3333D0",
    "D333333D",
    "03300330",
    "0DD00DD0"
]

player_up = [
    "00DDDD00",
    "0D2222D0",
    "D222222D",
    "D222222D",
    "0D3333D0",
    "D333333D",
    "03300330",
    "0DD00DD0"
]

player_left = [
    "00DDDD00",
    "0D222D00",
    "D2112D00",
    "D1612DD0",
    "0D33333D",
    "D3333330",
    "03300330",
    "0DD00DD0"
]

player_right = [
    "00DDDD00",
    "00D222D0",
    "00D2112D",
    "0DD2161D",
    "D33333D0",
    "0333333D",
    "03300330",
    "0DD00DD0"
]

monster_down = [
    "00DDDD00",
    "0D5555D0",
    "D556655D",
    "D555555D",
    "D554455D",
    "0D5555D0",
    "05500550",
    "0DD00DD0"
]

monster_up = [
    "00DDDD00",
    "0D5555D0",
    "D555555D",
    "D555555D",
    "D557755D",
    "0D5555D0",
    "05500550",
    "0DD00DD0"
]

monster_left = [
    "00DDDD00",
    "0D555D00",
    "D5565D00",
    "D5545DD0",
    "D555555D",
    "0D555550",
    "05500550",
    "0DD00DD0"
]

monster_right = [
    "00DDDD00",
    "00D555D0",
    "00D5655D",
    "0DD5455D",
    "D555555D",
    "055555D0",
    "05500550",
    "0DD00DD0"
]

slash_right3 = [
    "11000000",
    "01100000",
    "00110000",
    "00011000",
    "00011000",
    "00110000",
    "01100000",
    "11000000"
]

slash_right2 = [
    "00000000",
    "00000000",
    "00110000",
    "00011000",
    "00011000",
    "00110000",
    "01100000",
    "11000000"
]

slash_right1 = [
    "00000000",
    "00000000",
    "00000000",
    "00000000",
    "00000000",
    "00110000",
    "01100000",
    "11000000"
]

slash_left3 = [
    "00000011",
    "00000110",
    "00001100",
    "00011000",
    "00011000",
    "00001100",
    "00000110",
    "00000011"
]

slash_left2 = [
    "00000011",
    "00000110",
    "00001100",
    "00011000",
    "00011000",
    "00001100",
    "00000000",
    "00000000"
]

slash_left1 = [
    "00000011",
    "00000110",
    "00001100",
    "00000000",
    "00000000",
    "00000000",
    "00000000",
    "00000000"
]

slash_up3 = [
    "00000000",
    "00000000",
    "00000000",
    "00011000",
    "00111100",
    "01100110",
    "11000011",
    "10000001"
]

slash_up2 = [
    "00000000",
    "00000000",
    "00000000",
    "00011000",
    "00111100",
    "00100110",
    "00000011",
    "00000001"
]

slash_up1 = [
    "00000000",
    "00000000",
    "00000000",
    "00000000",
    "00000100",
    "00000110",
    "00000011",
    "00000001"
]

slash_down3 = [
    "10000001",
    "11000011",
    "01100110",
    "00111100",
    "00011000",
    "00000000",
    "00000000",
    "00000000"
]

slash_down2 = [
    "10000000",
    "11000000",
    "01100100",
    "00111100",
    "00011000",
    "00000000",
    "00000000",
    "00000000"
]

slash_down1 = [
    "10000000",
    "11000000",
    "01100000",
    "00100000",
    "00000000",
    "00000000",
    "00000000",
    "00000000"
]


# ============================================================
# SMALL GENERAL-PURPOSE HELPERS
# ============================================================

def clamp(value, minimum, maximum):
    if value < minimum:
        return minimum
    if value > maximum:
        return maximum
    return value


def rectangles_overlap(ax, ay, aw, ah, bx, by, bw, bh):
    return (
        ax < bx + bw and
        ax + aw > bx and
        ay < by + bh and
        ay + ah > by
    )


def sprite_for_direction(direction, up_sprite, down_sprite, left_sprite, right_sprite):
    if direction == "up":
        return up_sprite
    if direction == "down":
        return down_sprite
    if direction == "left":
        return left_sprite
    return right_sprite


def slash_sprite(direction, stage):
    if direction == "up":
        return (slash_up1, slash_up2, slash_up3)[stage]
    if direction == "down":
        return (slash_down1, slash_down2, slash_down3)[stage]
    if direction == "left":
        return (slash_left1, slash_left2, slash_left3)[stage]
    return (slash_right1, slash_right2, slash_right3)[stage]


def slash_position(owner_x, owner_y, direction):
    if direction == "up":
        return owner_x, owner_y - 8
    if direction == "down":
        return owner_x, owner_y + 8
    if direction == "left":
        return owner_x - 8, owner_y
    return owner_x + 8, owner_y


# ============================================================
# PROCEDURAL MAP GENERATION
# ============================================================

def make_filled_map(width, height, value):
    result = []
    for _ in range(height):
        result.append([value] * width)
    return result


def carve_floor(world, tile_x, tile_y):
    """Carve one tile and return 1 only when it changed wall into floor."""
    if 1 <= tile_x < MAP_WIDTH - 1 and 1 <= tile_y < MAP_HEIGHT - 1:
        if world[tile_y][tile_x] == "w":
            world[tile_y][tile_x] = "."
            return 1
    return 0


def carve_room(world, center_x, center_y, room_width, room_height):
    """Carve a room and return the number of newly-created floor tiles."""
    left = center_x - room_width // 2
    top = center_y - room_height // 2
    newly_carved = 0

    for tile_y in range(top, top + room_height):
        for tile_x in range(left, left + room_width):
            newly_carved += carve_floor(world, tile_x, tile_y)

    return newly_carved


def generate_world():
    """
    Fast connected dungeon generator.

    It uses a random walker, but unlike the first version:
    - it never recounts the whole map while generating;
    - every carve operation reports whether it created new floor;
    - it has a maximum step count, so startup cannot run indefinitely.
    """
    world = make_filled_map(MAP_WIDTH, MAP_HEIGHT, "w")

    walker_x = MAP_WIDTH // 2
    walker_y = MAP_HEIGHT // 2

    floor_target = (MAP_WIDTH * MAP_HEIGHT * 34) // 100
    floor_count = 0
    walker_steps = 0
    maximum_walker_steps = MAP_WIDTH * MAP_HEIGHT * 18

    directions = [
        (0, -1),
        (0, 1),
        (-1, 0),
        (1, 0),
    ]

    last_dx = 0
    last_dy = 0

    while floor_count < floor_target and walker_steps < maximum_walker_steps:
        walker_steps += 1
        floor_count += carve_floor(world, walker_x, walker_y)

        # Rooms are useful because they create many new floor tiles at once.
        if random.randint(1, 100) <= 9:
            room_width = random.choice([3, 5, 7])
            room_height = random.choice([3, 5])
            floor_count += carve_room(
                world,
                walker_x,
                walker_y,
                room_width,
                room_height
            )

        if random.randint(1, 100) <= 66 and (last_dx != 0 or last_dy != 0):
            dx = last_dx
            dy = last_dy
        else:
            dx, dy = random.choice(directions)

        candidate_x = walker_x + dx
        candidate_y = walker_y + dy

        if 1 <= candidate_x < MAP_WIDTH - 1 and 1 <= candidate_y < MAP_HEIGHT - 1:
            walker_x = candidate_x
            walker_y = candidate_y
            last_dx = dx
            last_dy = dy
        else:
            # Turn back toward the middle instead of wasting many edge steps.
            if walker_x < MAP_WIDTH // 2:
                walker_x += 1
            elif walker_x > MAP_WIDTH // 2:
                walker_x -= 1

            if walker_y < MAP_HEIGHT // 2:
                walker_y += 1
            elif walker_y > MAP_HEIGHT // 2:
                walker_y -= 1

            last_dx = 0
            last_dy = 0

    return world


def count_floor_tiles(world):
    total = 0
    for row in world:
        for tile in row:
            if tile == ".":
                total += 1
    return total


def get_floor_positions(world):
    positions = []
    for tile_y in range(1, MAP_HEIGHT - 1):
        for tile_x in range(1, MAP_WIDTH - 1):
            if world[tile_y][tile_x] == ".":
                positions.append((tile_x, tile_y))
    return positions


def choose_spawn_tile(floor_positions, avoid_x=None, avoid_y=None, minimum_distance=0):
    while True:
        tile_x, tile_y = random.choice(floor_positions)

        if avoid_x is None:
            return tile_x, tile_y

        distance = abs(tile_x - avoid_x) + abs(tile_y - avoid_y)
        if distance >= minimum_distance:
            return tile_x, tile_y


# ============================================================
# WORLD COLLISION AND LINE OF SIGHT
# ============================================================

def tile_is_wall(world, tile_x, tile_y):
    if tile_x < 0 or tile_x >= MAP_WIDTH:
        return True
    if tile_y < 0 or tile_y >= MAP_HEIGHT:
        return True
    return world[tile_y][tile_x] == "w"


def touches_wall(world, world_x, world_y):
    left_tile = world_x // TILE_SIZE
    right_tile = (world_x + TILE_SIZE - 1) // TILE_SIZE
    top_tile = world_y // TILE_SIZE
    bottom_tile = (world_y + TILE_SIZE - 1) // TILE_SIZE

    return (
        tile_is_wall(world, left_tile, top_tile) or
        tile_is_wall(world, right_tile, top_tile) or
        tile_is_wall(world, left_tile, bottom_tile) or
        tile_is_wall(world, right_tile, bottom_tile)
    )


def clear_line_of_sight(world, start_x, start_y, end_x, end_y):
    """
    Samples points along the line from monster center to player center.
    If any sampled point lands inside a wall tile, vision is blocked.
    """
    start_center_x = start_x + TILE_SIZE // 2
    start_center_y = start_y + TILE_SIZE // 2
    end_center_x = end_x + TILE_SIZE // 2
    end_center_y = end_y + TILE_SIZE // 2

    dx = end_center_x - start_center_x
    dy = end_center_y - start_center_y

    longest_axis = max(abs(dx), abs(dy))
    if longest_axis == 0:
        return True

    sample_count = longest_axis // 4
    if sample_count < 1:
        sample_count = 1

    for sample in range(1, sample_count):
        sample_x = start_center_x + (dx * sample) // sample_count
        sample_y = start_center_y + (dy * sample) // sample_count

        tile_x = sample_x // TILE_SIZE
        tile_y = sample_y // TILE_SIZE

        if tile_is_wall(world, tile_x, tile_y):
            return False

    return True


# ============================================================
# MONSTER CREATION AND AI
# ============================================================

def create_monster(tile_x, tile_y):
    now = time.ticks_ms()

    return {
        "x": tile_x * TILE_SIZE,
        "y": tile_y * TILE_SIZE,
        "health": MONSTER_HEALTH,
        "facing": "down",

        "wander_direction": "down",
        "wander_steps": 0,

        "state": "wander",
        "last_move": now,

        "attacking": False,
        "attack_start": 0,
        "attack_direction": "down",
        "attack_hit_player": False,
        "last_attack_end": time.ticks_add(now, -MONSTER_ATTACK_COOLDOWN),
    }


def choose_wander_direction(monster):
    monster["wander_direction"] = random.choice(["up", "down", "left", "right"])
    monster["wander_steps"] = random.randint(8, 28)
    monster["facing"] = monster["wander_direction"]


def monster_can_see_player(world, monster, player_x, player_y):
    dx = player_x - monster["x"]
    dy = player_y - monster["y"]

    if abs(dx) > MONSTER_VISION_DISTANCE:
        return False
    if abs(dy) > MONSTER_VISION_DISTANCE:
        return False

    return clear_line_of_sight(
        world,
        monster["x"],
        monster["y"],
        player_x,
        player_y
    )


def choose_chase_direction(monster, player_x, player_y):
    dx = player_x - monster["x"]
    dy = player_y - monster["y"]

    if abs(dx) > abs(dy):
        if dx > 0:
            return "right"
        return "left"

    if dy > 0:
        return "down"
    return "up"


def proposed_step(x, y, direction, speed):
    if direction == "up":
        return x, y - speed
    if direction == "down":
        return x, y + speed
    if direction == "left":
        return x - speed, y
    return x + speed, y


def position_hits_other_monster(monster, proposed_x, proposed_y, monsters):
    for other in monsters:
        if other is monster:
            continue

        if rectangles_overlap(
            proposed_x, proposed_y, TILE_SIZE, TILE_SIZE,
            other["x"], other["y"], TILE_SIZE, TILE_SIZE
        ):
            return True

    return False


def monster_is_in_attack_range(monster, player_x, player_y):
    dx = player_x - monster["x"]
    dy = player_y - monster["y"]

    # Attack only when mostly aligned on one axis.
    horizontally_aligned = abs(dy) <= 5 and abs(dx) <= MONSTER_ATTACK_DISTANCE
    vertically_aligned = abs(dx) <= 5 and abs(dy) <= MONSTER_ATTACK_DISTANCE

    return horizontally_aligned or vertically_aligned


def face_player(monster, player_x, player_y):
    monster["facing"] = choose_chase_direction(monster, player_x, player_y)


def begin_monster_attack(monster, player_x, player_y, now):
    face_player(monster, player_x, player_y)
    monster["state"] = "attack"
    monster["attacking"] = True
    monster["attack_start"] = now
    monster["attack_direction"] = monster["facing"]
    monster["attack_hit_player"] = False


def update_monster_attack(monster, player_x, player_y, player_health, now):
    elapsed = time.ticks_diff(now, monster["attack_start"])

    if elapsed >= MONSTER_ATTACK_LENGTH:
        monster["attacking"] = False
        monster["state"] = "chase"
        monster["last_attack_end"] = now
        return player_health

    slash_x, slash_y = slash_position(
        monster["x"],
        monster["y"],
        monster["attack_direction"]
    )

    # Damage is active during the middle and final parts of the swing.
    damage_active = elapsed >= MONSTER_ATTACK_LENGTH // 3

    if (
        damage_active and
        not monster["attack_hit_player"] and
        rectangles_overlap(
            slash_x, slash_y, TILE_SIZE, TILE_SIZE,
            player_x, player_y, TILE_SIZE, TILE_SIZE
        )
    ):
        player_health -= 1
        monster["attack_hit_player"] = True

    return player_health


def update_monster(world, monster, monsters, player_x, player_y, player_health, now):
    if monster["attacking"]:
        player_health = update_monster_attack(
            monster,
            player_x,
            player_y,
            player_health,
            now
        )
        return player_health

    sees_player = monster_can_see_player(world, monster, player_x, player_y)

    if sees_player:
        monster["state"] = "chase"
        monster["facing"] = choose_chase_direction(monster, player_x, player_y)

        if monster_is_in_attack_range(monster, player_x, player_y):
            cooldown_ready = (
                time.ticks_diff(now, monster["last_attack_end"])
                >= MONSTER_ATTACK_COOLDOWN
            )

            if cooldown_ready:
                begin_monster_attack(monster, player_x, player_y, now)

            return player_health
    else:
        monster["state"] = "wander"

    if time.ticks_diff(now, monster["last_move"]) < MONSTER_MOVE_DELAY:
        return player_health

    monster["last_move"] = now

    if monster["state"] == "wander":
        if monster["wander_steps"] <= 0:
            choose_wander_direction(monster)

        move_direction = monster["wander_direction"]
        monster["wander_steps"] -= 1
    else:
        move_direction = choose_chase_direction(monster, player_x, player_y)
        monster["facing"] = move_direction

    proposed_x, proposed_y = proposed_step(
        monster["x"],
        monster["y"],
        move_direction,
        MONSTER_SPEED
    )

    blocked_by_wall = touches_wall(world, proposed_x, proposed_y)
    blocked_by_player = rectangles_overlap(
        proposed_x, proposed_y, TILE_SIZE, TILE_SIZE,
        player_x, player_y, TILE_SIZE, TILE_SIZE
    )
    blocked_by_monster = position_hits_other_monster(
        monster,
        proposed_x,
        proposed_y,
        monsters
    )

    if not blocked_by_wall and not blocked_by_player and not blocked_by_monster:
        monster["x"] = proposed_x
        monster["y"] = proposed_y
    elif monster["state"] == "wander":
        monster["wander_steps"] = 0

    return player_health


# ============================================================
# PLAYER ATTACK
# ============================================================

def begin_player_attack(player_attack, player_x, player_y, facing, now):
    player_attack["active"] = True
    player_attack["start"] = now
    player_attack["direction"] = facing
    player_attack["hit_monsters"] = []

    slash_x, slash_y = slash_position(player_x, player_y, facing)
    player_attack["x"] = slash_x
    player_attack["y"] = slash_y


def update_player_attack(player_attack, monsters, now):
    if not player_attack["active"]:
        return

    elapsed = time.ticks_diff(now, player_attack["start"])

    if elapsed >= PLAYER_ATTACK_LENGTH:
        player_attack["active"] = False
        return

    damage_active = elapsed >= PLAYER_ATTACK_LENGTH // 3

    if not damage_active:
        return

    slash_x = player_attack["x"]
    slash_y = player_attack["y"]

    for monster in monsters:
        if monster in player_attack["hit_monsters"]:
            continue

        if rectangles_overlap(
            slash_x, slash_y, TILE_SIZE, TILE_SIZE,
            monster["x"], monster["y"], TILE_SIZE, TILE_SIZE
        ):
            monster["health"] -= 1
            player_attack["hit_monsters"].append(monster)


# ============================================================
# CAMERA AND DRAWING
# ============================================================

def calculate_camera(player_x, player_y):
    desired_x = player_x + TILE_SIZE // 2 - SCREEN_WIDTH // 2
    desired_y = player_y + TILE_SIZE // 2 - SCREEN_HEIGHT // 2

    max_camera_x = MAP_WIDTH * TILE_SIZE - SCREEN_WIDTH
    max_camera_y = MAP_HEIGHT * TILE_SIZE - SCREEN_HEIGHT

    camera_x = clamp(desired_x, 0, max_camera_x)
    camera_y = clamp(desired_y, 0, max_camera_y)

    return camera_x, camera_y


def draw_world(oled, world, camera_x, camera_y):
    """
    Draw visible terrain with framebuffer rectangle operations.

    The original version called draw_color_sprite for every visible tile.
    That meant roughly 17,000 Python-level pixel decisions per frame.
    fill_rect and line execute inside the framebuffer driver and are far faster.
    """
    first_tile_x = camera_x // TILE_SIZE
    first_tile_y = camera_y // TILE_SIZE

    pixel_offset_x = -(camera_x % TILE_SIZE)
    pixel_offset_y = -(camera_y % TILE_SIZE)

    for view_y in range(VIEW_TILES_Y + 2):
        tile_y = first_tile_y + view_y
        if tile_y < 0 or tile_y >= MAP_HEIGHT:
            continue

        screen_y = pixel_offset_y + view_y * TILE_SIZE

        for view_x in range(VIEW_TILES_X + 2):
            tile_x = first_tile_x + view_x
            if tile_x < 0 or tile_x >= MAP_WIDTH:
                continue

            screen_x = pixel_offset_x + view_x * TILE_SIZE

            if world[tile_y][tile_x] == "w":
                oled.fill_rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE, GRAY)
                oled.hline(screen_x, screen_y + 3, TILE_SIZE, DARK_GRAY)

                # Alternate the short vertical mortar seam by row.
                if tile_y & 1:
                    oled.vline(screen_x + 2, screen_y, 3, DARK_GRAY)
                    oled.vline(screen_x + 6, screen_y + 4, 4, DARK_GRAY)
                else:
                    oled.vline(screen_x + 5, screen_y, 3, DARK_GRAY)
                    oled.vline(screen_x + 2, screen_y + 4, 4, DARK_GRAY)
            else:
                oled.fill_rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE, DARK_GRAY)

                # One tiny deterministic floor fleck; no random call per frame.
                fleck_x = screen_x + ((tile_x * 3 + tile_y) % 6) + 1
                fleck_y = screen_y + ((tile_y * 5 + tile_x) % 6) + 1
                oled.pixel(fleck_x, fleck_y, GRAY)


def draw_monster(oled, monster, camera_x, camera_y):
    screen_x = monster["x"] - camera_x
    screen_y = monster["y"] - camera_y

    if (
        screen_x <= -TILE_SIZE or screen_x >= SCREEN_WIDTH or
        screen_y <= -TILE_SIZE or screen_y >= SCREEN_HEIGHT
    ):
        return

    sprite = sprite_for_direction(
        monster["facing"],
        monster_up,
        monster_down,
        monster_left,
        monster_right
    )

    draw_color_sprite(oled, sprite, screen_x, screen_y)


def draw_attack(oled, world_x, world_y, direction, start_time, length, camera_x, camera_y, now):
    elapsed = time.ticks_diff(now, start_time)

    if elapsed < length // 3:
        stage = 0
    elif elapsed < (length * 2) // 3:
        stage = 1
    else:
        stage = 2

    sprite = slash_sprite(direction, stage)

    draw_color_sprite(
        oled,
        sprite,
        world_x - camera_x,
        world_y - camera_y
    )


def draw_health(oled, health):
    # Tiny compact HUD: one 5x5 block per health point.
    for index in range(PLAYER_MAX_HEALTH):
        x = 2 + index * 7

        if index < health:
            oled.fill_rect(x, 2, 5, 5, HEALTH_GREEN)
        else:
            oled.rect(x, 2, 5, 5, DARK_GRAY)


def draw_scene(
    oled,
    world,
    player_x,
    player_y,
    player_facing,
    player_health,
    monsters,
    player_attack,
    camera_x,
    camera_y,
    now
):
    oled.fill(BLACK)

    draw_world(oled, world, camera_x, camera_y)

    for monster in monsters:
        draw_monster(oled, monster, camera_x, camera_y)

    player_sprite = sprite_for_direction(
        player_facing,
        player_up,
        player_down,
        player_left,
        player_right
    )

    draw_color_sprite(
        oled,
        player_sprite,
        player_x - camera_x,
        player_y - camera_y
    )

    # Draw monster sword attacks above bodies.
    for monster in monsters:
        if monster["attacking"]:
            attack_x, attack_y = slash_position(
                monster["x"],
                monster["y"],
                monster["attack_direction"]
            )

            draw_attack(
                oled,
                attack_x,
                attack_y,
                monster["attack_direction"],
                monster["attack_start"],
                MONSTER_ATTACK_LENGTH,
                camera_x,
                camera_y,
                now
            )

    # Draw player sword last so it is very easy to see.
    if player_attack["active"]:
        draw_attack(
            oled,
            player_attack["x"],
            player_attack["y"],
            player_attack["direction"],
            player_attack["start"],
            PLAYER_ATTACK_LENGTH,
            camera_x,
            camera_y,
            now
        )

    draw_health(oled, player_health)
    show_display(oled)


# ============================================================
# GAME SETUP, DEATH SCREEN, AND MAIN LOOP
# ============================================================

def create_game():
    world = generate_world()
    floor_positions = get_floor_positions(world)

    player_tile_x, player_tile_y = choose_spawn_tile(floor_positions)

    player_x = player_tile_x * TILE_SIZE
    player_y = player_tile_y * TILE_SIZE

    monsters = []
    used_tiles = {(player_tile_x, player_tile_y)}

    while len(monsters) < MONSTER_COUNT:
        monster_tile_x, monster_tile_y = choose_spawn_tile(
            floor_positions,
            player_tile_x,
            player_tile_y,
            minimum_distance=9
        )

        tile_position = (monster_tile_x, monster_tile_y)

        if tile_position in used_tiles:
            continue

        used_tiles.add(tile_position)
        monsters.append(create_monster(monster_tile_x, monster_tile_y))

    return world, player_x, player_y, monsters


def draw_centered_text(oled, text, y, color):
    x = (SCREEN_WIDTH - len(text) * 8) // 2
    oled.text(text, x, y, color)


def show_death_screen(oled, button_G):
    oled.fill(BLACK)
    draw_centered_text(oled, "YOU WERE DEFEATED", 25, RED)
    draw_centered_text(oled, "GREEN: NEW MAP", 43, WHITE)
    show_display(oled)

    while button_G.value() == 1:
        time.sleep(0.02)

    while button_G.value() == 0:
        time.sleep(0.02)


def main(oled, controls, settings):
    button_G = ButtonAdapter(controls["green"])

    while True:
        world, player_x, player_y, monsters = create_game()

        player_health = PLAYER_MAX_HEALTH
        player_facing = "down"

        player_attack = {
            "active": False,
            "start": 0,
            "direction": "down",
            "x": 0,
            "y": 0,
            "hit_monsters": [],
            "last_end": time.ticks_add(
                time.ticks_ms(),
                -PLAYER_ATTACK_COOLDOWN
            ),
        }

        green_was_down = False

        while player_health > 0:
            frame_start = time.ticks_ms()
            now = frame_start

            left, right, up, down = controls["joystick"]()

            proposed_x = player_x
            proposed_y = player_y

            # One axis at a time prevents accidental diagonal speed boosts.
            if left:
                proposed_x -= PLAYER_SPEED
                player_facing = "left"
            elif right:
                proposed_x += PLAYER_SPEED
                player_facing = "right"
            elif up:
                proposed_y -= PLAYER_SPEED
                player_facing = "up"
            elif down:
                proposed_y += PLAYER_SPEED
                player_facing = "down"

            if proposed_x != player_x:
                if not touches_wall(world, proposed_x, player_y):
                    player_x = proposed_x

            if proposed_y != player_y:
                if not touches_wall(world, player_x, proposed_y):
                    player_y = proposed_y

            green_now_down = button_G.value() == 0

            if green_now_down and not green_was_down:
                attack_ready = (
                    not player_attack["active"] and
                    time.ticks_diff(now, player_attack["last_end"])
                    >= PLAYER_ATTACK_COOLDOWN
                )

                if attack_ready:
                    begin_player_attack(
                        player_attack,
                        player_x,
                        player_y,
                        player_facing,
                        now
                    )

            green_was_down = green_now_down

            attack_was_active = player_attack["active"]
            update_player_attack(player_attack, monsters, now)

            if attack_was_active and not player_attack["active"]:
                player_attack["last_end"] = now

            for monster in monsters:
                player_health = update_monster(
                    world,
                    monster,
                    monsters,
                    player_x,
                    player_y,
                    player_health,
                    now
                )

            # Remove monsters only after every update has finished.
            living_monsters = []
            for monster in monsters:
                if monster["health"] > 0:
                    living_monsters.append(monster)
            monsters = living_monsters

            camera_x, camera_y = calculate_camera(player_x, player_y)

            draw_scene(
                oled,
                world,
                player_x,
                player_y,
                player_facing,
                player_health,
                monsters,
                player_attack,
                camera_x,
                camera_y,
                now
            )

            elapsed = time.ticks_diff(time.ticks_ms(), frame_start)
            remaining = TARGET_FRAME_MS - elapsed

            if remaining > 0:
                time.sleep_ms(remaining)

        show_death_screen(oled, button_G)


