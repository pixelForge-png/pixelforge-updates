from machine import Pin
import random
import time
from buzzer_sounds import sound

# Screen size used by the color version. Change if your display is different.
SCREEN_W = 160
SCREEN_H = 80

# -----------------------------
# RGB565 colors
# -----------------------------
def color565(r, g, b):
    # Byte-swapped RGB565 for st7735_fb framebuffer driver.
    c = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return ((c & 0xFF) << 8) | (c >> 8)

# Use this instead if red and blue are swapped on your display.
def color565_bgr(r, g, b):
    c = ((b & 0xF8) << 8) | ((g & 0xFC) << 3) | (r >> 3)
    return ((c & 0xFF) << 8) | (c >> 8)

BLACK = color565(0, 0, 0)
WHITE = color565(255, 255, 255)
GRAY = color565(128, 128, 128)
DARK_GRAY = color565(40, 40, 40)
RED = color565(255, 0, 0)
GREEN = color565(0, 255, 0)
BLUE = color565(0, 0, 255)
YELLOW = color565(255, 255, 0)
CYAN = color565(0, 255, 255)
MAGENTA = color565(255, 0, 255)
ORANGE = color565(255, 128, 0)
PURPLE = color565(128, 0, 255)
PINK = color565(255, 80, 160)
HEALTH_GREEN = color565(0, 255, 80)
DANGER_RED = color565(255, 40, 40)
SHIELD_BLUE = color565(80, 180, 255)
SPACE_BLACK = color565(0, 0, 8)
STAR_WHITE = color565(240, 240, 255)
ENEMY_BULLET = color565(255, 80, 0)
PLAYER_BULLET = color565(0, 255, 255)
LASER_COLOR = color565(255, 0, 0)
FREEZE_COLOR = color565(120, 220, 255)
BOMB_COLOR = color565(255, 180, 0)
BOSS_GHOST = color565(180, 220, 255)
BOSS_CORE = color565(255, 0, 80)

# Color sprite palette:
# 0 = transparent. Other characters become colors.
GAME_PALETTE = {
    "0": None,
    "1": WHITE,
    "2": CYAN,
    "3": BLUE,
    "4": RED,
    "5": GREEN,
    "6": YELLOW,
    "7": ORANGE,
    "8": PURPLE,
    "9": GRAY,
    "A": MAGENTA,
    "B": SHIELD_BLUE,
    "C": BOSS_CORE,
    "D": DARK_GRAY,
    "E": color565(80, 255, 80),
    "F": color565(255, 120, 0),
    "G": BOSS_GHOST,
    "H": HEALTH_GREEN,
}

# -----------------------------
# Display helpers
# -----------------------------
def show_display(display):
    if hasattr(display, "show"):
        display.show()

def draw_text(display, text, x, y, color=WHITE):
    try:
        display.text(text, x, y, color)
    except TypeError:
        display.text(text, x, y)

def center_text_x(display, text, y, color=WHITE, screen_w=SCREEN_W):
    x = (screen_w - len(text) * 8) // 2
    draw_text(display, text, x, y, color)

def safe_pixel(display, x, y, color, screen_w=SCREEN_W, screen_h=SCREEN_H):
    if 0 <= x < screen_w and 0 <= y < screen_h:
        display.pixel(x, y, color)

def draw_sprite(display, sprite, x, y, color=WHITE, screen_w=SCREEN_W, screen_h=SCREEN_H):
    for row_index, row in enumerate(sprite):
        for col_index, pixel in enumerate(row):
            if pixel == "1":
                safe_pixel(display, x + col_index, y + row_index, color, screen_w, screen_h)

def draw_color_sprite(display, sprite, x, y, palette=GAME_PALETTE, transparent="0", screen_w=SCREEN_W, screen_h=SCREEN_H):
    for row_index, row in enumerate(sprite):
        for col_index, pixel in enumerate(row):
            if pixel != transparent and pixel in palette:
                color = palette[pixel]
                if color is not None:
                    safe_pixel(display, x + col_index, y + row_index, color, screen_w, screen_h)

