import ujson
import os

SETTINGS_FILE = "/data/settings.json"
VERSIONS_FILE = "/data/versions.json"

DEFAULT_SETTINGS = {
    "username": "PLAYER",
    "wifi_ssid": "",
    "wifi_password": "",
    "auto_update": True,
    "dev_mode" : False
}

def ensure_data_folder():
    try:
        os.mkdir("/data")
    except OSError:
        pass

def load_settings():
    ensure_data_folder()

    try:
        with open(SETTINGS_FILE, "r") as f:
            return ujson.loads(f.read())
    except:
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    ensure_data_folder()

    with open(SETTINGS_FILE, "w") as f:
        f.write(ujson.dumps(settings))

def load_versions():
    ensure_data_folder()

    try:
        with open(VERSIONS_FILE, "r") as f:
            return ujson.loads(f.read())
    except:
        save_versions({})
        return {}

def save_versions(versions):
    ensure_data_folder()

    with open(VERSIONS_FILE, "w") as f:
        f.write(ujson.dumps(versions))
GAME_INFO_FILE = "/data/game_info.json"

def load_game_info():
    ensure_data_folder()

    try:
        with open(GAME_INFO_FILE, "r") as f:
            return ujson.loads(f.read())
    except:
        save_game_info({})
        return {}

def save_game_info(game_info):
    ensure_data_folder()

    with open(GAME_INFO_FILE, "w") as f:
        f.write(ujson.dumps(game_info))

