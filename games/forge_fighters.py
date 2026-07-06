import time
import gc
from helpers.mp_client import MultiplayerClient

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

# Stone Bridge map
PLATFORM_X = 20
PLATFORM_Y = 62
PLATFORM_W = 120
PLATFORM_H = 4

RESPAWN_1_X = 45
RESPAWN_2_X = 108
RESPAWN_Y = 35

# Player state indexes
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

ACTION_IDLE = 0
ACTION_RUN = 1
ACTION_JUMP = 2

CHARACTERS = [
    {
        "id": "kael",
        "name": "Kael",
        "title": "Ironblade",
        "short": "KAEL",
        "speed": 3,
        "jump": -8,
        "weight": 1,
        "color": WHITE
    },
    {
        "id": "nyra",
        "name": "Nyra",
        "title": "Swiftfang",
        "short": "NYRA",
        "speed": 4,
        "jump": -9,
        "weight": 0,
        "color": WHITE
    },
    {
        "id": "brugo",
        "name": "Brugo",
        "title": "Stonehelm",
        "short": "BRUGO",
        "speed": 2,
        "jump": -7,
        "weight": 2,
        "color": WHITE
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


def character_select(oled, controls, role):
    index = 0
    last_move = time.ticks_ms()

    while True:
        char = get_character(index)

        oled.fill(BLACK)
        center_text("CHOOSE FIGHTER", 3, CYAN)

        if role == "host":
            center_text("PLAYER 1", 15, WHITE)
        else:
            center_text("PLAYER 2", 15, WHITE)

        oled.text("<", 3, 37, YELLOW)
        oled.text(">", 150, 37, YELLOW)

        center_text(char["name"], 30, WHITE)
        center_text(char["title"], 43, CYAN)

        stat_line = "SPD" + str(char["speed"]) + " JMP" + str(abs(char["jump"]))
        center_text(stat_line, 56, WHITE)

        oled.text("G=Pick", 2, 70, WHITE)
        oled.text("Y=Back", 104, 70, GRAY)

        # Tiny preview fighter
        draw_preview_fighter(oled, 75, 24, index)

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


def wait_button_release(controls):
    while (
        controls["green"]() or
        controls["yellow"]() or
        controls["blue"]() or
        controls["red"]()
    ):
        time.sleep(0.02)


def draw_preview_fighter(oled, x, y, char_index):
    # Simple character preview. More detailed sprites come later.
    if char_index == 0:
        # Kael: balanced sword shape
        oled.fill_rect(x, y, 8, 13, WHITE)
        oled.fill_rect(x + 2, y - 4, 4, 4, WHITE)
        oled.hline(x + 8, y + 5, 8, WHITE)

    elif char_index == 1:
        # Nyra: slimmer/faster
        oled.fill_rect(x + 1, y, 6, 13, WHITE)
        oled.fill_rect(x + 2, y - 4, 4, 4, WHITE)
        oled.hline(x + 7, y + 5, 10, WHITE)
        oled.pixel(x - 1, y + 2, WHITE)
        oled.pixel(x - 2, y + 3, WHITE)

    else:
        # Brugo: wider/heavier
        oled.fill_rect(x - 1, y, 10, 13, WHITE)
        oled.fill_rect(x + 1, y - 4, 6, 4, WHITE)
        oled.hline(x + 9, y + 6, 6, WHITE)
        oled.vline(x - 2, y + 3, 7, WHITE)


def make_player(x, y, facing, char_index):
    # x, y, vx, vy, facing, on_ground, falls, char, stocks, damage, action, timer
    return [
        x,
        y,
        0,
        0,
        facing,
        0,
        0,
        char_index,
        3,
        0,
        ACTION_IDLE,
        0
    ]


def make_one_player_state(player):
    return (
        str(int(player[PX])) + "," +
        str(int(player[PY])) + "," +
        str(int(player[PVX])) + "," +
        str(int(player[PVY])) + "," +
        str(int(player[PFACING])) + "," +
        str(int(player[PONGROUND])) + "," +
        str(int(player[PFALLS])) + "," +
        str(int(player[PCHAR])) + "," +
        str(int(player[PSTOCKS])) + "," +
        str(int(player[PDAMAGE])) + "," +
        str(int(player[PACTION])) + "," +
        str(int(player[PTIMER]))
    )


def parse_one_player_state(data, old_player):
    try:
        parts = data.split(",")

        if len(parts) < 12:
            return old_player

        return [
            parse_int(parts[0], old_player[PX]),
            parse_int(parts[1], old_player[PY]),
            parse_int(parts[2], old_player[PVX]),
            parse_int(parts[3], old_player[PVY]),
            parse_int(parts[4], old_player[PFACING]),
            parse_int(parts[5], old_player[PONGROUND]),
            parse_int(parts[6], old_player[PFALLS]),
            parse_int(parts[7], old_player[PCHAR]),
            parse_int(parts[8], old_player[PSTOCKS]),
            parse_int(parts[9], old_player[PDAMAGE]),
            parse_int(parts[10], old_player[PACTION]),
            parse_int(parts[11], old_player[PTIMER])
        ]

    except:
        return old_player


def smooth_correct_player(local_player, real_player):
    diff_x = real_player[PX] - local_player[PX]
    diff_y = real_player[PY] - local_player[PY]

    # Big difference means respawn or major correction.
    if diff_x > 25 or diff_x < -25 or diff_y > 25 or diff_y < -25:
        local_player[PX] = real_player[PX]
        local_player[PY] = real_player[PY]
    else:
        local_player[PX] = local_player[PX] + diff_x // 3
        local_player[PY] = local_player[PY] + diff_y // 3

    local_player[PVX] = real_player[PVX]
    local_player[PVY] = real_player[PVY]
    local_player[PFACING] = real_player[PFACING]
    local_player[PONGROUND] = real_player[PONGROUND]
    local_player[PFALLS] = real_player[PFALLS]
    local_player[PCHAR] = real_player[PCHAR]
    local_player[PSTOCKS] = real_player[PSTOCKS]
    local_player[PDAMAGE] = real_player[PDAMAGE]
    local_player[PACTION] = real_player[PACTION]
    local_player[PTIMER] = real_player[PTIMER]


def respawn_player(player, player_num):
    if player_num == 1:
        player[PX] = RESPAWN_1_X
        player[PFACING] = 1
    else:
        player[PX] = RESPAWN_2_X
        player[PFACING] = -1

    player[PY] = RESPAWN_Y
    player[PVX] = 0
    player[PVY] = 0
    player[PONGROUND] = 0
    player[PDAMAGE] = 0
    player[PACTION] = ACTION_IDLE
    player[PTIMER] = 0


def apply_player_input(player, left, right, up):
    char = get_character(player[PCHAR])
    speed = char["speed"]
    jump_power = char["jump"]

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


def update_physics(player, player_num):
    old_y = player[PY]

    char = get_character(player[PCHAR])

    # Heavier characters fall a little more firmly.
    gravity = GRAVITY

    if char["weight"] >= 2:
        gravity = 1

    player[PVY] += gravity

    if player[PVY] > MAX_FALL:
        player[PVY] = MAX_FALL

    player[PX] += player[PVX]
    player[PY] += player[PVY]

    player[PX] = clamp(player[PX], -25, SCREEN_W + 25)

    # Platform collision
    player_bottom_old = old_y + PLAYER_H
    player_bottom_new = player[PY] + PLAYER_H

    player_left = player[PX]
    player_right = player[PX] + PLAYER_W

    platform_left = PLATFORM_X
    platform_right = PLATFORM_X + PLATFORM_W

    touching_x = (
        player_right >= platform_left and
        player_left <= platform_right
    )

    falling = player[PVY] >= 0

    crossed_platform = (
        player_bottom_old <= PLATFORM_Y and
        player_bottom_new >= PLATFORM_Y
    )

    if touching_x and falling and crossed_platform:
        player[PY] = PLATFORM_Y - PLAYER_H
        player[PVY] = 0
        player[PONGROUND] = 1
    else:
        player[PONGROUND] = 0

    # Fall off map
    if player[PY] > SCREEN_H + 20:
        player[PFALLS] += 1
        respawn_player(player, player_num)


def predict_remote_physics(player):
    old_y = player[PY]

    player[PVY] += GRAVITY

    if player[PVY] > MAX_FALL:
        player[PVY] = MAX_FALL

    player[PX] += player[PVX]
    player[PY] += player[PVY]

    player[PX] = clamp(player[PX], -25, SCREEN_W + 25)

    player_bottom_old = old_y + PLAYER_H
    player_bottom_new = player[PY] + PLAYER_H

    player_left = player[PX]
    player_right = player[PX] + PLAYER_W

    platform_left = PLATFORM_X
    platform_right = PLATFORM_X + PLATFORM_W

    touching_x = (
        player_right >= platform_left and
        player_left <= platform_right
    )

    falling = player[PVY] >= 0

    crossed_platform = (
        player_bottom_old <= PLATFORM_Y and
        player_bottom_new >= PLATFORM_Y
    )

    if touching_x and falling and crossed_platform:
        player[PY] = PLATFORM_Y - PLAYER_H
        player[PVY] = 0
        player[PONGROUND] = 1
    else:
        player[PONGROUND] = 0


def draw_player(oled, player, label):
    x = int(player[PX])
    y = int(player[PY])
    facing = int(player[PFACING])
    char_index = int(player[PCHAR])
    action = int(player[PACTION])

    if x < -30 or x > SCREEN_W + 30:
        return

    char = get_character(char_index)

    # Different simple shapes for each character.
    if char["id"] == "kael":
        draw_kael(oled, x, y, facing, action)

    elif char["id"] == "nyra":
        draw_nyra(oled, x, y, facing, action)

    else:
        draw_brugo(oled, x, y, facing, action)

    oled.text(label, x, y - 12, WHITE)


def draw_kael(oled, x, y, facing, action):
    # Balanced swordsman
    if action == ACTION_RUN:
        leg_offset = (time.ticks_ms() // 120) % 2
    else:
        leg_offset = 0

    oled.fill_rect(x, y, 7, 12, WHITE)
    oled.fill_rect(x + 2, y - 3, 3, 3, WHITE)

    # legs
    oled.vline(x + 1, y + 12, 3 + leg_offset, WHITE)
    oled.vline(x + 5, y + 12, 4 - leg_offset, WHITE)

    # sword
    if facing >= 0:
        oled.hline(x + 7, y + 5, 7, WHITE)
    else:
        oled.hline(x - 7, y + 5, 7, WHITE)


def draw_nyra(oled, x, y, facing, action):
    # Slim fast duelist
    if action == ACTION_RUN:
        leg_offset = (time.ticks_ms() // 90) % 2
    else:
        leg_offset = 0

    oled.fill_rect(x + 1, y, 5, 12, WHITE)
    oled.fill_rect(x + 2, y - 3, 3, 3, WHITE)

    # fast trailing pixels
    if action == ACTION_RUN:
        if facing >= 0:
            oled.pixel(x - 2, y + 4, WHITE)
            oled.pixel(x - 3, y + 7, WHITE)
        else:
            oled.pixel(x + 8, y + 4, WHITE)
            oled.pixel(x + 9, y + 7, WHITE)

    # legs
    oled.vline(x + 2, y + 12, 3 + leg_offset, WHITE)
    oled.vline(x + 5, y + 12, 4 - leg_offset, WHITE)

    # longer thin sword
    if facing >= 0:
        oled.hline(x + 6, y + 5, 9, WHITE)
    else:
        oled.hline(x - 9, y + 5, 9, WHITE)


def draw_brugo(oled, x, y, facing, action):
    # Heavy warrior
    if action == ACTION_RUN:
        leg_offset = (time.ticks_ms() // 170) % 2
    else:
        leg_offset = 0

    oled.fill_rect(x - 1, y, 9, 12, WHITE)
    oled.fill_rect(x + 1, y - 4, 5, 4, WHITE)

    # heavy shoulders
    oled.hline(x - 2, y + 2, 11, WHITE)

    # legs
    oled.vline(x + 1, y + 12, 4 + leg_offset, WHITE)
    oled.vline(x + 6, y + 12, 5 - leg_offset, WHITE)

    # short heavy weapon
    if facing >= 0:
        oled.hline(x + 8, y + 6, 6, WHITE)
        oled.vline(x + 13, y + 4, 5, WHITE)
    else:
        oled.hline(x - 6, y + 6, 6, WHITE)
        oled.vline(x - 6, y + 4, 5, WHITE)


def draw_game(oled, role, p1, p2, net_ok):
    oled.fill(BLACK)

    if role == "host":
        oled.text("H", 2, 2, WHITE)
    else:
        oled.text("J", 2, 2, WHITE)

    p1_char = get_character(p1[PCHAR])
    p2_char = get_character(p2[PCHAR])

    oled.text(p1_char["short"][:4], 18, 2, WHITE)
    oled.text(str(p1[PFALLS]), 56, 2, WHITE)

    oled.text(p2_char["short"][:4], 94, 2, WHITE)
    oled.text(str(p2[PFALLS]), 136, 2, WHITE)

    if net_ok:
        oled.pixel(78, 2, WHITE)
    else:
        oled.text("!", 76, 2, WHITE)

    # Platform
    oled.fill_rect(PLATFORM_X, PLATFORM_Y, PLATFORM_W, PLATFORM_H, WHITE)
    oled.vline(PLATFORM_X, PLATFORM_Y, 6, WHITE)
    oled.vline(PLATFORM_X + PLATFORM_W, PLATFORM_Y, 6, WHITE)

    draw_player(oled, p1, "1")
    draw_player(oled, p2, "2")

    oled.show()


def main(oled, controls, settings, role, room_code):
    mp_mode = settings.get("mp_mode", "online")

    chosen_char = character_select(oled, controls, role)

    if chosen_char == None:
        return

    wait_screen(oled, "FORGE FIGHTERS", "CONNECTING", mp_mode.upper())

    ws = MultiplayerClient(mp_mode)

    try:
        ws.connect(room_code, role)
    except Exception as e:
        print("FF CONNECT ERROR:", e)
        oled.fill(BLACK)
        center_text(oled, "CONNECT FAIL", 14)
        center_text(oled, str(e)[:18], 38)
        oled.show()
        time.sleep(5)
        return

    if role == "host":
        p1 = make_player(RESPAWN_1_X, RESPAWN_Y, 1, chosen_char)
        p2 = make_player(RESPAWN_2_X, RESPAWN_Y, -1, 0)
    else:
        p1 = make_player(RESPAWN_1_X, RESPAWN_Y, 1, 0)
        p2 = make_player(RESPAWN_2_X, RESPAWN_Y, -1, chosen_char)

    last_frame = time.ticks_ms()
    last_sync = time.ticks_ms()
    last_gc = time.ticks_ms()
    last_good_net = time.ticks_ms()

    net_ok = False

    wait_screen(oled, "FORGE FIGHTERS", role.upper(), "STONE BRIDGE")
    time.sleep(0.7)

    while True:
        left, right, up, down = controls["joystick"]()

        if controls["yellow"]():
            time.sleep(0.3)
            ws.close()
            return

        now = time.ticks_ms()

        # HOST: controls Player 1 locally
        if role == "host":
            if time.ticks_diff(now, last_frame) > FRAME_MS:
                apply_player_input(p1, left, right, up)
                update_physics(p1, 1)

                # Predict remote player
                predict_remote_physics(p2)

                last_frame = now

            if time.ticks_diff(now, last_sync) > SYNC_MS:
                packet = make_one_player_state(p1)

                reply = ws.sync(packet)
                peer = parse_peer_message(reply)

                if peer != "":
                    real_p2 = parse_one_player_state(peer, p2)
                    smooth_correct_player(p2, real_p2)
                    net_ok = True
                    last_good_net = now
                else:
                    net_ok = False

                last_sync = now

        # JOINER: controls Player 2 locally
        else:
            if time.ticks_diff(now, last_frame) > FRAME_MS:
                predict_remote_physics(p1)

                apply_player_input(p2, left, right, up)
                update_physics(p2, 2)

                last_frame = now

            if time.ticks_diff(now, last_sync) > SYNC_MS:
                packet = make_one_player_state(p2)

                reply = ws.sync(packet)
                peer = parse_peer_message(reply)

                if peer != "":
                    real_p1 = parse_one_player_state(peer, p1)
                    smooth_correct_player(p1, real_p1)
                    net_ok = True
                    last_good_net = now
                else:
                    net_ok = False

                last_sync = now

        if time.ticks_diff(now, last_good_net) > 1000:
            net_ok = False

        draw_game(oled, role, p1, p2, net_ok)

        if time.ticks_diff(now, last_gc) > 5000:
            gc.collect()
            last_gc = now

        time.sleep(0.02)