# -----------------------------
# Tiny text
# -----------------------------
tiny_font = {
    "A": ["010", "101", "111", "101", "101"],
    "B": ["110", "101", "110", "101", "110"],
    "C": ["011", "100", "100", "100", "011"],
    "D": ["110", "101", "101", "101", "110"],
    "E": ["111", "100", "110", "100", "111"],
    "F": ["111", "100", "110", "100", "100"],
    "G": ["011", "100", "101", "101", "011"],
    "H": ["101", "101", "111", "101", "101"],
    "I": ["111", "010", "010", "010", "111"],
    "J": ["001", "001", "001", "101", "010"],
    "K": ["101", "101", "110", "101", "101"],
    "L": ["100", "100", "100", "100", "111"],
    "M": ["101", "111", "111", "101", "101"],
    "N": ["101", "111", "111", "111", "101"],
    "O": ["111", "101", "101", "101", "111"],
    "P": ["110", "101", "110", "100", "100"],
    "Q": ["111", "101", "101", "111", "001"],
    "R": ["110", "101", "110", "101", "101"],
    "S": ["011", "100", "111", "001", "110"],
    "T": ["111", "010", "010", "010", "010"],
    "U": ["101", "101", "101", "101", "111"],
    "V": ["101", "101", "101", "101", "010"],
    "W": ["101", "101", "111", "111", "101"],
    "X": ["101", "101", "010", "101", "101"],
    "Y": ["101", "101", "010", "010", "010"],
    "Z": ["111", "001", "010", "100", "111"],
    "0": ["111", "101", "101", "101", "111"],
    "1": ["010", "110", "010", "010", "111"],
    "2": ["111", "001", "111", "100", "111"],
    "3": ["111", "001", "111", "001", "111"],
    "4": ["101", "101", "111", "001", "001"],
    "5": ["111", "100", "111", "001", "111"],
    "6": ["111", "100", "111", "101", "111"],
    "7": ["111", "001", "010", "010", "010"],
    "8": ["111", "101", "111", "101", "111"],
    "9": ["111", "101", "111", "001", "111"],
    " ": ["000", "000", "000", "000", "000"],
    "/": ["001", "001", "010", "100", "100"],
    "-": ["000", "000", "111", "000", "000"],
    ":": ["000", "010", "000", "010", "000"],
    "!": ["010", "010", "010", "000", "010"],
    "?": ["111", "001", "010", "000", "010"],
}

def draw_tiny_char(display, char, x, y, color=WHITE):
    char = char.upper()
    if char in tiny_font:
        draw_sprite(display, tiny_font[char], x, y, color)
    else:
        draw_sprite(display, tiny_font["?"], x, y, color)

def draw_tiny_text(display, text, x, y, color=WHITE):
    for i in range(len(text)):
        draw_tiny_char(display, text[i], x + i * 4, y, color)

def draw_upgrade_name(display, upgrade_name, box_x, box_y, box_width, color=WHITE):
    words = upgrade_name.split(" ")
    for i in range(len(words)):
        word = words[i]
        word_width = len(word) * 4
        x = box_x + (box_width - word_width) // 2
        y = box_y + i * 7
        draw_tiny_text(display, word, x, y, color)

# -----------------------------
# Joystick helpers
# -----------------------------
def joystick_direction(joy_x, joy_y, low=22000, high=43000):
    x = joy_x.read_u16()
    y = joy_y.read_u16()
    right = x < low
    left = x > high
    down = y > high
    up = y < low
    return left, right, up, down, x, y

def joystick_pressed(joy_sw):
    return joy_sw.value() == 0

def wait_for_joystick_release(joy_sw):
    while joy_sw.value() == 0:
        time.sleep(0.01)

