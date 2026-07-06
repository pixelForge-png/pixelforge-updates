import time
import gc
from helpers.mp_client import MultiplayerClient
from helpers.forge_sprites import draw_fighter, draw_blast

SCREEN_W = 160
SCREEN_H = 80
WORLD_W = 280

BLACK = 0
WHITE = 65535
GRAY = 33808
CYAN = 2047
YELLOW = 65504

PLAYER_W = 12
PLAYER_H = 18

GRAVITY = 1
MAX_FALL = 8

SYNC_MS = 45
FRAME_MS = 35

# Player indexes
PX = 0
PY = 1
PVX = 2
PVY = 3
PFACING = 4
PONGROUND = 5
PFALLS = 6
PCHAR = 7
PSTOCKS = 8
PDAMAGE = 9
PACTION = 10
PTIMER = 11
PATKCD = 12
PHITSTUN = 13
PHITDONE = 14
PSPECCD = 15
PSPECTIMER = 16
PSPECDONE = 17
PCROUCH = 18
PINVINCIBLE = 19
PSPAWNWAIT = 20
PBLASTX = 21
PBLASTY = 22
PBLASTTIMER = 23
PSPECDIR = 24
PJUMPS = 25
PUPHELD = 26

ACTION_IDLE = 0
ACTION_RUN = 1
ACTION_JUMP = 2
ACTION_ATTACK = 3
ACTION_HURT = 4
ACTION_SPECIAL = 5
ACTION_CROUCH = 6
ACTION_SPAWN = 7

SPEC_SIDE = 0
SPEC_UP = 1
SPEC_DOWN = 2

PAUSE_PLAY = 0
PAUSE_PAUSED = 1
PAUSE_QUIT = 2

CHARACTERS = [
    {
        "id": "kael",
        "name": "Kael",
        "title": "Ironblade",
        "short": "KAE",
        "speed": 3,
        "jump": -9,
        "weight": 1,
        "attack_damage": 10,
        "attack_knockback": 5,
        "special_cooldown": 45
    },
    {
        "id": "nyra",
        "name": "Nyra",
        "title": "Swiftfang",
        "short": "NYR",
        "speed": 4,
        "jump": -10,
        "weight": 0,
        "attack_damage": 8,
        "attack_knockback": 4,
        "special_cooldown": 32
    },
    {
        "id": "brugo",
        "name": "Brugo",
        "title": "Stonehelm",
        "short": "BRU",
        "speed": 2,
        "jump": -8,
        "weight": 2,
        "attack_damage": 14,
        "attack_knockback": 7,
        "special_cooldown": 60
    }
]

MAPS = [
    {
        "id": "stone_bridge",
        "name": "Stone Bridge",
        "platforms": [
            [40, 62, 200, 4]
        ],
        "spawn1": [95, 35],
        "spawn2": [175, 35],
        "death_y": 104
    },
    {
        "id": "sky_ruins",
        "name": "Sky Ruins",
        "platforms": [
            [65, 64, 150, 4],
            [18, 42, 58, 4],
            [204, 42, 58, 4]
        ],
        "spawn1": [95, 35],
        "spawn2": [175, 35],
        "death_y": 104
    },
    {
        "id": "lava_pit",
        "name": "Lava Pit",
        "platforms": [
            [82, 62, 116, 4],
            [20, 47, 58, 4],
            [202, 47, 58, 4]
        ],
        "spawn1": [108, 35],
        "spawn2": [160, 35],
        "death_y": 88
    }
]


def clamp(value, low, high):
    if value < low:
        return low
    if value > high:
        return high
    return value


def center_text(oled, text, y, color=WHITE):
    text = str(text)
    x = (SCREEN_W - len(text) * 8) // 2
    oled.text(text, x, y, color)


def wait_screen(oled, title, line1="", line2=""):
    oled.fill(BLACK)
    center_text(oled, title, 10, WHITE)
    center_text(oled, line1, 32, WHITE)
    center_text(oled, line2, 52, CYAN)
    oled.show()


def wait_button_release(controls):
    while (
        controls["green"]() or
        controls["yellow"]() or
        controls["blue"]() or
        controls["red"]()
    ):
        time.sleep(0.02)


def parse_int(value, default=0):
    try:
        return int(value)
    except:
        return default


def parse_peer_message(msg):
    if msg == None:
        return ""

    if not msg.startswith("PEER|"):
        return ""

    parts = msg.split("|", 2)

    if len(parts) < 3:
        return ""

    return parts[2]


def get_character(char_index):
    if char_index < 0:
        char_index = 0
    if char_index >= len(CHARACTERS):
        char_index = 0
    return CHARACTERS[char_index]


def get_map(map_index):
    if map_index < 0:
        map_index = 0
    if map_index >= len(MAPS):
        map_index = 0
    return MAPS[map_index]


def get_camera_x(local_player):
    target = local_player[PX] + PLAYER_W // 2 - SCREEN_W // 2
    return clamp(target, 0, WORLD_W - SCREEN_W)


def world_to_screen_x(x, camera_x):
    return int(x - camera_x)


