import time
import os
import gc
from machine import Pin, SPI, ADC
from st7735_fb import ST7735FB

import settings_manager
import update_manager
import keyboard

SCK_PIN = 18
MOSI_PIN = 19
CS_PIN = 17
DC_PIN = 21
RST_PIN = 20

SCREEN_W = 160
SCREEN_H = 80

JOY_X = ADC(27)
JOY_Y = ADC(26)

button_Y = Pin(4, Pin.IN, Pin.PULL_UP)
button_G = Pin(3, Pin.IN, Pin.PULL_UP)
button_B = Pin(5, Pin.IN, Pin.PULL_UP)
button_R = Pin(2, Pin.IN, Pin.PULL_UP)

def color565(r, g, b):
    c = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return ((c & 0xFF) << 8) | (c >> 8)

BLACK = color565(0, 0, 0)
WHITE = color565(255, 255, 255)
CYAN = color565(0, 255, 255)
GREEN = color565(0, 255, 0)
YELLOW = color565(255, 255, 0)
RED = color565(255, 0, 0)
GRAY = color565(100, 100, 100)

spi = SPI(
    0,
    baudrate=40000000,
    polarity=0,
    phase=0,
    sck=Pin(SCK_PIN),
    mosi=Pin(MOSI_PIN)
)

oled = ST7735FB(
    spi=spi,
    cs=Pin(CS_PIN, Pin.OUT),
    dc=Pin(DC_PIN, Pin.OUT),
    rst=Pin(RST_PIN, Pin.OUT),
    width=SCREEN_W,
    height=SCREEN_H,
    xstart=0,
    ystart=24,
    invert=False,
    bgr=True
)

def pressed(pin):
    return pin.value() == 0

def green_pressed():
    return pressed(button_G)

def yellow_pressed():
    return pressed(button_Y)

def blue_pressed():
    return pressed(button_B)

def red_pressed():
    return pressed(button_R)

def joystick_direction():
    settings = settings_manager.load_settings()
    joystick_mode = settings.get("joystick_mode", "normal")

    x = JOY_X.read_u16()
    y = JOY_Y.read_u16()

    raw_left = x > 52000
    raw_right = x < 12000
    raw_up = y < 12000
    raw_down = y > 52000

    if joystick_mode == "normal":
        left = raw_left
        right = raw_right
        up = raw_up
        down = raw_down

    elif joystick_mode == "rotated_left":
        # Fixes:
        # physical right reading as up
        # physical up reading as right
        # physical down reading as left
        # physical left reading as down
        left = raw_down
        right = raw_up
        up = raw_right
        down = raw_left

    elif joystick_mode == "rotated_right":
        left = raw_up
        right = raw_down
        up = raw_left
        down = raw_right

    elif joystick_mode == "upside_down":
        left = raw_right
        right = raw_left
        up = raw_down
        down = raw_up

    else:
        left = raw_left
        right = raw_right
        up = raw_up
        down = raw_down

    return left, right, up, down

controls = {
    "green": green_pressed,
    "yellow": yellow_pressed,
    "blue": blue_pressed,
    "red": red_pressed,
    "joystick": joystick_direction
}

def wait_release():
    while green_pressed() or yellow_pressed() or blue_pressed() or red_pressed():
        time.sleep(0.02)

def center_text(text, y, color=WHITE):
    text = str(text)
    x = (SCREEN_W - len(text) * 8) // 2
    oled.text(text, x, y, color)

def screen_status(title, line1="", line2="", color=WHITE):
    oled.fill(BLACK)
    center_text(title, 8, color)
    center_text(line1, 32, WHITE)
    center_text(line2, 52, CYAN)
    oled.show()

def ensure_folders():
    for folder in ["/games", "/data", "/helpers"]:
        try:
            os.mkdir(folder)
        except OSError:
            pass