# -----------------------------
# Game logic helpers
# -----------------------------
def enemy_row(display, y, enemy_count, enemy_type, screen_w=SCREEN_W):
    enemies = []
    spacing = round((screen_w - 16) / enemy_count)
    if enemy_type == "tank":
        enemy_lives = 3
    elif enemy_type == "shielded":
        enemy_lives = 5
    elif enemy_type == "spawner":
        enemy_lives = 4
    elif enemy_type == "elite":
        enemy_lives = 4
    elif enemy_type == "bomber":
        enemy_lives = 3
    elif enemy_type == "splitter":
        enemy_lives = 2
    elif enemy_type == "charger":
        enemy_lives = 2
    else:
        enemy_lives = 1
    for i in range(enemy_count):
        enemy_x = 8 + spacing * i
        enemies.append([enemy_x, y, enemy_lives, enemy_type])
    return enemies

def make_level(display, levels, level, screen_w=SCREEN_W):
    enemies = []
    level_data = levels[level - 1]
    for row in level_data:
        row_enemies = enemy_row(display, row[2], row[1], row[0], screen_w)
        for enemy in row_enemies:
            enemies.append(enemy)
    return enemies

def update_enimies(enemies, bullet_x, bullet_y, bullet_damage=1):
    new_enemies = []
    bullet_hit = False
    hit_x = None
    hit_y = None
    points_gained = 0
    death_shots = []

    for enemy in enemies:
        if enemy[2] > 0:
            if bullet_hit == False:
                if bullet_x < enemy[0] + 8 and bullet_x + 2 > enemy[0] and bullet_y < enemy[1] + 8 and bullet_y + 2 > enemy[1]:
                    enemy[2] = enemy[2] - bullet_damage
                    bullet_hit = True
                    hit_x = enemy[0]
                    hit_y = enemy[1]
                    if enemy[3] == "basic":
                        sound(1200, 7000, 0.02)
                        sound(900, 7000, 0.02)
                    elif enemy[3] == "tank" or enemy[3] == "shielded":
                        sound(330, 9000, 0.01)
                        sound(220, 9000, 0.03)
                    elif enemy[3] == "shooter" or enemy[3] == "sniper" or enemy[3] == "elite":
                        sound(1400, 7000, 0.02)
                        sound(1000, 7000, 0.02)
                    elif enemy[3] == "fast" or enemy[3] == "dodger" or enemy[3] == "charger":
                        sound(2000, 7000, 0.02)
                        sound(2200, 7000, 0.02)
                    else:
                        sound(900, 7000, 0.02)

            if enemy[2] > 0:
                new_enemies.append([enemy[0], enemy[1], enemy[2], enemy[3]])
            else:
                if enemy[3] == "splitter":
                    death_shots.append([enemy[0] + 2, enemy[1] + 8])

                if enemy[3] == "basic":
                    points_gained += 10
                elif enemy[3] == "fast":
                    points_gained += 15
                elif enemy[3] == "shooter":
                    points_gained += 20
                elif enemy[3] == "tank":
                    points_gained += 30
                elif enemy[3] == "dodger":
                    points_gained += 25
                elif enemy[3] == "splitter":
                    points_gained += 35
                elif enemy[3] == "sniper":
                    points_gained += 40
                elif enemy[3] == "charger":
                    points_gained += 35
                elif enemy[3] == "shielded":
                    points_gained += 50
                elif enemy[3] == "spawner":
                    points_gained += 60
                elif enemy[3] == "bomber":
                    points_gained += 70
                elif enemy[3] == "elite":
                    points_gained += 90

    return new_enemies, bullet_hit, hit_x, hit_y, points_gained, death_shots

def wait_for_release(button):
    while button.value() == 0:
        time.sleep(0.01)


def button_pressed(button):
    return button.value() == 0


