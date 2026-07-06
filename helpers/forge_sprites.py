import time

WHITE = 65535

ACTION_IDLE = 0
ACTION_RUN = 1
ACTION_JUMP = 2
ACTION_ATTACK = 3
ACTION_HURT = 4
ACTION_SPECIAL = 5
ACTION_CROUCH = 6
ACTION_SPAWN = 7


def _line(oled, x1, y1, x2, y2, color):
    # Tiny Bresenham line for MicroPython displays.
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


def _flip_x(value, facing):
    if facing >= 0:
        return value
    return -value


def _draw_stick(oled, x, y, facing, frame, color=WHITE):
    # frame values are relative points:
    # head, neck, hip, left/right hand, left/right foot, weapon end
    bob = frame.get("bob", 0)

    head = frame.get("head", [0, -12 + bob])
    neck = frame.get("neck", [0, -7 + bob])
    hip = frame.get("hip", [0, 0 + bob])
    hand1 = frame.get("hand1", [-4, -5 + bob])
    hand2 = frame.get("hand2", [5, -4 + bob])
    foot1 = frame.get("foot1", [-3, 6])
    foot2 = frame.get("foot2", [4, 6])
    sword = frame.get("sword", [12, -4 + bob])

    hx = x + _flip_x(head[0], facing)
    hy = y + head[1]

    nx = x + _flip_x(neck[0], facing)
    ny = y + neck[1]

    px = x + _flip_x(hip[0], facing)
    py = y + hip[1]

    h1x = x + _flip_x(hand1[0], facing)
    h1y = y + hand1[1]

    h2x = x + _flip_x(hand2[0], facing)
    h2y = y + hand2[1]

    f1x = x + _flip_x(foot1[0], facing)
    f1y = y + foot1[1]

    f2x = x + _flip_x(foot2[0], facing)
    f2y = y + foot2[1]

    sx = x + _flip_x(sword[0], facing)
    sy = y + sword[1]

    # head
    oled.rect(hx - 2, hy - 2, 5, 5, color)

    # body
    _line(oled, nx, ny, px, py, color)

    # arms
    _line(oled, nx, ny, h1x, h1y, color)
    _line(oled, nx, ny, h2x, h2y, color)

    # legs
    _line(oled, px, py, f1x, f1y, color)
    _line(oled, px, py, f2x, f2y, color)

    # weapon/sword from hand2
    _line(oled, h2x, h2y, sx, sy, color)


def _kael_frame(action, frame):
    if action == ACTION_RUN:
        if frame % 2 == 0:
            return {
                "bob": 0,
                "hand1": [-5, -5],
                "hand2": [5, -5],
                "foot1": [-5, 6],
                "foot2": [5, 5],
                "sword": [13, -5]
            }
        return {
            "bob": 1,
            "hand1": [-3, -4],
            "hand2": [6, -5],
            "foot1": [4, 6],
            "foot2": [-4, 5],
            "sword": [14, -4]
        }

    if action == ACTION_JUMP:
        return {
            "bob": -1,
            "hand1": [-5, -8],
            "hand2": [5, -8],
            "foot1": [-3, 5],
            "foot2": [4, 5],
            "sword": [12, -10]
        }

    if action == ACTION_ATTACK:
        return {
            "bob": 0,
            "hand1": [-5, -4],
            "hand2": [8, -5],
            "foot1": [-4, 6],
            "foot2": [4, 6],
            "sword": [18, -5]
        }

    if action == ACTION_SPECIAL:
        return {
            "bob": 0,
            "hand1": [-6, -5],
            "hand2": [8, -6],
            "foot1": [-6, 6],
            "foot2": [5, 6],
            "sword": [22, -6]
        }

    if action == ACTION_CROUCH:
        return {
            "head": [0, -8],
            "neck": [0, -4],
            "hip": [0, 2],
            "hand1": [-5, -2],
            "hand2": [5, -2],
            "foot1": [-5, 6],
            "foot2": [5, 6],
            "sword": [12, -1]
        }

    if action == ACTION_HURT:
        return {
            "bob": 1,
            "hand1": [-7, -8],
            "hand2": [4, -8],
            "foot1": [-4, 6],
            "foot2": [4, 6],
            "sword": [9, -9]
        }

    if action == ACTION_SPAWN:
        return {
            "bob": -2,
            "hand1": [-5, -8],
            "hand2": [5, -8],
            "foot1": [-3, 5],
            "foot2": [3, 5],
            "sword": [10, -9]
        }

    # idle standing animation
    if frame % 2 == 0:
        bob = 0
    else:
        bob = 1

    return {
        "bob": bob,
        "hand1": [-4, -5 + bob],
        "hand2": [5, -4 + bob],
        "foot1": [-3, 6],
        "foot2": [4, 6],
        "sword": [12, -4 + bob]
    }


