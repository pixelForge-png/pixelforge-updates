import time
import gc
from helpers.mp_client import MultiplayerClient
from helpers.forge_sprites import draw_fighter, draw_blast

SCREEN_W = 160
SCREEN_H = 80

BLACK = 0
WHITE = 65535
GRAY = 33808
CYAN = 2047
YELLOW = 65504

PLAYER_W = 7
PLAYER_H = 12

GRAVITY = 1
MAX_FALL = 7

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

ACTION_IDLE = 0
ACTION_RUN = 1
ACTION_JUMP = 2
ACTION_ATTACK = 3
ACTION_HURT = 4
ACTION_SPECIAL = 5
ACTION_CROUCH = 6
ACTION_SPAWN = 7

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
        "jump": -8,
        "weight": 1,
        "attack_damage": 10,
        "attack_knockback": 5,
        "special_name": "Blade Dash",
        "special_damage": 14,
        "special_knockback": 7,
        "special_cooldown": 45
    },
    {
        "id": "nyra",
        "name": "Nyra",
        "title": "Swiftfang",
        "short": "NYR",
        "speed": 4,
        "jump": -9,
        "weight": 0,
        "attack_damage": 8,
        "attack_knockback": 4,
        "special_name": "Shadow Step",
        "special_damage": 8,
        "special_knockback": 5,
        "special_cooldown": 32
    },
    {
        "id": "brugo",
        "name": "Brugo",
        "title": "Stonehelm",
        "short": "BRU",
        "speed": 2,
        "jump": -7,
        "weight": 2,
        "attack_damage": 14,
        "attack_knockback": 7,
        "special_name": "Ground Break",
        "special_damage": 18,
        "special_knockback": 9,
        "special_cooldown": 60
    }
]

