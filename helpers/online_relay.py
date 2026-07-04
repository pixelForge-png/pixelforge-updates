import urequests
import ujson

RELAY_URL = "https://pixelforge-relay-server-1.onrender.com"

def get_json(path):
    try:
        response = urequests.get(RELAY_URL + path)
        text = response.text
        response.close()
        return ujson.loads(text)
    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }

def create_room():
    return get_json("/create")

def join_room(code):
    return get_json("/join?code=" + str(code))

def set_game(code, game_id):
    return get_json("/setgame?code=" + str(code) + "&game=" + str(game_id))

def get_status(code):
    return get_json("/status?code=" + str(code))

def send_data(code, player, data):
    return get_json(
        "/send?code=" + str(code) +
        "&player=" + str(player) +
        "&data=" + str(data)
    )

def read_data(code, player):
    return get_json(
        "/read?code=" + str(code) +
        "&player=" + str(player)
    )
