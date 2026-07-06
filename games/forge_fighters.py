import time
import gc
from helpers.mp_client import MultiplayerClient

SCREEN_W = 160
SCREEN_H = 80

BLACK = 0
WHITE = 65535
GRAY = 33808

P1_COLOR = WHITE
P2_COLOR = WHITE

PLAYER_W = 7
PLAYER_H = 12

MOVE_SPEED = 3
GRAVITY = 1
JUMP_POWER = -8
MAX_FALL = 7

SYNC_MS = 60
FRAME_MS = 35

# Stone Bridge map
PLATFORM_X = 20
PLATFORM_Y = 62
PLATFORM_W = 120
PLATFORM_H = 4

RESPAWN_1_X = 45
RESPAWN_2_X = 108
RESPAWN_Y = 35


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
    center_text(oled, title, 10)
    center_text(oled, line1, 32)
    center_text(oled, line2, 52)
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


def make_player(x, y, facing):
    # x, y, vx, vy, facing, on_ground, falls
    return [x, y, 0, 0, facing, 0, 0]


def make_one_player_state(player):
    # x,y,vx,vy,facing,on_ground,falls
    return (
        str(int(player[0])) + "," +
        str(int(player[1])) + "," +
        str(int(player[2])) + "," +
        str(int(player[3])) + "," +
        str(int(player[4])) + "," +
        str(int(player[5])) + "," +
        str(int(player[6]))
    )


def parse_one_player_state(data, old_player):
    try:
        parts = data.split(",")

        if len(parts) < 7:
            return old_player

        return [
            parse_int(parts[0], old_player[0]),
            parse_int(parts[1], old_player[1]),
            parse_int(parts[2], old_player[2]),
            parse_int(parts[3], old_player[3]),
            parse_int(parts[4], old_player[4]),
            parse_int(parts[5], old_player[5]),
            parse_int(parts[6], old_player[6])
        ]

    except:
        return old_player


def smooth_correct_player(local_player, real_player):
    # Use this later if we need smoother remote players.
    diff_x = real_player[0] - local_player[0]
    diff_y = real_player[1] - local_player[1]

    if diff_x > 18 or diff_x < -18 or diff_y > 18 or diff_y < -18:
        local_player[0] = real_player[0]
        local_player[1] = real_player[1]
    else:
        local_player[0] = local_player[0] + diff_x // 3
        local_player[1] = local_player[1] + diff_y // 3

    local_player[2] = real_player[2]
    local_player[3] = real_player[3]
    local_player[4] = real_player[4]
    local_player[5] = real_player[5]
    local_player[6] = real_player[6]


def respawn_player(player, player_num):
    if player_num == 1:
        player[0] = RESPAWN_1_X
        player[4] = 1
    else:
        player[0] = RESPAWN_2_X
        player[4] = -1

    player[1] = RESPAWN_Y
    player[2] = 0
    player[3] = 0
    player[5] = 0


def apply_player_input(player, left, right, up):
    if left:
        player[2] = -MOVE_SPEED
        player[4] = -1

    elif right:
        player[2] = MOVE_SPEED
        player[4] = 1

    else:
        player[2] = 0

    if up and player[5] == 1:
        player[3] = JUMP_POWER
        player[5] = 0


def update_physics(player, player_num):
    old_y = player[1]

    # Gravity
    player[3] += GRAVITY

    if player[3] > MAX_FALL:
        player[3] = MAX_FALL

    # Move
    player[0] += player[2]
    player[1] += player[3]

    # Let players go slightly off screen before falling.
    player[0] = clamp(player[0], -25, SCREEN_W + 25)

    # Platform collision
    player_bottom_old = old_y + PLAYER_H
    player_bottom_new = player[1] + PLAYER_H

    player_left = player[0]
    player_right = player[0] + PLAYER_W

    platform_left = PLATFORM_X
    platform_right = PLATFORM_X + PLATFORM_W

    touching_x = (
        player_right >= platform_left and
        player_left <= platform_right
    )

    falling = player[3] >= 0

    crossed_platform = (
        player_bottom_old <= PLATFORM_Y and
        player_bottom_new >= PLATFORM_Y
    )

    if touching_x and falling and crossed_platform:
        player[1] = PLATFORM_Y - PLAYER_H
        player[3] = 0
        player[5] = 1
    else:
        player[5] = 0

    # Fall off map
    if player[1] > SCREEN_H + 20:
        player[6] += 1
        respawn_player(player, player_num)


def draw_player(oled, player, color, label):
    x = int(player[0])
    y = int(player[1])
    facing = int(player[4])

    # Do not draw if super far offscreen.
    if x < -30 or x > SCREEN_W + 30:
        return

    # Body
    oled.fill_rect(x, y, PLAYER_W, PLAYER_H, color)

    # Head
    oled.fill_rect(x + 2, y - 3, 3, 3, color)

    # Tiny sword / facing marker
    if facing >= 0:
        oled.hline(x + PLAYER_W, y + 5, 5, color)
    else:
        oled.hline(x - 5, y + 5, 5, color)

    # Label
    oled.text(label, x, y - 11, color)


def draw_game(oled, role, p1, p2, net_ok):
    oled.fill(BLACK)

    # Role marker
    if role == "host":
        oled.text("H", 2, 2, WHITE)
    else:
        oled.text("J", 2, 2, WHITE)

    # Fall counters
    oled.text("P1:" + str(p1[6]), 24, 2, WHITE)
    oled.text("P2:" + str(p2[6]), 112, 2, WHITE)

    # Network marker
    if net_ok:
        oled.pixel(78, 2, WHITE)
    else:
        oled.text("!", 76, 2, WHITE)

    # Platform
    oled.fill_rect(PLATFORM_X, PLATFORM_Y, PLATFORM_W, PLATFORM_H, WHITE)

    # Platform ends
    oled.vline(PLATFORM_X, PLATFORM_Y, 6, WHITE)
    oled.vline(PLATFORM_X + PLATFORM_W, PLATFORM_Y, 6, WHITE)

    # Players
    draw_player(oled, p1, P1_COLOR, "1")
    draw_player(oled, p2, P2_COLOR, "2")

    oled.show()


def main(oled, controls, settings, role, room_code):
    mp_mode = settings.get("mp_mode", "online")

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

    # p1 = host player
    # p2 = joiner player
    p1 = make_player(RESPAWN_1_X, RESPAWN_Y, 1)
    p2 = make_player(RESPAWN_2_X, RESPAWN_Y, -1)

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

        # -------------------------
        # HOST: controls Player 1 locally
        # -------------------------
        if role == "host":
            if time.ticks_diff(now, last_frame) > FRAME_MS:
                apply_player_input(p1, left, right, up)
                update_physics(p1, 1)
                last_frame = now

            if time.ticks_diff(now, last_sync) > SYNC_MS:
                packet = make_one_player_state(p1)

                reply = ws.sync(packet)
                peer = parse_peer_message(reply)

                if peer != "":
                    p2 = parse_one_player_state(peer, p2)
                    net_ok = True
                    last_good_net = now
                else:
                    net_ok = False

                last_sync = now

        # -------------------------
        # JOINER: controls Player 2 locally
        # -------------------------
        else:
            if time.ticks_diff(now, last_frame) > FRAME_MS:
                apply_player_input(p2, left, right, up)
                update_physics(p2, 2)
                last_frame = now

            if time.ticks_diff(now, last_sync) > SYNC_MS:
                packet = make_one_player_state(p2)

                reply = ws.sync(packet)
                peer = parse_peer_message(reply)

                if peer != "":
                    p1 = parse_one_player_state(peer, p1)
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
