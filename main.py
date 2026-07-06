import time
import os
import gc
from machine import Pin, SPI, ADC
from st7735_fb import ST7735FB

import settings_manager
import update_manager
import keyboard

try:
    from helpers import online_relay
except:
    online_relay = None

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

def list_local_games(include_dev=False, mode="singleplayer", mp_mode=None):
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

            game_mode = info.get("mode", "singleplayer")

            if game_mode != mode:
                continue

            if mode == "multiplayer" and mp_mode != None:
                network = info.get("network", "local")
            
                if mp_mode == "online" and network != "online":
                    continue
            
                # Local shows both local-only games and online-capable games.
                # So no filter is needed for mp_mode == "local".

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
                "mode": game_mode,
                "network": info.get("network", "local"),
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

def simple_menu(title, items):
    index = 0
    last_move = time.ticks_ms()

    while True:
        oled.fill(BLACK)
        center_text(title, 2, CYAN)

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
            return items[index]

        if yellow_pressed():
            wait_release()
            return "Back"

        time.sleep(0.03)

def wifi_settings_menu():
    while True:
        settings = settings_manager.load_settings()

        choice = simple_menu("WIFI", [
            "WiFi Name",
            "WiFi Pass",
            "Connect",
            "Back"
        ])

        if choice == "WiFi Name":
            settings["wifi_ssid"] = keyboard.type_text(
                oled,
                controls,
                "WIFI NAME",
                settings.get("wifi_ssid", "")
            )
            settings_manager.save_settings(settings)

        elif choice == "WiFi Pass":
            settings["wifi_password"] = keyboard.type_text(
                oled,
                controls,
                "WIFI PASS",
                settings.get("wifi_password", "")
            )
            settings_manager.save_settings(settings)

        elif choice == "Connect":
            connected = update_manager.connect_wifi(
                settings.get("wifi_ssid", ""),
                settings.get("wifi_password", ""),
                oled,
                screen_status
            )

            if connected:
                screen_status("WIFI", "CONNECTED", "OK", GREEN)
                time.sleep(1)
            else:
                screen_status("WIFI", "FAILED", "CHECK INFO", RED)
                time.sleep(2)

        elif choice == "Back":
            return

def updates_settings_menu():
    while True:
        choice = simple_menu("UPDATES", [
            "Update Now",
            "Back"
        ])

        if choice == "Update Now":
            settings = settings_manager.load_settings()

            connected = update_manager.connect_wifi(
                settings.get("wifi_ssid", ""),
                settings.get("wifi_password", ""),
                oled,
                screen_status
            )

            if connected:
                update_manager.check_for_updates(screen_status)
            else:
                screen_status("NO WIFI", "CONNECT", "FIRST", RED)
                time.sleep(2)

        elif choice == "Back":
            return

def console_settings_menu():
    while True:
        settings = settings_manager.load_settings()

        auto_text = "Auto Update: "
        if settings.get("auto_update", True):
            auto_text += "On"
        else:
            auto_text += "Off"

        joystick_mode = settings.get("joystick_mode", "normal")

        choice = simple_menu("CONSOLE", [
            "Username",
            "Joystick",
            auto_text,
            "Back"
        ])

        if choice == "Username":
            settings["username"] = keyboard.type_text(
                oled,
                controls,
                "USERNAME",
                settings.get("username", "")
            )
            settings_manager.save_settings(settings)

        elif choice == "Joystick":
            joystick_settings_menu(settings)

        elif choice.startswith("Auto Update"):
            settings["auto_update"] = not settings.get("auto_update", True)
            settings_manager.save_settings(settings)

            if settings["auto_update"]:
                screen_status("AUTO UPDATE", "ON", "", GREEN)
            else:
                screen_status("AUTO UPDATE", "OFF", "", YELLOW)

            time.sleep(1)

        elif choice == "Back":
            return

