import network
import time
import urequests
import ujson
import os
import settings_manager

MANIFEST_URL = "https://raw.githubusercontent.com/pixelForge-png/pixelforge-updates/main/manifest.json"

def ensure_folder(path):
    try:
        os.mkdir(path)
    except OSError:
        pass

def ensure_parent_folder(filepath):
    parts = filepath.split("/")

    if len(parts) <= 2:
        return

    folder = "/" + parts[1]

    try:
        os.mkdir(folder)
    except OSError:
        pass

def connect_wifi(ssid, password, oled=None, screen_status=None):
    if ssid == "":
        return False

    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)

    if wifi.isconnected():
        return True

    if screen_status:
        screen_status("WIFI", "CONNECTING", ssid)

    if password == "":
        wifi.connect(ssid)
    else:
        wifi.connect(ssid, password)

    start = time.ticks_ms()

    while not wifi.isconnected():
        elapsed = time.ticks_diff(time.ticks_ms(), start) // 1000

        if screen_status:
            screen_status("WIFI", "WAIT " + str(elapsed), ssid)

        if elapsed > 10:
            if screen_status:
                screen_status("NO WIFI", "COULDNT", "CONNECT")
                time.sleep(2)
            return False

        time.sleep(1)

    if screen_status:
        screen_status("WIFI", "CONNECTED", wifi.ifconfig()[0])
        time.sleep(1)

    return True

def download_text(url):
    response = urequests.get(url)
    text = response.text
    response.close()
    return text

def download_file(url, filepath):
    ensure_parent_folder(filepath)

    response = urequests.get(url)

    with open(filepath, "w") as f:
        f.write(response.text)

    response.close()

def download_manifest(screen_status=None):
    if screen_status:
        screen_status("UPDATES", "CHECKING", "")

    try:
        manifest_text = download_text(MANIFEST_URL)
        manifest = ujson.loads(manifest_text)
        return manifest
    except Exception as e:
        if screen_status:
            screen_status("UPDATE FAIL", "MANIFEST", str(e)[:16])
            time.sleep(2)
        return None

def update_file_list(file_list, versions, version_prefix, dev_mode, screen_status=None):
    updated_count = 0

    for item in file_list:
        channel = item.get("channel", "release")

        if channel == "dev" and not dev_mode:
            continue

        file_id = version_prefix + item["id"]
        filepath = "/" + item["file"]
        version = item["version"]
        url = item["url"]

        current_version = versions.get(file_id, 0)

        needs_update = False

        if current_version < version:
            needs_update = True

        try:
            os.stat(filepath)
        except OSError:
            needs_update = True

        if needs_update:
            if screen_status:
                screen_status("DOWNLOADING", item["id"][:16], "v" + str(version))

            try:
                download_file(url, filepath)
                versions[file_id] = version
                updated_count += 1
            except Exception as e:
                if screen_status:
                    screen_status("DL FAILED", item["id"][:16], str(e)[:16])
                    time.sleep(2)

    return updated_count

def check_for_updates(screen_status=None):
    ensure_folder("/games")
    ensure_folder("/data")
    ensure_folder("/helpers")

    manifest = download_manifest(screen_status)

    if manifest == None:
        return []

    versions = settings_manager.load_versions()
    settings = settings_manager.load_settings()
    game_info = settings_manager.load_game_info()

    dev_mode = settings.get("dev_mode", False)

    updated_count = 0

    system_files = manifest.get("system_files", [])
    updated_count += update_file_list(
        system_files,
        versions,
        "system_",
        dev_mode,
        screen_status
    )

    helper_files = manifest.get("helpers", [])
    updated_count += update_file_list(
        helper_files,
        versions,
        "helper_",
        dev_mode,
        screen_status
    )

    games = manifest.get("games", [])
    visible_games = []

    for game in games:
        channel = game.get("channel", "release")

        if channel == "dev" and not dev_mode:
            continue

        visible_games.append(game)

        game_info[game["id"]] = {
            "title": game.get("title", game["id"]),
            "display_version": game.get("display_version", str(game["version"])),
            "channel": game.get("channel", "release")
        }

        game_id = game["id"]
        title = game["title"]
        filepath = "/" + game["file"]
        version = game["version"]
        url = game["url"]

        current_version = versions.get(game_id, 0)

        needs_update = False

        if current_version < version:
            needs_update = True

        try:
            os.stat(filepath)
        except OSError:
            needs_update = True

        if needs_update:
            if screen_status:
                display_version = game.get("display_version", str(version))
                screen_status("DOWNLOADING", title[:16], "v" + display_version)

            try:
                download_file(url, filepath)
                versions[game_id] = version
                updated_count += 1
            except Exception as e:
                if screen_status:
                    screen_status("DL FAILED", title[:16], str(e)[:16])
                    time.sleep(2)

    settings_manager.save_game_info(game_info)
    settings_manager.save_versions(versions)

    if screen_status:
        if updated_count == 0:
            screen_status("UPDATES", "NO NEW", "FILES")
        else:
            screen_status("UPDATED", str(updated_count), "FILE(S)")
        time.sleep(1)

    return visible_games

def load_manifest_only(screen_status=None):
    try:
        manifest_text = download_text(MANIFEST_URL)
        manifest = ujson.loads(manifest_text)
        return manifest.get("games", [])
    except:
        return []