def draw_line(oled, x1, y1, x2, y2, color):
    dx = abs(x2 - x1)
    dy = -abs(y2 - y1)

    if x1 < x2:
        sx = 1
    else:
        sx = -1

    if y1 < y2:
        sy = 1
    else:
        sy = -1

    err = dx + dy

    while True:
        if x1 >= 0 and x1 < SCREEN_W and y1 >= 0 and y1 < SCREEN_H:
            oled.pixel(x1, y1, color)

        if x1 == x2 and y1 == y2:
            break

        e2 = 2 * err

        if e2 >= dy:
            err += dy
            x1 += sx

        if e2 <= dx:
            err += dx
            y1 += sy


def rects_touch(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b

    if ax + aw < bx:
        return False
    if ax > bx + bw:
        return False
    if ay + ah < by:
        return False
    if ay > by + bh:
        return False

    return True


def draw_preview_fighter(oled, x, y, char_index):
    char = get_character(char_index)
    tick = time.ticks_ms() // 40
    draw_fighter(oled, char["id"], x, y, 1, ACTION_IDLE, tick, WHITE)
    draw_fighter(oled, char["id"], x + 1, y, 1, ACTION_IDLE, tick, WHITE)


def character_select(oled, controls, role):
    index = 0
    last_move = time.ticks_ms()

    while True:
        char = get_character(index)

        oled.fill(BLACK)
        center_text(oled, "CHOOSE FIGHTER", 3, CYAN)

        if role == "host":
            oled.text("PLAYER 1", 8, 16, WHITE)
        else:
            oled.text("PLAYER 2", 8, 16, WHITE)

        oled.text("<", 3, 39, YELLOW)
        oled.text(">", 150, 39, YELLOW)

        oled.text(char["name"], 18, 30, WHITE)
        oled.text(char["title"], 18, 42, CYAN)

        stat_line = "SPD" + str(char["speed"]) + " JMP" + str(abs(char["jump"]))
        oled.text(stat_line, 18, 55, WHITE)

        draw_preview_fighter(oled, 133, 60, index)

        oled.text("G=Pick", 2, 70, WHITE)
        oled.text("Y=Back", 104, 70, GRAY)

        oled.show()

        left, right, up, down = controls["joystick"]()
        now = time.ticks_ms()

        if time.ticks_diff(now, last_move) > 220:
            if left:
                index -= 1
                if index < 0:
                    index = len(CHARACTERS) - 1
                last_move = now

            elif right:
                index += 1
                if index >= len(CHARACTERS):
                    index = 0
                last_move = now

        if controls["green"]():
            wait_button_release(controls)
            return index

        if controls["yellow"]():
            wait_button_release(controls)
            return None

        time.sleep(0.03)


def draw_map_preview(oled, map_index):
    m = get_map(map_index)

    for p in m["platforms"]:
        x = p[0] * SCREEN_W // WORLD_W
        y = p[1]
        w = p[2] * SCREEN_W // WORLD_W

        if w < 2:
            w = 2

        oled.fill_rect(x, y, w, p[3], WHITE)


def map_select(oled, controls):
    index = 0
    last_move = time.ticks_ms()

    while True:
        m = get_map(index)

        oled.fill(BLACK)
        center_text(oled, "HOST CHOOSE MAP", 3, CYAN)

        oled.text("<", 3, 35, YELLOW)
        oled.text(">", 150, 35, YELLOW)

        center_text(oled, m["name"], 18, WHITE)
        draw_map_preview(oled, index)

        oled.text("G=Pick", 2, 70, WHITE)
        oled.text("Y=Back", 104, 70, GRAY)

        oled.show()

        left, right, up, down = controls["joystick"]()
        now = time.ticks_ms()

        if time.ticks_diff(now, last_move) > 220:
            if left:
                index -= 1
                if index < 0:
                    index = len(MAPS) - 1
                last_move = now

            elif right:
                index += 1
                if index >= len(MAPS):
                    index = 0
                last_move = now

        if controls["green"]():
            wait_button_release(controls)
            return index

        if controls["yellow"]():
            wait_button_release(controls)
            return None

        time.sleep(0.03)


def setup_sync(oled, ws, controls, role, chosen_char, chosen_map):
    while True:
        if role == "host":
            packet = "SETUP|" + str(chosen_char) + "|" + str(chosen_map)
            wait_screen(oled, "SETUP", "WAIT JOINER", get_map(chosen_map)["name"])
        else:
            packet = "SETUP|" + str(chosen_char) + "|-1"
            wait_screen(oled, "SETUP", "WAIT MAP", "FROM HOST")

        reply = ws.sync(packet)
        peer = parse_peer_message(reply)

        if peer.startswith("SETUP|"):
            parts = peer.split("|")

            if len(parts) >= 3:
                peer_char = parse_int(parts[1], 0)
                peer_map = parse_int(parts[2], -1)

                if role == "host":
                    return peer_char, chosen_map

                if peer_map >= 0:
                    return peer_char, peer_map

        if controls["yellow"]():
            wait_button_release(controls)
            return None, None

        time.sleep(0.08)


def make_player(x, y, facing, char_index):
    return [
        x, y, 0, 0, facing, 0, 0,
        char_index, 3, 0,
        ACTION_SPAWN, 0,
        0, 0, 0,
        0, 0, 0,
        0, 45, 35,
        x, y, 0,
        SPEC_SIDE,
        2, 0
    ]


def make_packet(player, hit_id, hit_damage, hit_kbx, hit_kby, pause_state, map_index):
    values = []

    for i in range(27):
        values.append(str(int(player[i])))

    values.append(str(int(hit_id)))
    values.append(str(int(hit_damage)))
    values.append(str(int(hit_kbx)))
    values.append(str(int(hit_kby)))
    values.append(str(int(pause_state)))
    values.append(str(int(map_index)))

    return ",".join(values)


def parse_packet(data, old_player):
    try:
        parts = data.split(",")

        if len(parts) < 33:
            return old_player, 0, 0, 0, 0, PAUSE_PLAY, 0

        player = []

        for i in range(27):
            player.append(parse_int(parts[i], old_player[i]))

        hit_id = parse_int(parts[27], 0)
        hit_damage = parse_int(parts[28], 0)
        hit_kbx = parse_int(parts[29], 0)
        hit_kby = parse_int(parts[30], 0)
        pause_state = parse_int(parts[31], PAUSE_PLAY)
        map_index = parse_int(parts[32], 0)

        return player, hit_id, hit_damage, hit_kbx, hit_kby, pause_state, map_index

    except:
        return old_player, 0, 0, 0, 0, PAUSE_PLAY, 0


def smooth_correct_player(local_player, real_player):
    diff_x = real_player[PX] - local_player[PX]
    diff_y = real_player[PY] - local_player[PY]

    if diff_x > 35 or diff_x < -35 or diff_y > 25 or diff_y < -25:
        local_player[PX] = real_player[PX]
        local_player[PY] = real_player[PY]
    else:
        local_player[PX] = local_player[PX] + diff_x // 3
        local_player[PY] = local_player[PY] + diff_y // 3

    for i in range(2, 27):
        local_player[i] = real_player[i]


def start_death_blast(player):
    player[PBLASTX] = player[PX] + PLAYER_W // 2
    player[PBLASTY] = player[PY] + PLAYER_H // 2
    player[PBLASTTIMER] = 12


def respawn_player(player, player_num, map_index):
    if player_num == 1:
        player[PFACING] = 1
    else:
        player[PFACING] = -1

    player[PX] = WORLD_W // 2 - PLAYER_W // 2
    player[PY] = 5
    player[PVX] = 0
    player[PVY] = 0

    player[PONGROUND] = 0
    player[PDAMAGE] = 0
    player[PACTION] = ACTION_SPAWN
    player[PTIMER] = 0
    player[PATKCD] = 0
    player[PHITSTUN] = 0
    player[PHITDONE] = 0
    player[PSPECCD] = 0
    player[PSPECTIMER] = 0
    player[PSPECDONE] = 0
    player[PCROUCH] = 0
    player[PINVINCIBLE] = 60
    player[PSPAWNWAIT] = 35
    player[PSPECDIR] = SPEC_SIDE
    player[PJUMPS] = 2
    player[PUPHELD] = 0


def start_attack(player):
    if player[PATKCD] > 0:
        return
    if player[PHITSTUN] > 0:
        return
    if player[PACTION] == ACTION_ATTACK or player[PACTION] == ACTION_SPECIAL:
        return

    player[PACTION] = ACTION_ATTACK
    player[PTIMER] = 12
    player[PATKCD] = 18
    player[PHITDONE] = 0


def start_directional_special(player, left, right, up, down):
    char = get_character(player[PCHAR])
    char_id = char["id"]

    if player[PSPECCD] > 0:
        return
    if player[PHITSTUN] > 0:
        return
    if player[PACTION] == ACTION_ATTACK or player[PACTION] == ACTION_SPECIAL:
        return

    if left:
        player[PFACING] = -1
    elif right:
        player[PFACING] = 1

    player[PACTION] = ACTION_SPECIAL
    player[PTIMER] = 18
    player[PSPECTIMER] = 18
    player[PSPECCD] = char["special_cooldown"]
    player[PSPECDONE] = 0

    # UP SPECIALS: recovery moves
    if up:
        player[PSPECDIR] = SPEC_UP

        if char_id == "kael":
            # Rising Slash
            player[PVY] = -12
            player[PVX] = player[PFACING] * 2
            player[PTIMER] = 20

        elif char_id == "nyra":
            # Sky Needle
            player[PVY] = -15
            player[PVX] = player[PFACING] * 3
            player[PTIMER] = 18

        else:
            # Stone Uppercut
            player[PVY] = -10
            player[PVX] = player[PFACING]
            player[PTIMER] = 22

    # DOWN SPECIALS
    elif down:
        player[PSPECDIR] = SPEC_DOWN

        if char_id == "kael":
            # Guard Break
            player[PVX] = 0

            if player[PONGROUND] == 0:
                player[PVY] = 7

            player[PTIMER] = 16

        elif char_id == "nyra":
            # Shadow Drop
            player[PVX] = player[PFACING] * 4
            player[PVY] = 7
            player[PTIMER] = 16

        else:
            # Earthquake
            player[PVX] = 0

            if player[PONGROUND] == 0:
                player[PVY] = 10
            else:
                player[PVY] = 0

            player[PTIMER] = 24

    # SIDE SPECIALS
    else:
        player[PSPECDIR] = SPEC_SIDE

        if char_id == "kael":
            # Blade Dash
            player[PVX] = player[PFACING] * 7
            player[PVY] = 0
            player[PTIMER] = 18

        elif char_id == "nyra":
            # Shadow Step
            player[PVX] = player[PFACING] * 10
            player[PVY] = 0
            player[PTIMER] = 14

        else:
            # Boulder Charge
            player[PVX] = player[PFACING] * 5
            player[PVY] = 0
            player[PTIMER] = 24


def tick_timers(player):
    if player[PTIMER] > 0:
        player[PTIMER] -= 1

    if player[PATKCD] > 0:
        player[PATKCD] -= 1

    if player[PHITSTUN] > 0:
        player[PHITSTUN] -= 1

    if player[PSPECCD] > 0:
        player[PSPECCD] -= 1

    if player[PSPECTIMER] > 0:
        player[PSPECTIMER] -= 1

    if player[PBLASTTIMER] > 0:
        player[PBLASTTIMER] -= 1

    if player[PINVINCIBLE] > 0:
        player[PINVINCIBLE] -= 1

    if player[PACTION] == ACTION_ATTACK and player[PTIMER] <= 0:
        player[PACTION] = ACTION_IDLE
        player[PHITDONE] = 0

    if player[PACTION] == ACTION_SPECIAL and player[PTIMER] <= 0:
        player[PACTION] = ACTION_IDLE
        player[PSPECDONE] = 0
        player[PSPECTIMER] = 0
        player[PSPECDIR] = SPEC_SIDE

    if player[PACTION] == ACTION_HURT and player[PHITSTUN] <= 0:
        player[PACTION] = ACTION_IDLE


def apply_special_motion(player):
    char = get_character(player[PCHAR])
    char_id = char["id"]

    if player[PACTION] != ACTION_SPECIAL:
        return

    spec_dir = player[PSPECDIR]

    # UP SPECIAL MOTION
    if spec_dir == SPEC_UP:
        if char_id == "kael":
            if player[PTIMER] > 9:
                player[PVY] = -7
                player[PVX] = player[PFACING] * 2

        elif char_id == "nyra":
            if player[PTIMER] > 8:
                player[PVY] = -9
                player[PVX] = player[PFACING] * 3

        else:
            if player[PTIMER] > 11:
                player[PVY] = -5
                player[PVX] = player[PFACING]

        return

    # DOWN SPECIAL MOTION
    if spec_dir == SPEC_DOWN:
        if char_id == "kael":
            if player[PONGROUND] == 0:
                player[PVY] += 1
            player[PVX] = 0

        elif char_id == "nyra":
            if player[PTIMER] > 6:
                player[PVX] = player[PFACING] * 4
                player[PVY] = 7
            else:
                player[PVX] = 0

        else:
            if player[PONGROUND] == 0:
                player[PVY] += 3
            player[PVX] = 0

        return

    # SIDE SPECIAL MOTION
    if char_id == "kael":
        if player[PTIMER] > 5:
            if player[PVX] == 0:
                player[PVX] = player[PFACING] * 7
        else:
            player[PVX] = 0

    elif char_id == "nyra":
        if player[PTIMER] > 5:
            if player[PVX] == 0:
                player[PVX] = player[PFACING] * 9
        else:
            player[PVX] = 0

    else:
        if player[PTIMER] > 8:
            if player[PVX] == 0:
                player[PVX] = player[PFACING] * 4
        else:
            player[PVX] = 0


def apply_player_input(player, left, right, up, down, attack, special):
    char = get_character(player[PCHAR])
    speed = char["speed"]
    jump_power = char["jump"]

    if player[PSPAWNWAIT] > 0:
        if left or right or up or down:
            player[PSPAWNWAIT] = 0

    # One jump per up press.
    jump_pressed = False

    if up and player[PUPHELD] == 0:
        jump_pressed = True
        player[PUPHELD] = 1

    if not up:
        player[PUPHELD] = 0

    if down and player[PONGROUND] == 1 and player[PACTION] != ACTION_ATTACK and player[PACTION] != ACTION_SPECIAL:
        player[PCROUCH] = 1
        player[PACTION] = ACTION_CROUCH
    else:
        player[PCROUCH] = 0

    if special:
        start_directional_special(player, left, right, up, down)

    elif attack:
        start_attack(player)

    if player[PHITSTUN] > 0:
        return

    if player[PACTION] == ACTION_ATTACK:
        player[PVX] = 0
        return

    if player[PACTION] == ACTION_SPECIAL:
        apply_special_motion(player)
        return

    if player[PCROUCH] == 1:
        player[PVX] = 0
        return

    moving = False

    if left:
        player[PVX] = -speed
        player[PFACING] = -1
        moving = True

    elif right:
        player[PVX] = speed
        player[PFACING] = 1
        moving = True

    else:
        player[PVX] = 0

    # Double jump system.
    if jump_pressed:
        if player[PONGROUND] == 1:
            player[PVY] = jump_power
            player[PONGROUND] = 0
            player[PJUMPS] = 1

        elif player[PJUMPS] > 0:
            player[PVY] = jump_power
            player[PJUMPS] -= 1
            player[PONGROUND] = 0

    if player[PONGROUND] == 0:
        player[PACTION] = ACTION_JUMP
    elif moving:
        player[PACTION] = ACTION_RUN
    else:
        player[PACTION] = ACTION_IDLE


def collide_platforms(player, old_y, map_index):
    m = get_map(map_index)

    player_bottom_old = old_y + PLAYER_H
    player_bottom_new = player[PY] + PLAYER_H

    player_left = player[PX]
    player_right = player[PX] + PLAYER_W

    for p in m["platforms"]:
        px, py, pw, ph = p

        touching_x = (
            player_right >= px and
            player_left <= px + pw
        )

        falling = player[PVY] >= 0

        crossed_platform = (
            player_bottom_old <= py and
            player_bottom_new >= py
        )

        if touching_x and falling and crossed_platform:
            player[PY] = py - PLAYER_H
            player[PVY] = 0
            player[PONGROUND] = 1
            player[PJUMPS] = 2
            return

    player[PONGROUND] = 0


def update_physics(player, player_num, map_index):
    old_y = player[PY]

    if player[PSPAWNWAIT] > 0:
        player[PSPAWNWAIT] -= 1

        if player[PVX] != 0:
            player[PSPAWNWAIT] = 0

        if player[PSPAWNWAIT] > 0:
            player[PVY] = 0
            return
        else:
            player[PACTION] = ACTION_JUMP

    player[PVY] += GRAVITY

    if player[PVY] > MAX_FALL:
        player[PVY] = MAX_FALL

    player[PX] += player[PVX]
    player[PY] += player[PVY]

    player[PX] = clamp(player[PX], -35, WORLD_W + 35)

    collide_platforms(player, old_y, map_index)

    m = get_map(map_index)

    if player[PY] > m["death_y"]:
        start_death_blast(player)

        player[PSTOCKS] -= 1

        if player[PSTOCKS] < 0:
            player[PSTOCKS] = 0

        player[PFALLS] += 1

        if player[PSTOCKS] > 0:
            respawn_player(player, player_num, map_index)


def predict_remote_physics(player, map_index):
    old_y = player[PY]

    if player[PACTION] == ACTION_SPECIAL:
        apply_special_motion(player)

    if player[PSPAWNWAIT] > 0:
        return

    player[PVY] += GRAVITY

    if player[PVY] > MAX_FALL:
        player[PVY] = MAX_FALL

    player[PX] += player[PVX]
    player[PY] += player[PVY]

    player[PX] = clamp(player[PX], -35, WORLD_W + 35)

    collide_platforms(player, old_y, map_index)


def player_rect(player):
    if player[PCROUCH] == 1:
        return [player[PX], player[PY] + 9, PLAYER_W, PLAYER_H - 9]

    return [player[PX], player[PY], PLAYER_W, PLAYER_H]


def attack_active(player):
    return player[PACTION] == ACTION_ATTACK and player[PTIMER] <= 9 and player[PTIMER] >= 4


def special_active(player):
    if player[PACTION] != ACTION_SPECIAL:
        return False

    if player[PSPECDIR] == SPEC_UP:
        return player[PTIMER] <= 14 and player[PTIMER] >= 5

    if player[PSPECDIR] == SPEC_DOWN:
        return player[PTIMER] <= 12 and player[PTIMER] >= 3

    return player[PTIMER] <= 13 and player[PTIMER] >= 5


def attack_rect(player):
    x = player[PX]
    y = player[PY]

    if player[PFACING] >= 0:
        return [x + PLAYER_W, y + 2, 18, 7]
    else:
        return [x - 18, y + 2, 18, 7]


def special_rect(player):
    x = player[PX]
    y = player[PY]
    char = get_character(player[PCHAR])
    char_id = char["id"]
    spec_dir = player[PSPECDIR]

    # UP SPECIAL HITBOXES
    if spec_dir == SPEC_UP:
        if char_id == "kael":
            return [x - 8, y - 24, PLAYER_W + 16, 34]

        elif char_id == "nyra":
            return [x - 6, y - 32, PLAYER_W + 12, 42]

        else:
            return [x - 16, y - 20, PLAYER_W + 32, 30]

    # DOWN SPECIAL HITBOXES
    if spec_dir == SPEC_DOWN:
        if char_id == "kael":
            return [x - 24, y + PLAYER_H - 6, PLAYER_W + 48, 12]

        elif char_id == "nyra":
            if player[PFACING] >= 0:
                return [x + PLAYER_W, y + 5, 30, 14]
            else:
                return [x - 30, y + 5, 30, 14]

        else:
            return [x - 50, y + PLAYER_H - 6, PLAYER_W + 100, 14]

    # SIDE SPECIAL HITBOXES
    if char_id == "kael":
        if player[PFACING] >= 0:
            return [x + PLAYER_W, y + 1, 32, 14]
        else:
            return [x - 32, y + 1, 32, 14]

    elif char_id == "nyra":
        if player[PFACING] >= 0:
            return [x + PLAYER_W, y, 40, 16]
        else:
            return [x - 40, y, 40, 16]

    else:
        if player[PFACING] >= 0:
            return [x + PLAYER_W, y + 3, 30, 16]
        else:
            return [x - 30, y + 3, 30, 16]


def check_attack_hit(attacker, victim):
    if victim[PINVINCIBLE] > 0:
        return ""

    if attack_active(attacker) and attacker[PHITDONE] == 0:
        if rects_touch(attack_rect(attacker), player_rect(victim)):
            attacker[PHITDONE] = 1
            return "attack"

    if special_active(attacker) and attacker[PSPECDONE] == 0:
        if rects_touch(special_rect(attacker), player_rect(victim)):
            attacker[PSPECDONE] = 1
            return "special"

    return ""


def apply_hit(player, damage, kbx, kby):
    if player[PINVINCIBLE] > 0:
        return

    player[PDAMAGE] += damage
    player[PVX] = kbx
    player[PVY] = kby
    player[PONGROUND] = 0
    player[PACTION] = ACTION_HURT
    player[PHITSTUN] = 10 + abs(kbx) // 2
    player[PTIMER] = player[PHITSTUN]
    player[PCROUCH] = 0


def create_hit_event(attacker, victim, next_hit_id, hit_type):
    char = get_character(attacker[PCHAR])
    victim_char = get_character(victim[PCHAR])

    char_id = char["id"]
    damage = char["attack_damage"]
    base_kb = char["attack_knockback"]
    kby = -3

    if hit_type == "special":
        spec_dir = attacker[PSPECDIR]

        # KAEL
        if char_id == "kael":
            if spec_dir == SPEC_SIDE:
                damage = 14
                base_kb = 7
                kby = -4

            elif spec_dir == SPEC_UP:
                damage = 11
                base_kb = 6
                kby = -8

            else:
                damage = 13
                base_kb = 7
                kby = -2

        # NYRA
        elif char_id == "nyra":
            if spec_dir == SPEC_SIDE:
                damage = 8
                base_kb = 6
                kby = -3

            elif spec_dir == SPEC_UP:
                damage = 7
                base_kb = 5
                kby = -9

            else:
                damage = 10
                base_kb = 5
                kby = 5

        # BRUGO
        else:
            if spec_dir == SPEC_SIDE:
                damage = 16
                base_kb = 8
                kby = -3

            elif spec_dir == SPEC_UP:
                damage = 15
                base_kb = 8
                kby = -9

            else:
                damage = 20
                base_kb = 10
                kby = -4

    kb = base_kb + victim[PDAMAGE] // 15 - victim_char["weight"]

    if kb < 2:
        kb = 2

    if attacker[PFACING] >= 0:
        kbx = kb
    else:
        kbx = -kb

    if hit_type == "special" and attacker[PSPECDIR] == SPEC_UP:
        kbx = kbx // 2

    if hit_type == "special" and attacker[PSPECDIR] == SPEC_DOWN:
        if char_id == "brugo":
            kbx = kbx + attacker[PFACING] * 2
        elif char_id == "nyra":
            kbx = attacker[PFACING] * 3
        else:
            kbx = attacker[PFACING] * 4

    return next_hit_id, damage, kbx, kby


def draw_wind_side(oled, sx, sy, facing, length):
    if facing >= 0:
        tip = sx + length

        draw_line(oled, tip, sy, tip - 8, sy - 5, WHITE)
        draw_line(oled, tip, sy, tip - 8, sy + 5, WHITE)

        oled.hline(sx + 4, sy - 3, 10, WHITE)
        oled.hline(sx + 1, sy, 14, WHITE)
        oled.hline(sx + 4, sy + 3, 10, WHITE)

    else:
        tip = sx - length

        draw_line(oled, tip, sy, tip + 8, sy - 5, WHITE)
        draw_line(oled, tip, sy, tip + 8, sy + 5, WHITE)

        oled.hline(sx - 14, sy - 3, 10, WHITE)
        oled.hline(sx - 15, sy, 14, WHITE)
        oled.hline(sx - 14, sy + 3, 10, WHITE)


def draw_wind_up(oled, sx, sy):
    draw_line(oled, sx, sy - 24, sx - 6, sy - 14, WHITE)
    draw_line(oled, sx, sy - 24, sx + 6, sy - 14, WHITE)
    oled.vline(sx, sy - 22, 18, WHITE)
    oled.vline(sx - 4, sy - 17, 10, WHITE)
    oled.vline(sx + 4, sy - 17, 10, WHITE)


def draw_wind_down(oled, sx, sy):
    oled.hline(sx - 22, sy + 4, 44, WHITE)
    oled.hline(sx - 16, sy + 8, 32, WHITE)
    draw_line(oled, sx - 24, sy + 4, sx - 30, sy, WHITE)
    draw_line(oled, sx + 24, sy + 4, sx + 30, sy, WHITE)


def draw_action_effect(oled, player, camera_x):
    sx = world_to_screen_x(player[PX] + PLAYER_W // 2, camera_x)
    sy = player[PY] + PLAYER_H // 2

    if sx < -50 or sx > SCREEN_W + 50:
        return

    if attack_active(player):
        draw_wind_side(oled, sx, sy, player[PFACING], 20)

    elif special_active(player):
        if player[PSPECDIR] == SPEC_UP:
            draw_wind_up(oled, sx, sy)

        elif player[PSPECDIR] == SPEC_DOWN:
            draw_wind_down(oled, sx, player[PY] + PLAYER_H)

        else:
            if get_character(player[PCHAR])["id"] == "nyra":
                draw_wind_side(oled, sx, sy, player[PFACING], 34)
            elif get_character(player[PCHAR])["id"] == "brugo":
                draw_wind_side(oled, sx, sy, player[PFACING], 26)
            else:
                draw_wind_side(oled, sx, sy, player[PFACING], 30)


def draw_player(oled, player, label, camera_x):
    screen_x = world_to_screen_x(player[PX] + PLAYER_W // 2, camera_x)
    base_y = int(player[PY] + PLAYER_H - 6)

    if screen_x < -35 or screen_x > SCREEN_W + 35:
        return

    if player[PINVINCIBLE] > 0:
        if (time.ticks_ms() // 100) % 2 == 0:
            return

    char = get_character(player[PCHAR])
    action = int(player[PACTION])
    anim_tick = time.ticks_ms() // 40

    draw_fighter(oled, char["id"], screen_x, base_y, player[PFACING], action, anim_tick, WHITE)
    draw_fighter(oled, char["id"], screen_x + 1, base_y, player[PFACING], action, anim_tick, WHITE)

    oled.text(label, screen_x - 3, player[PY] - 10, WHITE)


def draw_game(oled, role, p1, p2, net_ok, map_index):
    if role == "host":
        local_player = p1
    else:
        local_player = p2

    camera_x = get_camera_x(local_player)

    oled.fill(BLACK)

    p1_char = get_character(p1[PCHAR])
    p2_char = get_character(p2[PCHAR])

    oled.text(p1_char["short"], 2, 2, WHITE)
    oled.text(str(p1[PDAMAGE]) + "%", 30, 2, WHITE)
    oled.text("S" + str(p1[PSTOCKS]), 62, 2, WHITE)

    oled.text(p2_char["short"], 88, 2, WHITE)
    oled.text(str(p2[PDAMAGE]) + "%", 116, 2, WHITE)
    oled.text("S" + str(p2[PSTOCKS]), 148, 2, WHITE)

    if net_ok:
        oled.pixel(78, 2, WHITE)
    else:
        oled.text("!", 76, 2, WHITE)

    m = get_map(map_index)

    for p in m["platforms"]:
        sx = world_to_screen_x(p[0], camera_x)
        oled.fill_rect(sx, p[1], p[2], p[3], WHITE)

    draw_action_effect(oled, p1, camera_x)
    draw_action_effect(oled, p2, camera_x)

    draw_player(oled, p1, "1", camera_x)
    draw_player(oled, p2, "2", camera_x)

    if p1[PBLASTTIMER] > 0:
        bx = world_to_screen_x(p1[PBLASTX], camera_x)
        draw_blast(oled, bx, p1[PBLASTY], 12 - p1[PBLASTTIMER], WHITE)

    if p2[PBLASTTIMER] > 0:
        bx = world_to_screen_x(p2[PBLASTX], camera_x)
        draw_blast(oled, bx, p2[PBLASTY], 12 - p2[PBLASTTIMER], WHITE)

    oled.show()


def draw_pause(oled, local_pause, peer_pause, pause_index):
    oled.fill(BLACK)
    center_text(oled, "PAUSED", 10, CYAN)

    if peer_pause == PAUSE_PAUSED and local_pause != PAUSE_PAUSED:
        center_text(oled, "OTHER PLAYER", 30, WHITE)
        center_text(oled, "PAUSED", 44, WHITE)
        oled.text("Y=Menu", 48, 66, GRAY)

    else:
        items = ["Resume", "Quit Match"]

        for i in range(len(items)):
            y = 32 + i * 14

            if i == pause_index:
                oled.text(">", 32, y, YELLOW)
                color = YELLOW
            else:
                color = WHITE

            oled.text(items[i], 48, y, color)

        oled.text("G=Pick Y=Back", 24, 68, GRAY)

    oled.show()


def pause_controls(controls, pause_index):
    left, right, up, down = controls["joystick"]()

    if up:
        pause_index -= 1
        if pause_index < 0:
            pause_index = 1
        time.sleep(0.18)

    elif down:
        pause_index += 1
        if pause_index > 1:
            pause_index = 0
        time.sleep(0.18)

    if controls["green"]():
        wait_button_release(controls)

        if pause_index == 0:
            return pause_index, PAUSE_PLAY
        else:
            return pause_index, PAUSE_QUIT

    if controls["yellow"]():
        wait_button_release(controls)
        return pause_index, PAUSE_PLAY

    return pause_index, PAUSE_PAUSED


def win_screen(oled, controls, winner_name):
    while True:
        oled.fill(BLACK)
        center_text(oled, winner_name, 18, WHITE)
        center_text(oled, "WINS", 34, CYAN)
        center_text(oled, "G/Y BACK", 56, WHITE)
        oled.show()

        if controls["green"]() or controls["yellow"]():
            wait_button_release(controls)
            return

        time.sleep(0.05)


def main(oled, controls, settings, role, room_code):
    mp_mode = settings.get("mp_mode", "online")

    wait_screen(oled, "FORGE FIGHTERS", "CONNECTING", mp_mode.upper())

    ws = MultiplayerClient(mp_mode)

    try:
        ws.connect(room_code, role)
    except Exception as e:
        print("FF CONNECT ERROR:", e)
        oled.fill(BLACK)
        center_text(oled, "CONNECT FAIL", 14, WHITE)
        center_text(oled, str(e)[:18], 38, WHITE)
        oled.show()
        time.sleep(5)
        return

    chosen_char = character_select(oled, controls, role)

    if chosen_char == None:
        ws.close()
        return

    if role == "host":
        chosen_map = map_select(oled, controls)

        if chosen_map == None:
            ws.close()
            return
    else:
        chosen_map = -1

    peer_char, final_map = setup_sync(
        oled,
        ws,
        controls,
        role,
        chosen_char,
        chosen_map
    )

    if peer_char == None or final_map == None:
        ws.close()
        return

    m = get_map(final_map)

    if role == "host":
        p1 = make_player(m["spawn1"][0], m["spawn1"][1], 1, chosen_char)
        p2 = make_player(m["spawn2"][0], m["spawn2"][1], -1, peer_char)
    else:
        p1 = make_player(m["spawn1"][0], m["spawn1"][1], 1, peer_char)
        p2 = make_player(m["spawn2"][0], m["spawn2"][1], -1, chosen_char)

    last_frame = time.ticks_ms()
    last_sync = time.ticks_ms()
    last_gc = time.ticks_ms()
    last_good_net = time.ticks_ms()
    last_yellow = time.ticks_ms()

    net_ok = False

    next_hit_id = 1
    outgoing_hit_id = 0
    outgoing_hit_damage = 0
    outgoing_hit_kbx = 0
    outgoing_hit_kby = 0
    outgoing_hit_repeats = 0
    last_received_hit_id = 0

    local_pause = PAUSE_PLAY
    peer_pause = PAUSE_PLAY
    pause_index = 0

    wait_screen(oled, "FORGE FIGHTERS", role.upper(), m["name"])
    time.sleep(0.7)

    while True:
        left, right, up, down = controls["joystick"]()
        attack = controls["green"]()
        special = controls["red"]()

        now = time.ticks_ms()

        if controls["yellow"]() and time.ticks_diff(now, last_yellow) > 350:
            wait_button_release(controls)
            last_yellow = now

            if local_pause == PAUSE_PLAY:
                local_pause = PAUSE_PAUSED
            else:
                local_pause = PAUSE_PLAY

        if peer_pause == PAUSE_QUIT or local_pause == PAUSE_QUIT:
            ws.close()
            return

        paused = (
            local_pause == PAUSE_PAUSED or
            peer_pause == PAUSE_PAUSED
        )

        if paused:
            draw_pause(oled, local_pause, peer_pause, pause_index)

            if local_pause == PAUSE_PAUSED:
                pause_index, local_pause = pause_controls(controls, pause_index)

        else:
            if time.ticks_diff(now, last_frame) > FRAME_MS:
                if role == "host":
                    tick_timers(p1)
                    tick_timers(p2)

                    apply_player_input(p1, left, right, up, down, attack, special)
                    update_physics(p1, 1, final_map)
                    predict_remote_physics(p2, final_map)

                    hit_type = check_attack_hit(p1, p2)

                    if hit_type != "":
                        hid, dmg, kbx, kby = create_hit_event(
                            p1,
                            p2,
                            next_hit_id,
                            hit_type
                        )
                        next_hit_id += 1
                        outgoing_hit_id = hid
                        outgoing_hit_damage = dmg
                        outgoing_hit_kbx = kbx
                        outgoing_hit_kby = kby
                        outgoing_hit_repeats = 5

                else:
                    tick_timers(p1)
                    tick_timers(p2)

                    predict_remote_physics(p1, final_map)
                    apply_player_input(p2, left, right, up, down, attack, special)
                    update_physics(p2, 2, final_map)

                    hit_type = check_attack_hit(p2, p1)

                    if hit_type != "":
                        hid, dmg, kbx, kby = create_hit_event(
                            p2,
                            p1,
                            next_hit_id,
                            hit_type
                        )
                        next_hit_id += 1
                        outgoing_hit_id = hid
                        outgoing_hit_damage = dmg
                        outgoing_hit_kbx = kbx
                        outgoing_hit_kby = kby
                        outgoing_hit_repeats = 5

                last_frame = now

        if time.ticks_diff(now, last_sync) > SYNC_MS:
            if role == "host":
                packet = make_packet(
                    p1,
                    outgoing_hit_id,
                    outgoing_hit_damage,
                    outgoing_hit_kbx,
                    outgoing_hit_kby,
                    local_pause,
                    final_map
                )
            else:
                packet = make_packet(
                    p2,
                    outgoing_hit_id,
                    outgoing_hit_damage,
                    outgoing_hit_kbx,
                    outgoing_hit_kby,
                    local_pause,
                    final_map
                )

            reply = ws.sync(packet)
            peer = parse_peer_message(reply)

            if peer != "":
                if role == "host":
                    real_p2, hit_id, hit_damage, hit_kbx, hit_kby, peer_pause, peer_map = parse_packet(peer, p2)
                    smooth_correct_player(p2, real_p2)

                    if hit_id != 0 and hit_id != last_received_hit_id:
                        apply_hit(p1, hit_damage, hit_kbx, hit_kby)
                        last_received_hit_id = hit_id

                else:
                    real_p1, hit_id, hit_damage, hit_kbx, hit_kby, peer_pause, peer_map = parse_packet(peer, p1)
                    smooth_correct_player(p1, real_p1)

                    if hit_id != 0 and hit_id != last_received_hit_id:
                        apply_hit(p2, hit_damage, hit_kbx, hit_kby)
                        last_received_hit_id = hit_id

                net_ok = True
                last_good_net = now
            else:
                net_ok = False

            if outgoing_hit_repeats > 0:
                outgoing_hit_repeats -= 1
            else:
                outgoing_hit_id = 0
                outgoing_hit_damage = 0
                outgoing_hit_kbx = 0
                outgoing_hit_kby = 0

            last_sync = now

        if time.ticks_diff(now, last_good_net) > 1000:
            net_ok = False

        if not paused:
            if p1[PSTOCKS] <= 0:
                win_screen(oled, controls, get_character(p2[PCHAR])["name"])
                ws.close()
                return

            if p2[PSTOCKS] <= 0:
                win_screen(oled, controls, get_character(p1[PCHAR])["name"])
                ws.close()
                return

            draw_game(oled, role, p1, p2, net_ok, final_map)

        if time.ticks_diff(now, last_gc) > 5000:
            gc.collect()
            last_gc = now

        time.sleep(0.02)