def joystick_settings_menu(settings):
    modes = [
        ["normal", "Normal"],
        ["rotated_left", "Rotated Left"],
        ["rotated_right", "Rotated Right"],
        ["upside_down", "Upside Down"]
    ]

    current_mode = settings.get("joystick_mode", "normal")
    index = 0

    for i in range(len(modes)):
        if modes[i][0] == current_mode:
            index = i

    last_move = time.ticks_ms()

    while True:
        oled.fill(BLACK)

        center_text("JOYSTICK", 3, CYAN)
        center_text(modes[index][1], 24, WHITE)
        center_text("<       >", 40, YELLOW)
        center_text("GREEN SAVE", 56, GREEN)
        oled.text("Y=Back", 2, 70, GRAY)

        oled.show()

        left, right, up, down = joystick_direction()
        now = time.ticks_ms()

        if time.ticks_diff(now, last_move) > 220:
            if left:
                index -= 1
                if index < 0:
                    index = len(modes) - 1
                last_move = now

            elif right:
                index += 1
                if index >= len(modes):
                    index = 0
                last_move = now

        if green_pressed():
            wait_release()

            settings["joystick_mode"] = modes[index][0]
            settings_manager.save_settings(settings)

            screen_status("JOYSTICK", "SAVED", modes[index][1], GREEN)
            time.sleep(1)
            return

        if yellow_pressed():
            wait_release()
            return

        time.sleep(0.03)

def dev_settings_menu():
    while True:
        choice = simple_menu("DEV", [
            "Test Games",
            "Back"
        ])

        if choice == "Test Games":
            test_games_menu()

        elif choice == "Back":
            return

def settings_menu():
    while True:
        settings = settings_manager.load_settings()
        dev_mode = settings.get("dev_mode", False)

        items = [
            "WiFi",
            "Updates",
            "Console"
        ]

        if dev_mode:
            items.append("Dev")

        items.append("Back")

        choice = simple_menu("SETTINGS", items)

        if choice == "WiFi":
            wifi_settings_menu()

        elif choice == "Updates":
            updates_settings_menu()

        elif choice == "Console":
            console_settings_menu()

        elif choice == "Dev":
            if dev_mode:
                dev_settings_menu()

        elif choice == "Back":
            return

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

def game_carousel(mode="singleplayer"):
    games = list_local_games(mode=mode)
    index = 0
    last_move = time.ticks_ms()

    while True:
        games = list_local_games(mode=mode)

        if len(games) > 0:
            if index >= len(games):
                index = 0

        oled.fill(BLACK)

        if mode == "multiplayer":
            center_text("MP GAMES", 3, CYAN)
        else:
            center_text("SINGLE PLAYER", 3, CYAN)

        oled.text("<", 3, 36, YELLOW)
        oled.text(">", 150, 36, YELLOW)

        if len(games) == 0:
            center_text("NO GAMES", 30, RED)
            center_text("YELLOW BACK", 50, WHITE)
        else:
            game = games[index]
            center_text(game["title"][:18], 24, WHITE)
            center_text("v" + game.get("display_version", "?"), 40, CYAN)

            if mode == "multiplayer":
                center_text("GREEN HOST", 58, GREEN)
            else:
                center_text("GREEN PLAY", 58, GREEN)

        oled.text("Y=Back", 2, 70, GRAY)
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

            if mode == "singleplayer":
                run_game(games[index])
            else:
                return games[index]

        if yellow_pressed():
            wait_release()
            return None

        time.sleep(0.03)