def make_title(game_id):
    parts = game_id.split("_")
    title_parts = []

    for part in parts:
        if len(part) > 0:
            title_parts.append(part[0].upper() + part[1:])

    return " ".join(title_parts)

def list_local_games(include_dev=False):
    ensure_folders()

    game_info = settings_manager.load_game_info()
    settings = settings_manager.load_settings()
    dev_mode = settings.get("dev_mode", False)

    games = []

    try:
        files = os.listdir("/games")
    except:
        files = []

    for filename in files:
        if filename.endswith(".py") and filename != "__init__.py":
            game_id = filename[:-3]
            title = make_title(game_id)
            info = game_info.get(game_id, {})

            channel = info.get("channel", "release")
            is_dev_game = (
                game_id.startswith("test") or
                game_id.startswith("dev") or
                channel == "dev"
            )

            if is_dev_game and not include_dev:
                continue

            if is_dev_game and not dev_mode:
                continue

            games.append({
                "id": game_id,
                "title": info.get("title", title),
                "display_version": info.get("display_version", "?"),
                "file": "games/" + filename,
                "module": "games." + game_id,
                "version": 0
            })

    return games

def run_game(game):
    oled.fill(BLACK)
    center_text("LOADING 1", 20, YELLOW)
    center_text("IMPORTING", 40, WHITE)
    oled.show()
    time.sleep(0.5)

    try:
        module_name = game["module"]

        try:
            import sys
            if module_name in sys.modules:
                del sys.modules[module_name]
        except:
            pass

        gc.collect()

        game_module = __import__(module_name, None, None, ["main"])

        oled.fill(BLACK)
        center_text("LOADING 2", 20, YELLOW)
        center_text("STARTING", 40, WHITE)
        oled.show()
        time.sleep(0.5)

        if hasattr(game_module, "main"):
            game_module.main(oled, controls, settings_manager.load_settings())
        else:
            screen_status("GAME ERROR", "NO main()", game["title"][:16], RED)
            time.sleep(2)

    except Exception as e:
        screen_status("GAME ERROR", str(e)[:16], game["title"][:16], RED)
        time.sleep(3)

def list_test_games():
    games = list_local_games(include_dev=True)
    test_games = []

    for game in games:
        if game["id"].startswith("test") or game["id"].startswith("dev"):
            test_games.append(game)

    return test_games

def test_games_menu():
    games = list_test_games()
    index = 0
    last_move = time.ticks_ms()

    while True:
        oled.fill(BLACK)
        center_text("TEST GAMES", 4, CYAN)

        if len(games) == 0:
            center_text("NO TEST GAMES", 30, RED)
            center_text("YELLOW BACK", 50, WHITE)
        else:
            oled.text("<", 3, 36, YELLOW)
            oled.text(">", 150, 36, YELLOW)
            center_text(games[index]["title"][:18], 24, WHITE)
            center_text("v" + games[index].get("display_version", "?"), 40, CYAN)
            center_text("GREEN TO PLAY", 58, GREEN)

        oled.show()

        left, right, up, down = joystick_direction()
        now = time.ticks_ms()

        if len(games) > 0 and time.ticks_diff(now, last_move) > 220:
            if left:
                index -= 1
                if index < 0:
                    index = len(games) - 1
                last_move = now

            elif right:
                index += 1
                if index >= len(games):
                    index = 0
                last_move = now

        if green_pressed() and len(games) > 0:
            wait_release()
            run_game(games[index])

        if yellow_pressed():
            wait_release()
            return

        time.sleep(0.03)

