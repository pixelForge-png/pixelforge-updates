import time
import random
from helpers.ws_relay import WebSocketClient

SCREEN_W = 160
SCREEN_H = 80

WHITE = 65535
BLACK = 0

PADDLE_W = 4
PADDLE_H = 18

HOST_X = 6
JOINER_X = SCREEN_W - 10
BALL_SIZE = 4

def clamp(value, low, high):
    if value < low:
        return low
    if value > high:
        return high
    return value

def center_text(oled, text, y, color=WHITE):
    x = (SCREEN_W - len(text) * 8) // 2
    oled.text(text, x, y, color)

def parse_int(value, default=0):
    try:
        return int(value)
    except:
        return default

def make_state(ball_x, ball_y, host_y, joiner_y, host_score, joiner_score):
    return (
        str(int(ball_x)) + "," +
        str(int(ball_y)) + "," +
        str(int(host_y)) + "," +
        str(int(joiner_y)) + "," +
        str(int(host_score)) + "," +
        str(int(joiner_score))
    )

def parse_state(data):
    try:
        parts = data.split(",")

        if len(parts) < 6:
            return None

        return [
            parse_int(parts[0]),
            parse_int(parts[1]),
            parse_int(parts[2]),
            parse_int(parts[3]),
            parse_int(parts[4]),
            parse_int(parts[5])
        ]
    except:
        return None

def parse_peer_message(msg):
    # Expected:
    # PEER|message_id|data
    if msg == None:
        return ""

    if not msg.startswith("PEER|"):
        return ""

    parts = msg.split("|", 2)

    if len(parts) < 3:
        return ""

    return parts[2]

def reset_ball(toward_joiner=True):
    ball_x = SCREEN_W // 2
    ball_y = SCREEN_H // 2

    if toward_joiner:
        ball_dx = 2
    else:
        ball_dx = -2

    if random.randint(0, 1) == 0:
        ball_dy = 1
    else:
        ball_dy = -1

    return ball_x, ball_y, ball_dx, ball_dy

