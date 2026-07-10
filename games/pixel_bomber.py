import time
import random
from helpers.buzzer_sounds import sound
from helpers.oled_functions import (
    BLACK, WHITE, GRAY, DARK_GRAY, RED, GREEN, BLUE, YELLOW, CYAN, MAGENTA,
    ORANGE, PURPLE, HEALTH_GREEN, DANGER_RED, SHIELD_BLUE, SPACE_BLACK,
    ENEMY_BULLET, PLAYER_BULLET, LASER_COLOR, FREEZE_COLOR, BOMB_COLOR,
    GAME_PALETTE,
    center_text_x, draw_tiny_text, draw_color_sprite, draw_sprite, show_display,
    joystick_direction, joystick_pressed, wait_for_joystick_release,
    make_level, update_enimies, upgrades, transition, make_boss, update_boss,
    boss_attack, draw_special_icon, make_aimed_enemy_bullet, bullet_screen_x, bullet_screen_y
)

# -----------------------------
# Launcher-compatible constants
# -----------------------------
SCREEN_W = 160
SCREEN_H = 80

MAX_PLAYER_BULLETS = 10
MAX_ENEMY_BULLETS = 16

# Player can move in both X and Y, but cannot fly behind enemy rows.
PLAYER_BASE_MIN_Y = 0

PLAYER_BULLET_PALETTE = {"0": None, "1": PLAYER_BULLET}
ENEMY_BULLET_PALETTE = {"0": None, "4": ENEMY_BULLET}

# -----------------------------
# Color sprites
# 0 = transparent. Other characters use GAME_PALETTE.
# -----------------------------
player = [
    "*"
]

bomb = [
    "11",
    "11"
]

enemy_bullet_sprite = [
    "44",
    "44"
]

basic = [
    "E000000E",
    "0E0000E0",
    "EEEEEEEE",
    "E0EEEE0E",
    "EEEEEEEE",
    "00E00E00",
    "0E0EE0E0",
    "E0E00E0E"
]

fast_enemy = [
    "00FEE000",
    "0FEEEE00",
    "FFE00EFF",
    "FFFFFFFF",
    "00FFFF00",
    "0FF00FF0",
    "FF0000FF",
    "F000000F"
]

tank = [
    "09999990",
    "99999999",
    "99D99D99",
    "99999999",
    "99999999",
    "09999990",
    "00900900",
    "09000090"
]

shooter = [
    "00AAAA00",
    "0AAAAAA0",
    "AA0AA0AA",
    "AAAAAAAA",
    "00AAAA00",
    "000AA000",
    "00A00A00",
    "0A0000A0"
]


dodger = [
    "00888800",
    "08FFFF80",
    "8F8888F8",
    "88888888",
    "00F88F00",
    "0F0000F0",
    "F000000F",
    "00000000"
]

charger = [
    "00044000",
    "00444400",
    "044FF440",
    "44FFFF44",
    "44444444",
    "00400400",
    "04000040",
    "40000004"
]

splitter = [
    "00666600",
    "066CC660",
    "66CCCC66",
    "66666666",
    "00666600",
    "06066060",
    "60000006",
    "00000000"
]

sniper = [
    "000BB000",
    "00BBBB00",
    "0BB00BB0",
    "BBBBBBBB",
    "000AA000",
    "000AA000",
    "00A00A00",
    "0A0000A0"
]

shielded = [
    "00BBBB00",
    "0B9999B0",
    "B999999B",
    "B99DD99B",
    "B999999B",
    "0B9999B0",
    "00B99B00",
    "00000000"
]

spawner = [
    "00555500",
    "05HHHH50",
    "5HCCCC H5".replace(" ", ""),
    "5HCCCC H5".replace(" ", ""),
    "05HHHH50",
    "00555500",
    "05000050",
    "50000005"
]

bomber = [
    "00777700",
    "07999970",
    "79944997",
    "79444497",
    "79944997",
    "07999970",
    "00777700",
    "00000000"
]

