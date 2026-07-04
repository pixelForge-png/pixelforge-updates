import socket
import ssl
import ubinascii
import uhashlib
import urandom
import time

RELAY_HOST = "pixelforge-relay-server.onrender.com"
RELAY_PORT = 443

_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

def _b64(data):
    return ubinascii.b2a_base64(data).strip().decode()

def _make_key():
    raw = bytes([urandom.getrandbits(8) for _ in range(16)])
    return _b64(raw)

def _mask_payload(payload):
    mask = bytes([urandom.getrandbits(8) for _ in range(4)])
    masked = bytearray()

    for i in range(len(payload)):
        masked.append(payload[i] ^ mask[i % 4])

    return mask + bytes(masked)

class WebSocketClient:
    def __init__(self, host=RELAY_HOST, port=RELAY_PORT):
        self.host = host
        self.port = port
        self.sock = None

    def connect(self, code, player):
        addr = socket.getaddrinfo(self.host, self.port)[0][-1]
        raw_sock = socket.socket()
        raw_sock.connect(addr)

        self.sock = ssl.wrap_socket(raw_sock, server_hostname=self.host)

        key = _make_key()
        path = "/ws?code=" + str(code) + "&player=" + str(player)

        request = (
            "GET " + path + " HTTP/1.1\r\n" +
            "Host: " + self.host + "\r\n" +
            "Upgrade: websocket\r\n" +
            "Connection: Upgrade\r\n" +
            "Sec-WebSocket-Key: " + key + "\r\n" +
            "Sec-WebSocket-Version: 13\r\n" +
            "\r\n"
        )

        self.sock.write(request.encode())

        response = self.sock.read(512)

        if response == None or b"101" not in response:
            raise Exception("ws handshake failed")

        # Keep reads from freezing forever.
        try:
            self.sock.settimeout(0.01)
        except:
            pass

    def send_text(self, text):
        if self.sock == None:
            return

        payload = text.encode()
        length = len(payload)

        # Client-to-server frames must be masked.
        if length < 126:
            header = bytes([0x81, 0x80 | length])
        elif length < 65536:
            header = bytes([0x81, 0x80 | 126, (length >> 8) & 255, length & 255])
        else:
            raise Exception("message too long")

        frame = header + _mask_payload(payload)
        self.sock.write(frame)

    def recv_text(self):
        if self.sock == None:
            return None

        try:
            first = self.sock.read(1)

            if first == None or len(first) == 0:
                return None

            second = self.sock.read(1)

            if second == None or len(second) == 0:
                return None

            first = first[0]
            second = second[0]

            opcode = first & 0x0F
            masked = (second & 0x80) != 0
            length = second & 0x7F

            if length == 126:
                ext = self.sock.read(2)
                if ext == None or len(ext) < 2:
                    return None
                length = (ext[0] << 8) | ext[1]

            elif length == 127:
                # We do not use giant packets.
                return None

            mask = None
            if masked:
                mask = self.sock.read(4)

            payload = self.sock.read(length)

            if payload == None or len(payload) < length:
                return None

            if masked and mask != None:
                unmasked = bytearray()
                for i in range(len(payload)):
                    unmasked.append(payload[i] ^ mask[i % 4])
                payload = bytes(unmasked)

            if opcode == 0x8:
                return None

            if opcode == 0x1:
                return payload.decode()

            return None

        except:
            return None

    def close(self):
        try:
            self.sock.close()
        except:
            pass

        self.sock = None