def upgrades(display, all_upgrades, button_B, button_G, button_R, button_Y):
    available_upgrades = []

    for upgrade in all_upgrades:
        if upgrade[1] < upgrade[2]:
            available_upgrades.append(upgrade)

    if len(available_upgrades) == 0:
        display.fill(BLACK)
        center_text_x(display, "No upgrades", 24, WHITE)
        show_display(display)
        time.sleep(1)
        return None

    rarity_weights = {
        "Common": 50,
        "Uncommon": 30,
        "Rare": 15,
        "Epic": 4,
        "Legendary": 1
    }

    weighted_upgrades = []

    for upgrade in available_upgrades:
        weight = rarity_weights[upgrade[3]]

        for i in range(weight):
            weighted_upgrades.append(upgrade)

    upgrade_choices = []
    choice_count = min(3, len(available_upgrades))

    while len(upgrade_choices) < choice_count:
        choice = random.choice(weighted_upgrades)

        if choice not in upgrade_choices:
            upgrade_choices.append(choice)

    selected = 0
    last_move = time.ticks_ms()

    while True:
        display.fill(BLACK)
        center_text_x(display, "UPGRADE", 0, YELLOW)

        box_positions = [4, 58, 112]
        box_width = 46

        for i in range(choice_count):
            box_x = box_positions[i]

            if i == selected:
                display.fill_rect(box_x, 10, box_width, 58, DARK_GRAY)

            display.rect(box_x, 10, box_width, 58, WHITE)
            draw_upgrade_name(display, upgrade_choices[i][0], box_x, 24, box_width, WHITE)

            count_text = str(upgrade_choices[i][1]) + "/" + str(upgrade_choices[i][2])
            draw_tiny_text(display, count_text, box_x + 10, 48, YELLOW)
            draw_tiny_text(display, upgrade_choices[i][3], box_x + 2, 58, CYAN)

        draw_tiny_text(display, "BLUE = left", 2, 72, BLUE)
        draw_tiny_text(display, "GREEN = select", 50, 72, GREEN)
        draw_tiny_text(display, "RED = right", 110, 72, RED)
        show_display(display)

        now = time.ticks_ms()

        if time.ticks_diff(now, last_move) > 180:
            if button_pressed(button_B) and selected > 0:
                selected -= 1
                last_move = now
            elif button_pressed(button_R) and selected < choice_count - 1:
                selected += 1
                last_move = now

        if button_pressed(button_G):
            player_choice = upgrade_choices[selected]
            player_choice[1] = player_choice[1] + 1
            wait_for_release(button_G)
            return player_choice

        if button_pressed(button_Y):
            wait_for_release(button_Y)
            return None

        time.sleep(0.02)


def transition(display, num):
    if num == 1:
        display.fill(WHITE)
    else:
        display.fill(BLACK)
    show_display(display)
    time.sleep(0.15)

def make_boss(bosses):
    boss_template = random.choice(bosses)
    boss = [
        boss_template[0],  # name
        boss_template[1],  # sprite
        boss_template[2],  # x
        boss_template[3],  # y
        boss_template[4],  # lives
        boss_template[5],  # max lives
        boss_template[6],  # direction
        boss_template[7],  # shoot delay
        boss_template[8],  # attack type
        0                  # shoot timer
    ]
    return boss

def update_boss(display, boss, bullets, bullet_speed, freeze_timer, palette=GAME_PALETTE, bullet_damage=1):
    boss_name = boss[0]
    boss_sprite = boss[1]
    boss_x = boss[2]
    boss_y = boss[3]
    boss_lives = boss[4]
    boss_max_lives = boss[5]
    boss_direction = boss[6]
    boss_shoot_delay = boss[7]
    boss_attack = boss[8]
    boss_shoot_timer = boss[9]
    if freeze_timer <= 0:
        boss_x = boss_x + boss_direction
        if boss_name == "Ghost" and random.randint(0, 80) == 0:
            boss_x = random.randint(0, 144)
        if boss_x <= 0 or boss_x >= 144:
            boss_direction = boss_direction * -1
    draw_color_sprite(display, boss_sprite, boss_x, boss_y, palette)
    new_bullets = []
    for b in bullets:
        b[1] = b[1] - bullet_speed
        if b[0] < boss_x + 16 and b[0] + 2 > boss_x and b[1] < boss_y + 16 and b[1] + 3 > boss_y:
            boss_lives = boss_lives - bullet_damage
            sound(1400, 7000, 0.02)
            sound(900, 7000, 0.02)
        else:
            if b[1] > -3:
                new_bullets.append(b)
    if boss_lives <= 0:
        return None, new_bullets
    boss = [boss_name, boss_sprite, boss_x, boss_y, boss_lives, boss_max_lives, boss_direction, boss_shoot_delay, boss_attack, boss_shoot_timer]
    return boss, new_bullets