def _nyra_frame(action, frame):
    base = _kael_frame(action, frame)

    # Nyra is slimmer and more energetic.
    if action == ACTION_IDLE:
        base["hand1"] = [-5, -6 + (frame % 2)]
        base["hand2"] = [6, -5 + (frame % 2)]
        base["sword"] = [15, -5 + (frame % 2)]

    elif action == ACTION_RUN:
        base["sword"] = [17, -4]
        base["foot1"] = [-6, 6]
        base["foot2"] = [6, 5]

    elif action == ACTION_SPECIAL:
        base["sword"] = [24, -5]
        base["hand2"] = [9, -5]
        base["foot1"] = [-7, 6]
        base["foot2"] = [7, 6]

    return base


def _brugo_frame(action, frame):
    base = _kael_frame(action, frame)

    # Brugo is wider/heavier.
    if action == ACTION_IDLE:
        base["hand1"] = [-6, -4 + (frame % 2)]
        base["hand2"] = [6, -4 + (frame % 2)]
        base["sword"] = [11, -2 + (frame % 2)]
        base["foot1"] = [-5, 6]
        base["foot2"] = [5, 6]

    elif action == ACTION_RUN:
        base["hand1"] = [-6, -4]
        base["hand2"] = [6, -4]
        base["sword"] = [12, -2]
        base["foot1"] = [-5, 6]
        base["foot2"] = [5, 6]

    elif action == ACTION_SPECIAL:
        base["hand1"] = [-8, -3]
        base["hand2"] = [8, -3]
        base["sword"] = [16, 2]
        base["foot1"] = [-7, 6]
        base["foot2"] = [7, 6]

    elif action == ACTION_CROUCH:
        base["head"] = [0, -7]
        base["neck"] = [0, -3]
        base["hip"] = [0, 2]
        base["hand1"] = [-7, -1]
        base["hand2"] = [7, -1]
        base["foot1"] = [-7, 6]
        base["foot2"] = [7, 6]
        base["sword"] = [12, 0]

    return base


def draw_fighter(oled, char_id, x, y, facing, action, anim_tick, color=WHITE):
    frame = (anim_tick // 8) % 2

    if char_id == "nyra":
        data = _nyra_frame(action, frame)
    elif char_id == "brugo":
        data = _brugo_frame(action, frame)
    else:
        data = _kael_frame(action, frame)

    _draw_stick(oled, x, y, facing, data, color)

    # Character-specific little detail
    if char_id == "nyra":
        if facing >= 0:
            oled.pixel(x - 5, y - 4, color)
            oled.pixel(x - 7, y - 2, color)
        else:
            oled.pixel(x + 5, y - 4, color)
            oled.pixel(x + 7, y - 2, color)

    elif char_id == "brugo":
        oled.hline(x - 5, y - 9, 11, color)


def draw_blast(oled, x, y, tick, color=WHITE):
    radius = 4 + tick * 2

    # big diagonal blast lines
    oled.hline(x - radius, y, radius * 2, color)
    oled.vline(x, y - radius, radius * 2, color)

    _line(oled, x - radius, y - radius, x + radius, y + radius, color)
    _line(oled, x - radius, y + radius, x + radius, y - radius, color)

    if tick % 2 == 0:
        oled.rect(x - radius // 2, y - radius // 2, radius, radius, color)