def multiplayer_host_menu(mp_mode="online"):
    settings = settings_manager.load_settings()

    if mp_mode == "online":
        if online_relay == None:
            screen_status("MP ERROR", "NO RELAY", "UPDATE OS", RED)
            time.sleep(2)
            return

        connected = update_manager.connect_wifi(
            settings.get("wifi_ssid", ""),
            settings.get("wifi_password", ""),
            oled,
            screen_status
        )

        if not connected:
            screen_status("NO WIFI", "CONNECT", "FIRST", RED)
            time.sleep(2)
            return

        screen_status("ROOM", "CREATING", "", CYAN)

        room = online_relay.create_room()

        if not room.get("ok", False):
            screen_status("ROOM FAIL", str(room.get("error", ""))[:16], "", RED)
            time.sleep(3)
            return

        code = room.get("code", "00000")

    else:
        code = "LOCAL"
        screen_status("LOCAL HOST", "PICK GAME", "JOIN WAITS", CYAN)
        time.sleep(1)

    games = list_local_games(mode="multiplayer", mp_mode=mp_mode)
    index = 0
    last_move = time.ticks_ms()

    while True:
        oled.fill(BLACK)

        if mp_mode == "online":
            center_text("CODE " + code, 3, CYAN)
        else:
            center_text("LOCAL HOST", 3, CYAN)

        if len(games) == 0:
            center_text("NO MP GAMES", 30, RED)
            center_text("YELLOW BACK", 50, WHITE)
        else:
            game = games[index]

            oled.text("<", 3, 36, YELLOW)
            oled.text(">", 150, 36, YELLOW)

            center_text(game["title"][:18], 24, WHITE)
            if mp_mode == "online":
                center_text("ONLINE v" + game.get("display_version", "?"), 40, CYAN)
            else:
                network = game.get("network", "local")
            
                if network == "online":
                    center_text("LOCAL/ONLINE", 40, CYAN)
                else:
                    center_text("LOCAL ONLY", 40, CYAN)
            center_text("GREEN START", 58, GREEN)

        oled.text("Y=Back", 2, 70, GRAY)
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

            game = games[index]

            if mp_mode == "online":
                result = online_relay.set_game(code, game["id"])

                if not result.get("ok", False):
                    screen_status("SET GAME", "FAILED", "", RED)
                    time.sleep(2)
                else:
                    run_multiplayer_game(game, "host", code, mp_mode)

            else:
                run_multiplayer_game(game, "host", code, mp_mode)

        if yellow_pressed():
            wait_release()
            return

        time.sleep(0.03)

def multiplayer_join_menu(mp_mode="online"):
    settings = settings_manager.load_settings()

    if mp_mode == "online":
        if online_relay == None:
            screen_status("MP ERROR", "NO RELAY", "UPDATE OS", RED)
            time.sleep(2)
            return

        connected = update_manager.connect_wifi(
            settings.get("wifi_ssid", ""),
            settings.get("wifi_password", ""),
            oled,
            screen_status
        )

        if not connected:
            screen_status("NO WIFI", "CONNECT", "FIRST", RED)
            time.sleep(2)
            return

        code = keyboard.type_text(
            oled,
            controls,
            "ROOM CODE",
            ""
        )

        if len(code) != 5:
            screen_status("BAD CODE", "NEED", "5 DIGITS", RED)
            time.sleep(2)
            return

        screen_status("JOINING", code, "WAIT", CYAN)

        result = online_relay.join_room(code)

        if not result.get("ok", False):
            screen_status("JOIN FAIL", str(result.get("error", ""))[:16], "", RED)
            time.sleep(3)
            return

        wait_for_host_game(code, mp_mode)

    else:
        game = local_join_game_select()

        if game != None:
            run_multiplayer_game(game, "joiner", "LOCAL", mp_mode)

def local_join_game_select():
    games = list_local_games(mode="multiplayer", mp_mode="local")
    index = 0
    last_move = time.ticks_ms()

    while True:
        oled.fill(BLACK)
        center_text("LOCAL JOIN", 3, CYAN)

        if len(games) == 0:
            center_text("NO MP GAMES", 30, RED)
            center_text("YELLOW BACK", 50, WHITE)
        else:
            game = games[index]

            oled.text("<", 3, 36, YELLOW)
            oled.text(">", 150, 36, YELLOW)

            center_text(game["title"][:18], 24, WHITE)
            center_text("v" + game.get("display_version", "?"), 40, CYAN)
            center_text("GREEN JOIN", 58, GREEN)

        oled.text("Y=Back", 2, 70, GRAY)
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
            return games[index]

        if yellow_pressed():
            wait_release()
            return None

        time.sleep(0.03)