MAPS = [
    {
        "id": "stone_bridge",
        "name": "Stone Bridge",
        "platforms": [
            [20, 62, 120, 4]
        ],
        "spawn1": [45, 35],
        "spawn2": [108, 35],
        "death_y": 100
    },
    {
        "id": "sky_ruins",
        "name": "Sky Ruins",
        "platforms": [
            [35, 64, 90, 4],
            [12, 42, 38, 4],
            [110, 42, 38, 4]
        ],
        "spawn1": [45, 35],
        "spawn2": [108, 35],
        "death_y": 100
    },
    {
        "id": "lava_pit",
        "name": "Lava Pit",
        "platforms": [
            [42, 62, 76, 4],
            [10, 47, 36, 4],
            [114, 47, 36, 4]
        ],
        "spawn1": [52, 35],
        "spawn2": [101, 35],
        "death_y": 86
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


def draw_rect(oled, x, y, w, h, color):
    oled.hline(x, y, w, color)
    oled.hline(x, y + h - 1, w, color)
    oled.vline(x, y, h, color)
    oled.vline(x + w - 1, y, h, color)


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
    draw_fighter(oled, char["id"], x, y, 1, ACTION_IDLE, time.ticks_ms() // 40, WHITE)


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

        # Preview is on right side so it does not overlap text.
        draw_preview_fighter(oled, 132, 60, index)

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
        oled.fill_rect(p[0], p[1], p[2], p[3], WHITE)


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
    peer_char = 0
    final_map = chosen_map

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
                    final_map = peer_map
                    return peer_char, final_map

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
        x, y, 0
    ]


def make_packet(player, hit_id, hit_damage, hit_kbx, hit_kby, pause_state, map_index):
    values = []

    for i in range(24):
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

        if len(parts) < 30:
            return old_player, 0, 0, 0, 0, PAUSE_PLAY, 0

        player = []

        for i in range(24):
            player.append(parse_int(parts[i], old_player[i]))

        hit_id = parse_int(parts[24], 0)
        hit_damage = parse_int(parts[25], 0)
        hit_kbx = parse_int(parts[26], 0)
        hit_kby = parse_int(parts[27], 0)
        pause_state = parse_int(parts[28], PAUSE_PLAY)
        map_index = parse_int(parts[29], 0)

        return player, hit_id, hit_damage, hit_kbx, hit_kby, pause_state, map_index

    except:
        return old_player, 0, 0, 0, 0, PAUSE_PLAY, 0


def smooth_correct_player(local_player, real_player):
    diff_x = real_player[PX] - local_player[PX]
    diff_y = real_player[PY] - local_player[PY]

    if diff_x > 25 or diff_x < -25 or diff_y > 25 or diff_y < -25:
        local_player[PX] = real_player[PX]
        local_player[PY] = real_player[PY]
    else:
        local_player[PX] = local_player[PX] + diff_x // 3
        local_player[PY] = local_player[PY] + diff_y // 3

    for i in range(2, 24):
        local_player[i] = real_player[i]


def start_death_blast(player):
    player[PBLASTX] = player[PX]
    player[PBLASTY] = player[PY]
    player[PBLASTTIMER] = 12


def respawn_player(player, player_num, map_index):
    if player_num == 1:
        player[PFACING] = 1
    else:
        player[PFACING] = -1

    # Spawn above center and wait briefly.
    player[PX] = SCREEN_W // 2
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
    player[PTIMER] = 16
    player[PSPECTIMER] = 16
    player[PSPECCD] = char["special_cooldown"]
    player[PSPECDONE] = 0

    # Directional red specials:
    # up = recovery, down = slam/crouch special, side/neutral = side special.
    if up:
        player[PVY] = -9
        player[PVX] = player[PFACING] * 2

    elif down:
        player[PVY] = 2
        player[PVX] = 0

    else:
        if char["id"] == "kael":
            player[PVX] = player[PFACING] * 6
        elif char["id"] == "nyra":
            player[PVX] = player[PFACING] * 8
        else:
            player[PVX] = player[PFACING] * 3


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

    if player[PACTION] == ACTION_HURT and player[PHITSTUN] <= 0:
        player[PACTION] = ACTION_IDLE


def apply_special_motion(player):
    char = get_character(player[PCHAR])

    if player[PACTION] != ACTION_SPECIAL:
        return

    # Kael: controlled sword dash.
    if char["id"] == "kael":
        if player[PTIMER] > 5:
            if player[PVX] == 0:
                player[PVX] = player[PFACING] * 5
        else:
            player[PVX] = 0

    # Nyra: faster burst.
    elif char["id"] == "nyra":
        if player[PTIMER] > 6:
            if player[PVX] == 0:
                player[PVX] = player[PFACING] * 7
        else:
            player[PVX] = 0

    # Brugo: heavy, stops after first push.
    else:
        if player[PTIMER] < 8:
            player[PVX] = 0


def apply_player_input(player, left, right, up, down, attack, special):
    char = get_character(player[PCHAR])
    speed = char["speed"]
    jump_power = char["jump"]

    # During spawn hover, movement starts the fall.
    if player[PSPAWNWAIT] > 0:
        if left or right or up or down:
            player[PSPAWNWAIT] = 0

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

    if up and player[PONGROUND] == 1:
        player[PVY] = jump_power
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
            return

    player[PONGROUND] = 0


def update_physics(player, player_num, map_index):
    old_y = player[PY]

    # Spawn hover.
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

    player[PX] = clamp(player[PX], -25, SCREEN_W + 25)

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

    player[PX] = clamp(player[PX], -25, SCREEN_W + 25)

    collide_platforms(player, old_y, map_index)


def player_rect(player):
    # Crouching makes the hurtbox lower/smaller.
    # This lets crouch avoid some high attacks.
    if player[PCROUCH] == 1:
        return [player[PX], player[PY] + 4, PLAYER_W, PLAYER_H - 4]

    return [player[PX], player[PY] - 3, PLAYER_W, PLAYER_H + 3]


def attack_active(player):
    return player[PACTION] == ACTION_ATTACK and player[PTIMER] <= 9 and player[PTIMER] >= 4


def special_active(player):
    if player[PACTION] != ACTION_SPECIAL:
        return False

    char = get_character(player[PCHAR])

    if char["id"] == "brugo":
        return player[PTIMER] <= 11 and player[PTIMER] >= 4

    return player[PTIMER] <= 13 and player[PTIMER] >= 5


def attack_rect(player):
    x = player[PX]
    y = player[PY]

    # High-ish sword hitbox. Crouch can avoid some of this.
    if player[PFACING] >= 0:
        return [x + PLAYER_W, y - 2, 14, 7]
    else:
        return [x - 14, y - 2, 14, 7]


def special_rect(player):
    x = player[PX]
    y = player[PY]
    char = get_character(player[PCHAR])

    if char["id"] == "kael":
        if player[PFACING] >= 0:
            return [x + PLAYER_W, y, 22, 12]
        else:
            return [x - 22, y, 22, 12]

    if char["id"] == "nyra":
        if player[PFACING] >= 0:
            return [x + PLAYER_W, y - 1, 26, 14]
        else:
            return [x - 26, y - 1, 26, 14]

    # Brugo shockwave is low, so crouch will not avoid it.
    if player[PFACING] >= 0:
        return [x + PLAYER_W, y + 7, 28, 8]
    else:
        return [x - 28, y + 7, 28, 8]


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

    if hit_type == "special":
        damage = char["special_damage"]
        base_kb = char["special_knockback"]
    else:
        damage = char["attack_damage"]
        base_kb = char["attack_knockback"]

    kb = base_kb + victim[PDAMAGE] // 15 - victim_char["weight"]

    if kb < 2:
        kb = 2

    if attacker[PFACING] >= 0:
        kbx = kb
    else:
        kbx = -kb

    if hit_type == "special" and char["id"] == "brugo":
        kby = -5
    elif hit_type == "special":
        kby = -4
    else:
        kby = -3

    return next_hit_id, damage, kbx, kby


def draw_action_box(oled, player):
    if attack_active(player):
        r = attack_rect(player)
        draw_rect(oled, r[0], r[1], r[2], r[3], WHITE)

    if special_active(player):
        r = special_rect(player)
        draw_rect(oled, r[0], r[1], r[2], r[3], WHITE)


def draw_player(oled, player, label):
    x = int(player[PX])
    y = int(player[PY])
    facing = int(player[PFACING])
    char = get_character(player[PCHAR])
    action = int(player[PACTION])

    if x < -35 or x > SCREEN_W + 35:
        return

    # Flash during respawn invincibility.
    if player[PINVINCIBLE] > 0:
        if (time.ticks_ms() // 100) % 2 == 0:
            return

    anim_tick = time.ticks_ms() // 40

    draw_fighter(
        oled,
        char["id"],
        x,
        y,
        facing,
        action,
        anim_tick,
        WHITE
    )

    oled.text(label, x, y - 18, WHITE)


def draw_game(oled, role, p1, p2, net_ok, map_index):
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
        oled.fill_rect(p[0], p[1], p[2], p[3], WHITE)

    draw_action_box(oled, p1)
    draw_action_box(oled, p2)

    draw_player(oled, p1, "1")
    draw_player(oled, p2, "2")

    if p1[PBLASTTIMER] > 0:
        draw_blast(oled, p1[PBLASTX], p1[PBLASTY], 12 - p1[PBLASTTIMER], WHITE)

    if p2[PBLASTTIMER] > 0:
        draw_blast(oled, p2[PBLASTX], p2[PBLASTY], 12 - p2[PBLASTTIMER], WHITE)

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