elite = [
    "00A66A00",
    "0A6CC6A0",
    "A6CCCC6A",
    "66CCCC66",
    "A6CCCC6A",
    "0A6CC6A0",
    "00A66A00",
    "0A0000A0"
]

life_ship = [
    "00200",
    "02220",
    "22222",
    "20202",
    "00200"
]

hit_spark = [
    "00600",
    "60606",
    "06660",
    "60606",
    "00600"
]

shield_sprite = [
    "000BBBBBB000",
    "00B000000B00",
    "0B00000000B0",
    "B0000000000B",
    "B0000000000B",
    "B0000000000B",
    "B0000000000B",
    "B0000000000B",
    "B0000000000B",
    "0B00000000B0",
    "00B000000B00",
    "000BBBBBB000"
]

wasp_boss = [
    "0006600000660000",
    "0066660006666000",
    "0666666066666600",
    "6660066666600666",
    "0666666666666600",
    "0066666666666000",
    "00066CCCC660000",
    "0000066666600000",
    "0000666666660000",
    "0006606006066000",
    "0066000000006600",
    "0660000000000660",
    "6600000000000066",
    "0000006666000000",
    "0000066006600000",
    "0000000000000000"
]

tank_boss = [
    "0099999999999900",
    "0999999999999990",
    "9999009999009999",
    "9999999999999999",
    "9909999999990999",
    "9909999999990999",
    "9999999999999999",
    "0999999999999990",
    "0099999999999900",
    "0009900000099000",
    "0099990009999000",
    "0990099009900990",
    "9900009999000099",
    "9000000990000009",
    "0000000990000000",
    "0000000000000000"
]

ghost_boss = [
    "00000GGGGGG00000",
    "000GGGGGGGGGG000",
    "00GGGGGGGGGGGG00",
    "0GGGGGGGGGGGGGG0",
    "0GGG00GGGG00GGG0",
    "GGG0000GG0000GGG",
    "GGG0000GG0000GGG",
    "GGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGG",
    "GGGG0GGGGGG0GGGG",
    "GGG000GGGG000GGG",
    "GG00000GG00000GG",
    "G00000000000000G",
    "G0G00G00G00G0G0G",
    "0G0G00G00G00G0G0"
]

all_upgrades = [
    # Level 100 mode: many more upgrade caps so upgrades keep appearing.
    ["Player Speed", 0, 6, "Common"],
    ["Bullet Speed", 0, 8, "Common"],
    ["Extra Shot", 0, 5, "Rare"],
    ["Extra Life", 0, 6, "Epic"],
    ["Slower Enemies", 0, 5, "Uncommon"],
    ["Faster Shots", 0, 8, "Rare"],
    ["Bullet Damage", 0, 8, "Rare"],
    ["Max Bullets", 0, 8, "Uncommon"],
    ["Rapid Charge", 0, 8, "Uncommon"],
    ["Longer Laser", 0, 5, "Rare"],
    ["Longer Freeze", 0, 5, "Rare"],
    ["Stronger Bomb", 0, 5, "Rare"]
]

boss_upgrades = [
    ["Laser", 0, 3, "Legendary"],
    ["Shield", 0, 4, "Legendary"],
    ["Bomb", 0, 3, "Legendary"],
    ["Freeze", 0, 3, "Legendary"],
    ["Heal", 0, 4, "Legendary"],
    ["Pulse", 0, 3, "Legendary"],
    ["Missile", 0, 3, "Legendary"],
    ["Overdrive", 0, 3, "Legendary"]
]

