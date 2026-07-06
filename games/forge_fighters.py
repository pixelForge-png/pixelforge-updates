import time
import gc
from helpers.mp_client import MultiplayerClient

SCREEN_W = 160
SCREEN_H = 80

BLACK = 0
WHITE = 65535
GRAY = 33808

# If your colors are weird, these are just labels.
P1_COLOR = WHITE
P2_COLOR = WHITE

PLAYER_W = 7
PLAYER_H = 12

MOVE_SPEED = 3
GRAVITY = 1
JUMP_POWER = -8
MAX_FALL = 7

SYNC_MS = 70
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

def make_one_player_state(player):
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


def make_state(p1, p2):
    # p1 and p2:
    # [x, y, vx, vy, facing, on_ground, falls]
    return (
        str(int(p1[0])) + "," +
        str(int(p1[1])) + "," +
        str(int(p1[2])) + "," +
        str(int(p1[3])) + "," +
        str(int(p1[4])) + "," +
        str(int(p1[5])) + "," +
        str(int(p1[6])) + "," +

        str(int(p2[0])) + "," +
        str(int(p2[1])) + "," +
        str(int(p2[2])) + "," +
        str(int(p2[3])) + "," +
        str(int(p2[4])) + "," +
        str(int(p2[5])) + "," +
        str(int(p2[6]))
    )


def parse_state(data):
    try:
        parts = data.split(",")

        if len(parts) < 14:
            return None

        p1 = [
            parse_int(parts[0]),
            parse_int(parts[1]),
            parse_int(parts[2]),
            parse_int(parts[3]),
            parse_int(parts[4]),
            parse_int(parts[5]),
            parse_int(parts[6])
        ]

        p2 = [
            parse_int(parts[7]),
            parse_int(parts[8]),
            parse_int(parts[9]),
            parse_int(parts[10]),
            parse_int(parts[11]),
            parse_int(parts[12]),
            parse_int(parts[13])
        ]

        return p1, p2

    except:
        return None

def smooth_correct_player(local_player, real_player):
    # Smoothly correct x/y so the player does not snap.
    diff_x = real_player[0] - local_player[0]
    diff_y = real_player[1] - local_player[1]

    if diff_x > 18 or diff_x < -18 or diff_y > 18 or diff_y < -18:
        local_player[0] = real_player[0]
        local_player[1] = real_player[1]
    else:
        local_player[0] = local_player[0] + diff_x // 3
        local_player[1] = local_player[1] + diff_y // 3

    # These should match the host.
    local_player[2] = real_player[2]
    local_player[3] = real_player[3]
    local_player[4] = real_player[4]
    local_player[5] = real_player[5]
    local_player[6] = real_player[6]


def make_player(x, y, facing):
    # x, y, vx, vy, facing, on_ground, falls
    return [x, y, 0, 0, facing, 0, 0]


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

    # gravity
    player[3] += GRAVITY

    if player[3] > MAX_FALL:
        player[3] = MAX_FALL

    # move
    player[0] += player[2]
    player[1] += player[3]

    # screen side bounds
    player[0] = clamp(player[0], -20, SCREEN_W + 20)

    # platform collision
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

    # fall off map
    if player[1] > SCREEN_H + 20:
        player[6] += 1
        respawn_player(player, player_num)


def draw_player(oled, player, color, label):
    x = int(player[0])
    y = int(player[1])
    facing = int(player[4])

    # body
    oled.fill_rect(x, y, PLAYER_W, PLAYER_H, color)

    # head
    oled.fill_rect(x + 2, y - 3, 3, 3, color)

    # tiny sword/face direction marker
    if facing >= 0:
        oled.hline(x + PLAYER_W, y + 5, 5, color)
    else:
        oled.hline(x - 5, y + 5, 5, color)

    # label
    oled.text(label, x, y - 11, color)


def draw_game(oled, role, p1, p2, net_ok):
    oled.fill(BLACK)

    # title/status
    if role == "host":
        oled.text("H", 2, 2, WHITE)
    else:
        oled.text("J", 2, 2, WHITE)

    oled.text("P1 falls:" + str(p1[6]), 18, 2, WHITE)
    oled.text("P2:" + str(p2[6]), 110, 2, WHITE)

    if net_ok:
        oled.pixel(78, 2, WHITE)
    else:
        oled.text("!", 76, 2, WHITE)

    # map
    oled.fill_rect(PLATFORM_X, PLATFORM_Y, PLATFORM_W, PLATFORM_H, WHITE)

    # small platform ends
    oled.vline(PLATFORM_X, PLATFORM_Y, 6, WHITE)
    oled.vline(PLATFORM_X + PLATFORM_W, PLATFORM_Y, 6, WHITE)

    # players
    draw_player(oled, p1, P1_COLOR, "1")
    draw_player(oled, p2, P2_COLOR, "2")

    oled.show()


def main(oled, controls, settings, role, room_code):
    wait_screen(oled, "FORGE FIGHTERS", "CONNECTING", room_code)

    mp_mode = settings.get("mp_mode", "online")
    ws = MultiplayerClient(mode)

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

    # p1 = host, p2 = joiner
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
        # HOST: real game simulation
        # -------------------------
        if role == "host":
            if time.ticks_diff(now, last_frame) > FRAME_MS:
                apply_player_input(p1, left, right, up)
                apply_player_input(p2, j_left, j_right, j_up)

                update_physics(p1, 1)
                update_physics(p2, 2)

                last_frame = now

            if time.ticks_diff(now, last_sync) > SYNC_MS:
                state = make_state(p1, p2)

                reply = ws.sync(state)
                peer = parse_peer_message(reply)

                if peer != "":
                    j_left, j_right, j_up = parse_input_packet(peer)
                    net_ok = True
                    last_good_net = now
                else:
                    net_ok = False

                last_sync = now

        # -------------------------
        # JOINER: send input, receive state
        # -------------------------
        # -------------------------
        # JOINER: local prediction + host correction
        # -------------------------
        else:
            # Move Player 2 locally immediately.
            # This makes the joiner's own sprite feel smooth.
            if time.ticks_diff(now, last_frame) > FRAME_MS:
                apply_player_input(p2, left, right, up)
                update_physics(p2, 2)
                last_frame = now
        
            # Send input to host and receive real state.
            if time.ticks_diff(now, last_sync) > SYNC_MS:
                packet = make_input_packet(left, right, up)
        
                reply = ws.sync(packet)
                peer = parse_peer_message(reply)
        
                if peer != "":
                    parsed = parse_state(peer)
        
                    if parsed != None:
                        real_p1, real_p2 = parsed
        
                        # Player 1 is host-controlled, so use host state directly.
                        p1 = real_p1
        
                        # Player 2 is controlled locally, so smooth-correct it.
                        smooth_correct_player(p2, real_p2)
        
                        net_ok = True
                        last_good_net = now
                    else:
                        net_ok = False
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