def wait_for_host_game(code, mp_mode="online"):
    last_check = time.ticks_ms()
    status = {}

    while True:
        oled.fill(BLACK)
        center_text("JOINED", 3, GREEN)
        center_text("CODE " + code, 20, CYAN)

        game_id = status.get("game", "")

        if game_id == "":
            center_text("WAIT HOST", 42, WHITE)
        else:
            center_text("GAME:", 34, WHITE)
            center_text(game_id[:18], 50, YELLOW)

        oled.text("Y=Back", 2, 70, GRAY)
        oled.show()

        now = time.ticks_ms()

        if time.ticks_diff(now, last_check) > 1500:
            status = online_relay.get_status(code)
            last_check = now

            if status.get("ok", False):
                game_id = status.get("game", "")

                if game_id != "":
                    game = find_game_by_id(game_id)

                    if game != None:
                        run_multiplayer_game(game, "joiner", code, mp_mode)
                        return
                    else:
                        screen_status("NO GAME", game_id[:16], "INSTALLED", RED)
                        time.sleep(3)
                        return

        if yellow_pressed():
            wait_release()
            return

        time.sleep(0.03)

def find_game_by_id(game_id):
    games = list_local_games(mode="multiplayer", mp_mode=mp_mode)

    for game in games:
        if game["id"] == game_id:
            return game

    return None

def run_multiplayer_game(game, role, room_code, mp_mode="online"):
    oled.fill(BLACK)
    center_text("MP LOADING", 16, YELLOW)
    center_text(role.upper(), 36, CYAN)

    if mp_mode == "local":
        center_text("LOCAL", 56, WHITE)
    else:
        center_text(room_code, 56, WHITE)

    oled.show()
    time.sleep(1)

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

        settings = settings_manager.load_settings()
        settings["mp_mode"] = mp_mode

        if hasattr(game_module, "main"):
            game_module.main(
                oled,
                controls,
                settings,
                role,
                room_code
            )
        else:
            screen_status("GAME ERROR", "NO main()", game["title"][:16], RED)
            time.sleep(2)

    except Exception as e:
        print("MP GAME ERROR:", e)
        screen_status("MP ERROR", str(e)[:16], game["title"][:16], RED)
        time.sleep(3)

def multiplayer_mode_menu(mp_mode):
    while True:
        if mp_mode == "online":
            title = "ONLINE MP"
        else:
            title = "LOCAL MP"

        choice = simple_menu(title, [
            "Host",
            "Join",
            "Back"
        ])

        if choice == "Host":
            multiplayer_host_menu(mp_mode)

        elif choice == "Join":
            multiplayer_join_menu(mp_mode)

        elif choice == "Back":
            return


def multiplayer_menu():
    while True:
        choice = simple_menu("MULTIPLAYER", [
            "Online",
            "Local",
            "Back"
        ])

        if choice == "Online":
            multiplayer_mode_menu("online")

        elif choice == "Local":
            multiplayer_mode_menu("local")

        elif choice == "Back":
            return

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

    while True:
        choice = simple_menu("PIXELFORGE", [
            "Single Player",
            "Multiplayer",
            "Settings"
        ])

        if choice == "Single Player":
            game_carousel("singleplayer")

        elif choice == "Multiplayer":
            multiplayer_menu()

        elif choice == "Settings":
            settings_menu()

ensure_folders()

screen_status("PIXELFORGE", "BOOTING", "OS", CYAN)
time.sleep(1)

home_screen()