def build_levels():
    generated_levels = []

    for lvl in range(1, 101):
        # Boss levels use a placeholder because the boss fight replaces enemies.
        if lvl % 5 == 0:
            generated_levels.append([["basic", 1, 10]])
        else:
            rows = []

            # Basic enemies are always present and keep increasing.
            rows.append(["basic", min(10, 4 + lvl // 2), 10])

            if lvl >= 4:
                rows.append(["fast", min(8, 2 + lvl // 7), 22])
            if lvl >= 8:
                rows.append(["tank", min(7, 2 + lvl // 10), 34])
            if lvl >= 12:
                rows.append(["shooter", min(7, 2 + lvl // 12), 46])

            # New enemy unlocks all the way to level 100.
            if lvl >= 18:
                rows.append(["dodger", min(6, 2 + lvl // 18), 16])
            if lvl >= 25:
                rows.append(["splitter", min(6, 2 + lvl // 20), 28])
            if lvl >= 35:
                rows.append(["sniper", min(5, 1 + lvl // 25), 40])
            if lvl >= 45:
                rows.append(["charger", min(5, 1 + lvl // 22), 52])
            if lvl >= 60:
                rows.append(["shielded", min(5, 1 + lvl // 25), 20])
            if lvl >= 75:
                rows.append(["spawner", min(4, 1 + lvl // 30), 32])
            if lvl >= 85:
                rows.append(["bomber", min(4, 1 + lvl // 35), 44])
            if lvl >= 95:
                rows.append(["elite", min(4, 1 + lvl // 40), 56])

            generated_levels.append(rows)

    return generated_levels

levels = build_levels()

# Boss template:
# [name, sprite, x, y, lives, max_lives, direction, shoot_delay, attack_type]
bosses = [
    ["Wasp", wasp_boss, 72, 10, 20, 20, 1, 30, "triple"],
    ["Tank Boss", tank_boss, 72, 10, 40, 40, 1, 45, "heavy"],
    ["Ghost", ghost_boss, 72, 10, 20, 20, 1, 25, "teleport"],
    ["Hornet", wasp_boss, 72, 10, 28, 28, 1, 24, "triple"],
    ["Crusher", tank_boss, 72, 10, 55, 55, 1, 36, "heavy"],
    ["Phantom", ghost_boss, 72, 10, 32, 32, 1, 20, "teleport"],
    ["Stinger", wasp_boss, 72, 10, 38, 38, 1, 20, "triple"],
    ["Fortress", tank_boss, 72, 10, 75, 75, 1, 30, "heavy"],
    ["Specter", ghost_boss, 72, 10, 45, 45, 1, 17, "teleport"],
    ["Queen", wasp_boss, 72, 10, 60, 60, 1, 16, "triple"],
    ["Dreadnought", tank_boss, 72, 10, 95, 95, 1, 25, "heavy"],
    ["Nightmare", ghost_boss, 72, 10, 60, 60, 1, 14, "teleport"],
    ["War Wasp", wasp_boss, 72, 10, 80, 80, 1, 14, "triple"],
    ["Iron Wall", tank_boss, 72, 10, 120, 120, 1, 22, "heavy"],
    ["Void Ghost", ghost_boss, 72, 10, 80, 80, 1, 12, "teleport"],
    ["Royal Swarm", wasp_boss, 72, 10, 100, 100, 1, 12, "triple"],
    ["Mega Tank", tank_boss, 72, 10, 150, 150, 1, 20, "heavy"],
    ["Final Ghost", ghost_boss, 72, 10, 110, 110, 1, 10, "teleport"],
    ["Hive King", wasp_boss, 72, 10, 130, 130, 1, 10, "triple"],
    ["Pixel Overlord", tank_boss, 72, 10, 180, 180, 1, 8, "heavy"]
]




def make_boss_for_level(bosses, level):
    boss_number = level // 5 - 1
    if boss_number < 0:
        boss_number = 0
    if boss_number >= len(bosses):
        boss_number = len(bosses) - 1
    return make_boss([bosses[boss_number]])

def harden_boss(boss, level):
    # Bosses get more health and shoot faster as levels go up.
    extra_lives = level * 2
    boss[4] = boss[4] + extra_lives
    boss[5] = boss[5] + extra_lives
    boss[7] = max(8, boss[7] - level)
    return boss



def rects_overlap(ax, ay, aw, ah, bx, by, bw, bh):
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by


def get_player_top_limit(enemies, boss_fight, boss):
    # This lets the player dodge vertically, but not fly behind enemy rows.
    top_limit = PLAYER_BASE_MIN_Y

    if enemies:
        lowest_enemy_y = 0
        for enemy in enemies:
            if enemy[1] > lowest_enemy_y:
                lowest_enemy_y = enemy[1]
        # Enemy sprites are 8 pixels tall. y + 8 means the player
        # is stopped directly under the enemy, not far below it.
        top_limit = max(top_limit, lowest_enemy_y + 8)

    if boss_fight and boss != None:
        # Boss sprites are 16 pixels tall, so stop directly below boss.
        top_limit = max(40, boss[3] + 16)

    if top_limit > SCREEN_H - 10:
        top_limit = SCREEN_H - 10

    return top_limit

def load_highscore():
    try:
        with open("pixel_swarm_highscore.txt", "r") as file:
            return int(file.read())
    except:
        return None

def save_highscore(score):
    with open("pixel_swarm_highscore.txt", "w") as file:
        file.write(str(score))

class ButtonAdapter:
    def __init__(self, press_func):
        self.press_func = press_func

    def value(self):
        # Old Pixel Swarm code expects active-low Pin objects:
        # 0 = pressed, 1 = not pressed.
        if self.press_func():
            return 0
        return 1

def wait_for_release(button):
    while button.value() == 0:
        time.sleep(0.01)

def swarm_info():
    oled.fill(BLACK)
    center_text_x(oled, "JOYSTICK MOVE", 8, WHITE, SCREEN_W)
    center_text_x(oled, "GREEN START", 24, GREEN, SCREEN_W)
    center_text_x(oled, "GREEN SPECIAL", 40, GREEN, SCREEN_W)
    center_text_x(oled, "YELLOW BACK", 56, WHITE, SCREEN_W)
    show_display(oled)
    while True:
        if button_Y.value() == 0:
            wait_for_release(button_Y)
            return
        time.sleep(0.05)


def main(oled_from_launcher, controls, settings):
    global oled, button_Y, button_G, button_B, button_R, highscore

    # Use the screen and controls from PixelForge OS.
    oled = oled_from_launcher

    # Keep the old .value() button style working.
    button_Y = ButtonAdapter(controls["yellow"])
    button_G = ButtonAdapter(controls["green"])
    button_B = ButtonAdapter(controls["blue"])
    button_R = ButtonAdapter(controls["red"])

    highscore = load_highscore()
    while True:
        while True:
            oled.fill(SPACE_BLACK)
            center_text_x(oled, "PIXEL SWARM", 8, CYAN, SCREEN_W)
            center_text_x(oled, "GREEN START", 28, GREEN, SCREEN_W)
            center_text_x(oled, "YELLOW INFO", 46, YELLOW, SCREEN_W)
            center_text_x(oled, "RED EXIT", 60, RED, SCREEN_W)
            show_display(oled)
            if button_Y.value() == 0:
                wait_for_release(button_Y)
                swarm_info()
            if button_R.value() == 0:
                return
            if button_G.value() == 0:
                wait_for_release(button_G)
                break
            time.sleep(0.05)

        transition(oled, 1)
        transition(oled, 0)

        enemy_direction = 1
        start_time = time.ticks_ms()
        level = 1
        enemies = make_level(oled, levels, level, SCREEN_W)
        player_speed = 2
        enemy_move_delay = 1
        enemy_move_timer = 0
        enemy_drop_timer = 0
        shot_count = 1
        bullet_speed = 2
        bullet_damage = 1
        max_player_bullets = MAX_PLAYER_BULLETS
        laser_bonus = 0
        freeze_bonus = 0
        bomb_bonus = 0
        overdrive_timer = 0
        shoot_delay = 14
        shoot_timer = 0
        boss_fight = False
        boss = None
        special_ability = None
        special_ready = True
        special_cooldown = 0
        special_cooldown_max = 45
        special_last_second = time.ticks_ms()
        shield = 0
        laser_timer = 0
        freeze_timer = 0
        was_a_boss_fight = False
        bullets = []
        enemy_bullets = []
        lives = 3
        player_x = 76
        player_y = 8
        score = 0
        invincible = 0

        while True:
            oled.text("*", player_x, player_y, )
            show_display(oled)


