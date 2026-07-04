import time
import random
from helpers import online_relay

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

def draw_center_text(oled, text, y, color=WHITE):
    x = (SCREEN_W - len(text) * 8) // 2
    oled.text(text, x, y, color)

def parse_int(value, default=0):
    try:
        return int(value)
    except:
        return default

def parse_state(data):
    # Expected:
    # bx,by,hy,jy,hs,js
    try:
        parts = data.split(",")
        if len(parts) < 6:
            return None

        return {
            "ball_x": parse_int(parts[0]),
            "ball_y": parse_int(parts[1]),
            "host_y": parse_int(parts[2]),
            "joiner_y": parse_int(parts[3]),
            "host_score": parse_int(parts[4]),
            "joiner_score": parse_int(parts[5])
        }
    except:
        return None

def make_state(ball_x, ball_y, host_y, joiner_y, host_score, joiner_score):
    return (
        str(int(ball_x)) + "," +
        str(int(ball_y)) + "," +
        str(int(host_y)) + "," +
        str(int(joiner_y)) + "," +
        str(int(host_score)) + "," +
        str(int(joiner_score))
    )

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

def draw_game(oled, role, room_code, ball_x, ball_y, host_y, joiner_y, host_score, joiner_score):
    oled.fill(BLACK)

    # Score
    oled.text(str(host_score), 58, 2, WHITE)
    oled.text(str(joiner_score), 94, 2, WHITE)

    # Center line
    for y in range(12, SCREEN_H, 8):
        oled.fill_rect(SCREEN_W // 2 - 1, y, 2, 4, WHITE)

    # Paddles
    oled.fill_rect(HOST_X, int(host_y), PADDLE_W, PADDLE_H, WHITE)
    oled.fill_rect(JOINER_X, int(joiner_y), PADDLE_W, PADDLE_H, WHITE)

    # Ball
    oled.fill_rect(int(ball_x), int(ball_y), BALL_SIZE, BALL_SIZE, WHITE)

    # Tiny role indicator
    if role == "host":
        oled.text("H", 2, 2, WHITE)
    else:
        oled.text("J", 150, 2, WHITE)

    oled.show()

def wait_screen(oled, title, line1="", line2=""):
    oled.fill(BLACK)
    draw_center_text(oled, title, 12, WHITE)
    draw_center_text(oled, line1, 34, WHITE)
    draw_center_text(oled, line2, 54, WHITE)
    oled.show()

def main(oled, controls, settings, role, room_code):
    host_y = 31
    joiner_y = 31

    host_score = 0
    joiner_score = 0

    ball_x, ball_y, ball_dx, ball_dy = reset_ball(True)

    last_send = time.ticks_ms()
    last_read = time.ticks_ms()
    last_frame = time.ticks_ms()

    wait_screen(oled, "MP PONG", role.upper(), room_code)
    time.sleep(1)

    while True:
        left, right, up, down = controls["joystick"]()

        # Yellow exits
        if controls["yellow"]():
            time.sleep(0.3)
            return

        # -----------------------------
        # Host controls real game
        # -----------------------------
        if role == "host":
            # Host paddle movement
            if up:
                host_y -= 3
            if down:
                host_y += 3

            host_y = clamp(host_y, 12, SCREEN_H - PADDLE_H)

            now = time.ticks_ms()

            # Read joiner paddle sometimes
            if time.ticks_diff(now, last_read) > 180:
                read_result = online_relay.read_data(room_code, "host")

                if read_result.get("ok", False):
                    data = read_result.get("data", "")

                    if data != "":
                        joiner_y = clamp(parse_int(data, joiner_y), 12, SCREEN_H - PADDLE_H)

                last_read = now

            # Game physics
            if time.ticks_diff(now, last_frame) > 30:
                ball_x += ball_dx
                ball_y += ball_dy

                # Top/bottom bounce
                if ball_y <= 12:
                    ball_y = 12
                    ball_dy = abs(ball_dy)

                if ball_y >= SCREEN_H - BALL_SIZE:
                    ball_y = SCREEN_H - BALL_SIZE
                    ball_dy = -abs(ball_dy)

                # Host paddle collision
                if (
                    ball_x <= HOST_X + PADDLE_W and
                    ball_x + BALL_SIZE >= HOST_X and
                    ball_y + BALL_SIZE >= host_y and
                    ball_y <= host_y + PADDLE_H
                ):
                    ball_x = HOST_X + PADDLE_W + 1
                    ball_dx = abs(ball_dx)

                    # Add a little angle based on where it hit
                    hit_center = host_y + PADDLE_H // 2
                    if ball_y < hit_center - 4:
                        ball_dy = -2
                    elif ball_y > hit_center + 4:
                        ball_dy = 2

                # Joiner paddle collision
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

                # Scoring
                if ball_x < -BALL_SIZE:
                    joiner_score += 1
                    ball_x, ball_y, ball_dx, ball_dy = reset_ball(True)

                if ball_x > SCREEN_W:
                    host_score += 1
                    ball_x, ball_y, ball_dx, ball_dy = reset_ball(False)

                last_frame = now

            # Send full game state sometimes
            if time.ticks_diff(now, last_send) > 120:
                state = make_state(
                    ball_x,
                    ball_y,
                    host_y,
                    joiner_y,
                    host_score,
                    joiner_score
                )

                online_relay.send_data(room_code, "host", state)
                last_send = now

            draw_game(
                oled,
                role,
                room_code,
                ball_x,
                ball_y,
                host_y,
                joiner_y,
                host_score,
                joiner_score
            )

        # -----------------------------
        # Joiner sends paddle, receives game
        # -----------------------------
        else:
            if up:
                joiner_y -= 3
            if down:
                joiner_y += 3

            joiner_y = clamp(joiner_y, 12, SCREEN_H - PADDLE_H)

            now = time.ticks_ms()

            # Send joiner paddle position
            if time.ticks_diff(now, last_send) > 120:
                online_relay.send_data(room_code, "joiner", str(int(joiner_y)))
                last_send = now

            # Read host state
            if time.ticks_diff(now, last_read) > 120:
                read_result = online_relay.read_data(room_code, "joiner")

                if read_result.get("ok", False):
                    data = read_result.get("data", "")
                    state = parse_state(data)

                    if state != None:
                        ball_x = state["ball_x"]
                        ball_y = state["ball_y"]
                        host_y = state["host_y"]
                        joiner_y = state["joiner_y"]
                        host_score = state["host_score"]
                        joiner_score = state["joiner_score"]

                last_read = now

            draw_game(
                oled,
                role,
                room_code,
                ball_x,
                ball_y,
                host_y,
                joiner_y,
                host_score,
                joiner_score
            )

        time.sleep(0.02)