def draw_game(oled, role, ball_x, ball_y, host_y, joiner_y, host_score, joiner_score, net_ok):
    oled.fill(BLACK)

    oled.text(str(host_score), 58, 2, WHITE)
    oled.text(str(joiner_score), 94, 2, WHITE)

    for y in range(12, SCREEN_H, 8):
        oled.fill_rect(SCREEN_W // 2 - 1, y, 2, 4, WHITE)

    oled.fill_rect(HOST_X, int(host_y), PADDLE_W, PADDLE_H, WHITE)
    oled.fill_rect(JOINER_X, int(joiner_y), PADDLE_W, PADDLE_H, WHITE)

    oled.fill_rect(int(ball_x), int(ball_y), BALL_SIZE, BALL_SIZE, WHITE)

    if role == "host":
        oled.text("H", 2, 2, WHITE)
    else:
        oled.text("J", 150, 2, WHITE)

    if net_ok:
        oled.pixel(78, 2, WHITE)
    else:
        oled.text("!", 76, 2, WHITE)

    oled.show()

def wait_screen(oled, title, line1="", line2=""):
    oled.fill(BLACK)
    center_text(oled, title, 12, WHITE)
    center_text(oled, line1, 34, WHITE)
    center_text(oled, line2, 54, WHITE)
    oled.show()

def main(oled, controls, settings, role, room_code):
    wait_screen(oled, "WS PONG", "CONNECTING", room_code)

    ws = WebSocketClient()

    try:
        ws.connect(room_code, role)
    except Exception as e:
        oled.fill(BLACK)
        center_text(oled, "WS FAIL", 16, WHITE)
        center_text(oled, str(e)[:18], 38, WHITE)
        oled.show()
        time.sleep(3)
        return

    host_y = 31
    joiner_y = 31

    host_score = 0
    joiner_score = 0

    ball_x, ball_y, ball_dx, ball_dy = reset_ball(True)

    last_frame = time.ticks_ms()
    last_sync = time.ticks_ms()
    net_ok = False

    wait_screen(oled, "WS PONG", role.upper(), room_code)
    time.sleep(0.5)

    while True:
        left, right, up, down = controls["joystick"]()

        if controls["yellow"]():
            time.sleep(0.3)
            ws.close()
            return

        now = time.ticks_ms()

        if role == "host":
            if up:
                host_y -= 3
            if down:
                host_y += 3

            host_y = clamp(host_y, 12, SCREEN_H - PADDLE_H)

            if time.ticks_diff(now, last_frame) > 35:
                ball_x += ball_dx
                ball_y += ball_dy

                if ball_y <= 12:
                    ball_y = 12
                    ball_dy = abs(ball_dy)

                if ball_y >= SCREEN_H - BALL_SIZE:
                    ball_y = SCREEN_H - BALL_SIZE
                    ball_dy = -abs(ball_dy)

                if (
                    ball_x <= HOST_X + PADDLE_W and
                    ball_x + BALL_SIZE >= HOST_X and
                    ball_y + BALL_SIZE >= host_y and
                    ball_y <= host_y + PADDLE_H
                ):
                    ball_x = HOST_X + PADDLE_W + 1
                    ball_dx = abs(ball_dx)

                    hit_center = host_y + PADDLE_H // 2
                    if ball_y < hit_center - 4:
                        ball_dy = -2
                    elif ball_y > hit_center + 4:
                        ball_dy = 2

                if (
                    ball_x + BALL_SIZE >= JOINER_X and
                    ball_x <= JOINER_X + PADDLE_W and
                    ball_y + BALL_SIZE >= joiner_y and
                    ball_y <= joiner_y + PADDLE_H
                ):
                    ball_x = JOINER_X - BALL_SIZE - 1
                    ball_dx = -abs(ball_dx)

                    hit_center = joiner_y + PADDLE_H // 2
                    if ball_y < hit_center - 4:
                        ball_dy = -2
                    elif ball_y > hit_center + 4:
                        ball_dy = 2

                if ball_x < -BALL_SIZE:
                    joiner_score += 1
                    ball_x, ball_y, ball_dx, ball_dy = reset_ball(True)

                if ball_x > SCREEN_W:
                    host_score += 1
                    ball_x, ball_y, ball_dx, ball_dy = reset_ball(False)

                last_frame = now

            if time.ticks_diff(now, last_sync) > 90:
                state = make_state(
                    ball_x,
                    ball_y,
                    host_y,
                    joiner_y,
                    host_score,
                    joiner_score
                )

                reply = ws.sync(state)
                peer = parse_peer_message(reply)

                if peer != "":
                    joiner_y = clamp(parse_int(peer, joiner_y), 12, SCREEN_H - PADDLE_H)
                    net_ok = True
                else:
                    net_ok = False

                last_sync = now

        else:
            if up:
                joiner_y -= 3
            if down:
                joiner_y += 3

            joiner_y = clamp(joiner_y, 12, SCREEN_H - PADDLE_H)

            if time.ticks_diff(now, last_sync) > 90:
                reply = ws.sync(str(int(joiner_y)))
                peer = parse_peer_message(reply)

                if peer != "":
                    state = parse_state(peer)

                    if state != None:
                        ball_x = state[0]
                        ball_y = state[1]
                        host_y = state[2]
                    
                        # IMPORTANT:
                        # Do NOT overwrite joiner_y here.
                        # The joiner should control and display its own paddle locally.
                        # The host's joiner_y is always a little old because of network delay.
                        # joiner_y = state[3]
                    
                        host_score = state[4]
                        joiner_score = state[5]
                        net_ok = True
                    else:
                        net_ok = False
                else:
                    net_ok = False

                last_sync = now

        draw_game(
            oled,
            role,
            ball_x,
            ball_y,
            host_y,
            joiner_y,
            host_score,
            joiner_score,
            net_ok
        )

        time.sleep(0.02)
