from helpers.ws_relay import WebSocketClient
from helpers.local_relay import LocalSocketClient


class MultiplayerClient:
    def __init__(self, mode="online"):
        self.mode = mode

        if mode == "local":
            self.client = LocalSocketClient()
        else:
            self.client = WebSocketClient()

    def connect(self, room_code, role):
        self.client.connect(room_code, role)

    def sync(self, data):
        return self.client.sync(data)

    def close(self):
        self.client.close()