AIM_SCALE = 100


def make_aimed_enemy_bullet(start_x, start_y, target_x, target_y, speed=2):
    # Fixed-point aimed bullet. Avoids floats so it runs well on the Pico.
    dx = target_x - start_x
    dy = target_y - start_y

    # Manhattan distance is cheaper than sqrt and good enough for aiming.
    distance = abs(dx) + abs(dy)
    if distance < 1:
        distance = 1

    vx = int(dx * speed * AIM_SCALE / distance)
    vy = int(dy * speed * AIM_SCALE / distance)

    # Enemy bullets should still move downward at least a little.
    if vy < int(0.6 * AIM_SCALE):
        vy = int(0.6 * AIM_SCALE)

    return [start_x * AIM_SCALE, start_y * AIM_SCALE, vx, vy]


def bullet_screen_x(bullet):
    return bullet[0] // AIM_SCALE


def bullet_screen_y(bullet):
    return bullet[1] // AIM_SCALE


def boss_attack(enemy_bullets, boss, target_x, target_y, bullet_speed=2):
    boss_x = boss[2]
    boss_y = boss[3]
    boss_attack_type = boss[8]

    if boss_attack_type == "triple":
        enemy_bullets.append(make_aimed_enemy_bullet(boss_x + 2, boss_y + 16, target_x, target_y, bullet_speed))
        enemy_bullets.append(make_aimed_enemy_bullet(boss_x + 7, boss_y + 16, target_x, target_y, bullet_speed))
        enemy_bullets.append(make_aimed_enemy_bullet(boss_x + 12, boss_y + 16, target_x, target_y, bullet_speed))

    elif boss_attack_type == "heavy":
        enemy_bullets.append(make_aimed_enemy_bullet(boss_x + 7, boss_y + 16, target_x, target_y, bullet_speed + 1))

    elif boss_attack_type == "teleport":
        # Ghost boss now shoots only from its own position, but aims at the player.
        enemy_bullets.append(make_aimed_enemy_bullet(boss_x + 7, boss_y + 16, target_x, target_y, bullet_speed))

    return enemy_bullets

shield_icon = ["00111100", "01000010", "10011001", "10111101", "10111101", "10011001", "01000010", "00111100"]
laser_icon = ["00100100", "00100100", "00100100", "11111111", "00100100", "00100100", "00100100", "00100100"]
bomb_icon = ["00011000", "00111100", "01111110", "01111110", "00111100", "00100100", "01000010", "10000001"]
freeze_icon = ["10010010", "01010100", "00111000", "11111110", "00111000", "01010100", "10010010", "00010000"]
heal_icon = ["00011000", "00011000", "01111110", "01111110", "00011000", "00011000", "00000000", "00000000"]

def draw_special_icon(display, special_ability):
    if special_ability == "Shield":
        draw_sprite(display, shield_icon, 148, 0, SHIELD_BLUE)
    elif special_ability == "Laser":
        draw_sprite(display, laser_icon, 148, 0, LASER_COLOR)
    elif special_ability == "Bomb":
        draw_sprite(display, bomb_icon, 148, 0, BOMB_COLOR)
    elif special_ability == "Freeze":
        draw_sprite(display, freeze_icon, 148, 0, FREEZE_COLOR)
    elif special_ability == "Heal":
        draw_sprite(display, heal_icon, 148, 0, HEALTH_GREEN)
    elif special_ability == "Pulse":
        display.rect(148, 0, 8, 8, CYAN)
        display.fill_rect(151, 3, 2, 2, CYAN)
    elif special_ability == "Missile":
        display.fill_rect(151, 0, 2, 8, ORANGE)
        display.pixel(150, 1, RED)
        display.pixel(153, 1, RED)
    elif special_ability == "Overdrive":
        display.fill_rect(148, 2, 8, 4, YELLOW)


