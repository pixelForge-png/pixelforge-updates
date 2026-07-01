from machine import Pin, SPI, ADC
from st7735_fb import ST7735FB
import time
import random
from buzzer_sounds import sound
from helpers.oled_functions_test import (
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
# Screen setup
# -----------------------------
# Change these pins if your screen is wired differently.
SPI_ID = 0
SCK_PIN = 18
MOSI_PIN = 19
CS_PIN = 17
DC_PIN = 21
RST_PIN = 20
BLK_PIN = None

SCREEN_W = 160
SCREEN_H = 80

MAX_PLAYER_BULLETS = 10
MAX_ENEMY_BULLETS = 16

# Player can move in both X and Y, but cannot fly behind enemy rows.
PLAYER_BASE_MIN_Y = 0

spi = SPI(SPI_ID, baudrate=40000000, polarity=0, phase=0, sck=Pin(SCK_PIN), mosi=Pin(MOSI_PIN))
if BLK_PIN is not None:
    backlight = Pin(BLK_PIN, Pin.OUT)
    backlight.value(1)

oled = ST7735FB(spi=spi, cs=Pin(CS_PIN, Pin.OUT), dc=Pin(DC_PIN, Pin.OUT), rst=Pin(RST_PIN, Pin.OUT), width=SCREEN_W, height=SCREEN_H, xstart=0, ystart=24, invert=False)

# -----------------------------
# Joystick and button setup
# -----------------------------
# X and Y must be ADC pins: GP26, GP27, or GP28.
JOY_X = ADC(27)
JOY_Y = ADC(26)

# Four color buttons, active-low with PULL_UP.
# Physical positions while holding the console:
# Yellow = top, Green = bottom, Blue = left, Red = right.
button_Y = Pin(4, Pin.IN, Pin.PULL_UP)
button_G = Pin(3, Pin.IN, Pin.PULL_UP)
button_B = Pin(5, Pin.IN, Pin.PULL_UP)
button_R = Pin(2, Pin.IN, Pin.PULL_UP)

PLAYER_BULLET_PALETTE = {"0": None, "1": PLAYER_BULLET}
ENEMY_BULLET_PALETTE = {"0": None, "4": ENEMY_BULLET}

# -----------------------------
# Color sprites
# 0 = transparent. Other characters use GAME_PALETTE.
# -----------------------------
player = [
    "00022000",
    "00022000",
    "00222200",
    "00211200",
    "02211220",
    "22222222",
    "00100100",
    "02000020"
]

bullet = [
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

highscore = load_highscore()
def main(oled, controls, settings):
    while True:
        while True:
            oled.fill(SPACE_BLACK)
            center_text_x(oled, "PIXEL SWARM", 8, CYAN, SCREEN_W)
            center_text_x(oled, "GREEN START", 36, GREEN, SCREEN_W)
            center_text_x(oled, "YELLOW INFO", 54, YELLOW, SCREEN_W)
            show_display(oled)
            if button_Y.value() == 0:
                wait_for_release(button_Y)
                swarm_info()
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
        player_y = 70
        score = 0
        invincible = 0
    
        while True:
            if freeze_timer > 0:
                freeze_timer -= 1
            new_enemy_bullets = []
    
            if lives <= 0:
                oled.fill(BLACK)
                live_time = time.ticks_diff(time.ticks_ms(), start_time) // 1000
                center_text_x(oled, "YOU LOST", 8, RED, SCREEN_W)
                center_text_x(oled, "SCORE " + str(score), 26, WHITE, SCREEN_W)
                center_text_x(oled, str(live_time) + " SECONDS", 42, CYAN, SCREEN_W)
                if highscore is None or score > highscore:
                    highscore = score
                    save_highscore(highscore)
                    center_text_x(oled, "NEW HIGH SCORE", 58, YELLOW, SCREEN_W)
                else:
                    center_text_x(oled, "BEST " + str(highscore), 58, YELLOW, SCREEN_W)
                show_display(oled)
                time.sleep(5)
                break
    
            if enemies == [] and boss_fight == False:
                level += 1
                if level > len(levels):
                    level = len(levels)
                oled.fill(BLACK)
                center_text_x(oled, "LEVEL " + str(level), 28, YELLOW, SCREEN_W)
                show_display(oled)
                time.sleep(1)
                if level % 5 == 0:
                    boss_fight = True
                    boss = harden_boss(make_boss_for_level(bosses, level), level)
                    enemies = []
                else:
                    boss_fight = False
                    enemies = make_level(oled, levels, level, SCREEN_W)
                    if was_a_boss_fight != True and level % 2 == 0:
                        player_choice = upgrades(oled, all_upgrades, button_B, button_G, button_R, button_Y)
                        if player_choice != None:
                            if player_choice[0] == "Player Speed":
                                player_speed += 1
                            elif player_choice[0] == "Bullet Speed":
                                bullet_speed += 1
                            elif player_choice[0] == "Extra Shot":
                                shot_count += 1
                            elif player_choice[0] == "Extra Life":
                                lives += 1
                            elif player_choice[0] == "Slower Enemies":
                                enemy_move_delay += 1
                            elif player_choice[0] == "Faster Shots":
                                if shoot_delay > 5:
                                    shoot_delay -= 1
                            elif player_choice[0] == "Bullet Damage":
                                bullet_damage += 1
                            elif player_choice[0] == "Max Bullets":
                                max_player_bullets += 2
                            elif player_choice[0] == "Rapid Charge":
                                if special_cooldown_max > 15:
                                    special_cooldown_max -= 5
                            elif player_choice[0] == "Longer Laser":
                                laser_bonus += 5
                            elif player_choice[0] == "Longer Freeze":
                                freeze_bonus += 10
                            elif player_choice[0] == "Stronger Bomb":
                                bomb_bonus += 2
                    was_a_boss_fight = False
                bullets = []
                enemy_bullets = []
    
            # Joystick movement: X and Y movement.
            # The top limit stops the player from getting behind enemy rows.
            left, right, up, down, raw_x, raw_y = joystick_direction(JOY_X, JOY_Y)
            player_top_limit = get_player_top_limit(enemies, boss_fight, boss)
    
            if left and player_x > 0:
                player_x -= player_speed
            elif right and player_x < SCREEN_W - 8:
                player_x += player_speed
    
            if up and player_y > player_top_limit:
                player_y -= player_speed
            elif down and player_y < SCREEN_H - 8:
                player_y += player_speed
    
            if player_y < player_top_limit:
                player_y = player_top_limit
    
            # Auto shoot
            if overdrive_timer > 0:
                overdrive_timer -= 1
                current_shoot_delay = max(3, shoot_delay // 2)
            else:
                current_shoot_delay = shoot_delay
    
            shoot_timer += 1
            if shoot_timer >= current_shoot_delay:
                shoot_timer = 0
                center_x = player_x + 3
                for i in range(shot_count):
                    if len(bullets) >= max_player_bullets:
                        break
                    offset = int((i - (shot_count - 1) / 2) * 4)
                    bullets.append([center_x + offset, player_y - 3])
    
            # Special ability with joystick press
            if button_G.value() == 0 and special_ready == True and special_ability != None:
                if special_ability == "Laser":
                    laser_timer = 12 + laser_bonus
                elif special_ability == "Shield":
                    shield = 1
                elif special_ability == "Bomb":
                    enemies = []
                    if boss_fight and boss != None:
                        boss[4] -= 3 + bomb_bonus
                    oled.fill(BOMB_COLOR)
                    show_display(oled)
                    time.sleep(0.25)
                elif special_ability == "Freeze":
                    freeze_timer = 50 + freeze_bonus
                elif special_ability == "Heal":
                    lives += 1
                elif special_ability == "Pulse":
                    enemy_bullets = []
                    for enemy in enemies:
                        enemy[2] -= 1 + bullet_damage // 2
                    if boss_fight and boss != None:
                        boss[4] -= 2 + bullet_damage
                elif special_ability == "Missile":
                    if boss_fight and boss != None:
                        boss[4] -= 8 + bullet_damage * 2
                    elif enemies:
                        target_enemy = enemies[0]
                        for enemy in enemies:
                            if enemy[1] > target_enemy[1]:
                                target_enemy = enemy
                        target_enemy[2] = 0
                elif special_ability == "Overdrive":
                    overdrive_timer = 100
                special_ready = False
                special_cooldown = special_cooldown_max
                special_last_second = time.ticks_ms()
                wait_for_release(button_G)
    
            # Cooldown once per second
            if special_ready == False:
                now = time.ticks_ms()
                if time.ticks_diff(now, special_last_second) >= 1000:
                    special_last_second = now
                    special_cooldown -= 1
                    if special_cooldown <= 0:
                        special_cooldown = 0
                        special_ready = True
    
            oled.fill(SPACE_BLACK)
    
            # Boss
            if boss_fight == True:
                boss, bullets = update_boss(oled, boss, bullets, bullet_speed, freeze_timer, GAME_PALETTE, bullet_damage)
                if boss != None:
                    boss_lives = boss[4]
                    boss_max_lives = boss[5]
                    oled.rect(25, 0, 110, 6, WHITE)
                    health_width = int((boss_lives / boss_max_lives) * 108)
                    if health_width < 0:
                        health_width = 0
                    oled.fill_rect(26, 1, health_width, 4, HEALTH_GREEN)
                    for b in bullets:
                        draw_color_sprite(oled, bullet, b[0], b[1], PLAYER_BULLET_PALETTE)
                    if freeze_timer <= 0:
                        boss[9] += 1
                        if boss[9] >= boss[7]:
                            boss[9] = 0
                            enemy_bullets = boss_attack(enemy_bullets, boss, player_x + 4, player_y + 4, 2 + level // 8)
                if boss == None:
                    boss_fight = False
                    was_a_boss_fight = True
                    bullets = []
                    enemy_bullets = []
                    score += 250
                    oled.fill(BLACK)
                    center_text_x(oled, "BOSS DEFEATED", 25, YELLOW, SCREEN_W)
                    show_display(oled)
                    time.sleep(1)
                    boss_choice = upgrades(oled, boss_upgrades, button_B, button_G, button_R, button_Y)
                    if boss_choice != None:
                        special_ability = boss_choice[0]
                        special_ready = True
                        special_cooldown = 0
    
            # Shield and player
            if shield > 0:
                shield_x = player_x - 2
                if shield_x < 0:
                    shield_x = 0
                elif shield_x > SCREEN_W - 12:
                    shield_x = SCREEN_W - 12
                draw_color_sprite(oled, shield_sprite, shield_x, player_y - 2, GAME_PALETTE)
            draw_color_sprite(oled, player, player_x, player_y, GAME_PALETTE)
    
            # UI
            for i in range(lives):
                draw_color_sprite(oled, life_ship, i * 8, 0, GAME_PALETTE)
            draw_tiny_text(oled, str(score), 40, 0, WHITE)
            if special_ability != None:
                draw_special_icon(oled, special_ability)
                if special_ready:
                    draw_tiny_text(oled, "R", 140, 10, GREEN)
                else:
                    draw_tiny_text(oled, str(special_cooldown), 136, 10, YELLOW)
    
            # Laser
            if laser_timer > 0:
                oled.fill_rect(player_x + 3, 0, 2, player_y, LASER_COLOR)
                laser_timer -= 1
                new_enemies = []
                for enemy in enemies:
                    if player_x + 3 < enemy[0] + 8 and player_x + 5 > enemy[0]:
                        enemy[2] -= 1
                    if enemy[2] > 0:
                        new_enemies.append(enemy)
                    else:
                        score += 10
                enemies = new_enemies
                if boss_fight and boss != None:
                    if player_x + 3 < boss[2] + 16 and player_x + 5 > boss[2]:
                        boss[4] -= 1
    
            # Player bullets against normal enemies
            new_bullets = []
            if boss_fight == False:
                for b in bullets:
                    b[1] -= bullet_speed
                    enemies, bullet_hit, hit_x, hit_y, points_gained, death_shots = update_enimies(enemies, b[0], b[1], bullet_damage)
                    score += points_gained
                    for shot in death_shots:
                        if len(enemy_bullets) < MAX_ENEMY_BULLETS:
                            enemy_bullets.append(make_aimed_enemy_bullet(shot[0], shot[1], player_x + 4, player_y + 4, 2 + level // 10))
                        if len(enemy_bullets) < MAX_ENEMY_BULLETS:
                            enemy_bullets.append(make_aimed_enemy_bullet(shot[0] + 4, shot[1], player_x + 4, player_y + 4, 2 + level // 10))
                    if b[1] > -3 and bullet_hit == False:
                        new_bullets.append(b)
                    elif bullet_hit == True:
                        draw_color_sprite(oled, hit_spark, hit_x + 2, hit_y + 2, GAME_PALETTE)
                bullets = new_bullets
                for b in bullets:
                    draw_color_sprite(oled, bullet, b[0], b[1], PLAYER_BULLET_PALETTE)
    
            # Enemy movement
            turn_around = False
            enemy_move_timer += 1
            if enemy_move_timer >= enemy_move_delay:
                enemy_move_timer = 0
                for enemy in enemies:
                    if enemy[0] <= 0 or enemy[0] >= SCREEN_W - 8:
                        turn_around = True
                if turn_around:
                    enemy_direction *= -1
                if freeze_timer <= 0:
                    enemy_speed_bonus = level // 6
                    for enemy in enemies:
                        if enemy[3] == "fast":
                            enemy[0] += enemy_direction * (2 + enemy_speed_bonus)
                        elif enemy[3] == "dodger":
                            enemy[0] += enemy_direction * (3 + enemy_speed_bonus)
                            if random.randint(0, 8) == 0:
                                enemy[0] += random.choice([-3, 3])
                        elif enemy[3] == "charger":
                            enemy[0] += enemy_direction * (1 + enemy_speed_bonus)
                            enemy[1] += 1
                        elif enemy[3] == "elite":
                            enemy[0] += enemy_direction * (2 + enemy_speed_bonus)
                        else:
                            enemy[0] += enemy_direction * (1 + enemy_speed_bonus)
    
                        if enemy[0] < 0:
                            enemy[0] = 0
                        elif enemy[0] > SCREEN_W - 8:
                            enemy[0] = SCREEN_W - 8
    
                    # Slow downward pressure. As level rises, enemies drop more often.
                    enemy_drop_timer += 1
                    enemy_drop_delay = max(18, 55 - level * 2)
                    if enemy_drop_timer >= enemy_drop_delay:
                        enemy_drop_timer = 0
                        for enemy in enemies:
                            enemy[1] += 1
    
            # Spawners occasionally create extra basic enemies.
            spawned_enemies = []
            if freeze_timer <= 0 and len(enemies) < 28:
                spawn_chance = max(25, 120 - level)
                for enemy in enemies:
                    if enemy[3] == "spawner" and random.randint(0, spawn_chance) == 0:
                        spawn_y = enemy[1] + 10
                        if spawn_y < SCREEN_H - 12:
                            spawned_enemies.append([enemy[0], spawn_y, 1, "basic"])
            for enemy in spawned_enemies:
                enemies.append(enemy)
    
            # Enemy contact damage. If enemies reach the player, they hurt you.
            if invincible <= 0:
                for enemy in enemies:
                    if rects_overlap(enemy[0], enemy[1], 8, 8, player_x, player_y, 8, 8):
                        if shield > 0:
                            shield -= 1
                        else:
                            lives -= 1
                            sound(220, 9000, 0.02)
                        invincible = 25
                        break
    
            # Draw enemies
            for enemy in enemies:
                if enemy[3] == "basic":
                    draw_color_sprite(oled, basic, enemy[0], enemy[1], GAME_PALETTE)
                elif enemy[3] == "tank":
                    draw_color_sprite(oled, tank, enemy[0], enemy[1], GAME_PALETTE)
                elif enemy[3] == "shooter":
                    draw_color_sprite(oled, shooter, enemy[0], enemy[1], GAME_PALETTE)
                elif enemy[3] == "fast":
                    draw_color_sprite(oled, fast_enemy, enemy[0], enemy[1], GAME_PALETTE)
                elif enemy[3] == "dodger":
                    draw_color_sprite(oled, dodger, enemy[0], enemy[1], GAME_PALETTE)
                elif enemy[3] == "splitter":
                    draw_color_sprite(oled, splitter, enemy[0], enemy[1], GAME_PALETTE)
                elif enemy[3] == "sniper":
                    draw_color_sprite(oled, sniper, enemy[0], enemy[1], GAME_PALETTE)
                elif enemy[3] == "charger":
                    draw_color_sprite(oled, charger, enemy[0], enemy[1], GAME_PALETTE)
                elif enemy[3] == "shielded":
                    draw_color_sprite(oled, shielded, enemy[0], enemy[1], GAME_PALETTE)
                elif enemy[3] == "spawner":
                    draw_color_sprite(oled, spawner, enemy[0], enemy[1], GAME_PALETTE)
                elif enemy[3] == "bomber":
                    draw_color_sprite(oled, bomber, enemy[0], enemy[1], GAME_PALETTE)
                elif enemy[3] == "elite":
                    draw_color_sprite(oled, elite, enemy[0], enemy[1], GAME_PALETTE)
    
            # Enemy shooting and bullets
            if freeze_timer <= 0:
                if enemies:
                    the_chosen_one = random.choice(enemies)
                    if the_chosen_one[3] == "basic":
                        shoot_chance = 16
                        enemy_bullet_speed = 2 + level // 10
                    elif the_chosen_one[3] == "tank":
                        shoot_chance = 24
                        enemy_bullet_speed = 2 + level // 12
                    elif the_chosen_one[3] == "shooter":
                        shoot_chance = 6
                        enemy_bullet_speed = 2 + level // 10
                    elif the_chosen_one[3] == "fast":
                        shoot_chance = 12
                        enemy_bullet_speed = 2 + level // 10
                    elif the_chosen_one[3] == "dodger":
                        shoot_chance = 13
                        enemy_bullet_speed = 2 + level // 10
                    elif the_chosen_one[3] == "splitter":
                        shoot_chance = 14
                        enemy_bullet_speed = 2 + level // 10
                    elif the_chosen_one[3] == "sniper":
                        shoot_chance = 4
                        enemy_bullet_speed = 3 + level // 10
                    elif the_chosen_one[3] == "charger":
                        shoot_chance = 16
                        enemy_bullet_speed = 2 + level // 12
                    elif the_chosen_one[3] == "shielded":
                        shoot_chance = 18
                        enemy_bullet_speed = 2 + level // 12
                    elif the_chosen_one[3] == "spawner":
                        shoot_chance = 20
                        enemy_bullet_speed = 2 + level // 12
                    elif the_chosen_one[3] == "bomber":
                        shoot_chance = 10
                        enemy_bullet_speed = 2 + level // 10
                    elif the_chosen_one[3] == "elite":
                        shoot_chance = 5
                        enemy_bullet_speed = 3 + level // 9
                    else:
                        shoot_chance = 16
                        enemy_bullet_speed = 2 + level // 10
    
                    # Lower shoot_chance means enemies shoot more often.
                    shoot_chance = max(3, shoot_chance - level // 2)
    
                    if random.randint(0, shoot_chance) == 0 and len(enemy_bullets) < MAX_ENEMY_BULLETS:
                        if the_chosen_one[3] == "bomber":
                            for offset in [-4, 0, 4]:
                                if len(enemy_bullets) < MAX_ENEMY_BULLETS:
                                    enemy_bullets.append(make_aimed_enemy_bullet(the_chosen_one[0] + 3 + offset, the_chosen_one[1] + 8, player_x + 4, player_y + 4, enemy_bullet_speed))
                        else:
                            enemy_bullets.append(make_aimed_enemy_bullet(the_chosen_one[0] + 3, the_chosen_one[1] + 8, player_x + 4, player_y + 4, enemy_bullet_speed))
                for eb in enemy_bullets:
                    eb[0] += eb[2]
                    eb[1] += eb[3]
                    eb_x = bullet_screen_x(eb)
                    eb_y = bullet_screen_y(eb)
    
                    if eb_x < player_x + 8 and eb_x + 2 > player_x and eb_y < player_y + 8 and eb_y + 3 > player_y and invincible <= 0:
                        if shield > 0:
                            shield -= 1
                        else:
                            lives -= 1
                            sound(220, 9000, 0.02)
                        invincible = 20
                    else:
                        if eb_x > -4 and eb_x < SCREEN_W and eb_y > -4 and eb_y < SCREEN_H:
                            draw_color_sprite(oled, enemy_bullet_sprite, eb_x, eb_y, ENEMY_BULLET_PALETTE)
                            new_enemy_bullets.append(eb)
                enemy_bullets = new_enemy_bullets
    
            if invincible > 0:
                invincible -= 1
            show_display(oled)