def settings_menu():
    settings = settings_manager.load_settings()

    items = [
        "Username",
        "WiFi Name",
        "WiFi Pass",
        "Update Now",
        "Test Games",
        "Back"
    ]

    index = 0
    last_move = time.ticks_ms()

    while True:
        oled.fill(BLACK)
        center_text("SETTINGS", 2, CYAN)

        for i in range(len(items)):
            y = 15 + i * 11

            if i == index:
                oled.text(">", 8, y, YELLOW)
                color = YELLOW
            else:
                color = WHITE

            oled.text(items[i], 22, y, color)

        oled.show()

        left, right, up, down = joystick_direction()
        now = time.ticks_ms()

        if time.ticks_diff(now, last_move) > 180:
            if up:
                index -= 1
                if index < 0:
                    index = len(items) - 1
                last_move = now

            elif down:
                index += 1
                if index >= len(items):
                    index = 0
                last_move = now

        if green_pressed():
            wait_release()

            if items[index] == "Username":
                settings["username"] = keyboard.type_text(
                    oled,
                    controls,
                    "USERNAME",
                    settings.get("username", "")
                )
                settings_manager.save_settings(settings)

            elif items[index] == "WiFi Name":
                settings["wifi_ssid"] = keyboard.type_text(
                    oled,
                    controls,
                    "WIFI NAME",
                    settings.get("wifi_ssid", "")
                )
                settings_manager.save_settings(settings)

            elif items[index] == "WiFi Pass":
                settings["wifi_password"] = keyboard.type_text(
                    oled,
                    controls,
                    "WIFI PASS",
                    settings.get("wifi_password", "")
                )
                settings_manager.save_settings(settings)

            elif items[index] == "Update Now":
                connected = update_manager.connect_wifi(
                    settings.get("wifi_ssid", ""),
                    settings.get("wifi_password", ""),
                    oled,
                    screen_status
                )

                if connected:
                    update_manager.check_for_updates(screen_status)
                else:
                    screen_status("NO WIFI", "CHECK", "SETTINGS", RED)
                    time.sleep(2)

            elif items[index] == "Test Games":
                if settings.get("dev_mode", False):
                    test_games_menu()
                else:
                    screen_status("LOCKED", "DEV ONLY", "", RED)
                    time.sleep(2)

            elif items[index] == "Back":
                return

        if yellow_pressed():
            wait_release()
            return

        time.sleep(0.03)

def draw_home(games, index):
    oled.fill(BLACK)
    center_text("PixelForge OS", 3, CYAN)

    oled.text("<", 3, 36, YELLOW)
    oled.text(">", 150, 36, YELLOW)

    if len(games) == 0:
        center_text("NO GAMES", 30, RED)
        center_text("GO SETTINGS", 48, WHITE)
    else:
        game = games[index]
        center_text(game["title"][:18], 24, WHITE)
        center_text("v" + game.get("display_version", "?"), 40, CYAN)
        center_text("GREEN TO PLAY", 58, GREEN)

    oled.text("Y=Settings", 2, 70, GRAY)
    oled.show()

def home_screen():
    settings = settings_manager.load_settings()

    if settings.get("auto_update", True):
        if settings.get("wifi_ssid", "") != "":
            connected = update_manager.connect_wifi(
                settings.get("wifi_ssid", ""),
                settings.get("wifi_password", ""),
                oled,
                screen_status
            )

            if connected:
                update_manager.check_for_updates(screen_status)

    games = list_local_games()
    index = 0
    last_move = time.ticks_ms()

    while True:
        games = list_local_games()

        if len(games) > 0:
            if index >= len(games):
                index = 0

        draw_home(games, index)

        left, right, up, down = joystick_direction()
        now = time.ticks_ms()

        if len(games) > 0 and time.ticks_diff(now, last_move) > 220:
            if left:
                index -= 1
                if index < 0:
                    index = len(games) - 1
                last_move = now

            elif right:
                index += 1
                if index >= len(games):
                    index = 0
                last_move = now

        if green_pressed():
            wait_release()

            if len(games) > 0:
                run_game(games[index])

        if yellow_pressed():
            wait_release()
            settings_menu()

        time.sleep(0.03)

ensure_folders()

screen_status("PIXELFORGE", "BOOTING", "OS", CYAN)
time.sleep(1)

home_screen()
