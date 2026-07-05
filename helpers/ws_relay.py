import socket
import ssl
import ubinascii
import urandom
import time

RELAY_HOST = "pixelforge-relay-server-1.onrender.com"
RELAY_PORT = 443

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

        try:
            raw_sock.settimeout(8)
        except:
            pass

        raw_sock.connect(addr)

        self.sock = ssl.wrap_socket(raw_sock, server_hostname=self.host)

        try:
            self.sock.settimeout(8)
        except:
            pass

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

        response = self._read_http_header(8000)

        if response == None:
            raise Exception("no handshake")

        if b"101" not in response:
            try:
                text = response.decode()
                first_line = text.split("\r\n")[0]
                raise Exception(first_line[:18])
            except:
                raise Exception("bad handshake")

        # After connecting, use shorter reads.
        try:
            self.sock.settimeout(0.015)
        except:
            pass

        # Read initial OK|code message if it is already waiting.
        self.recv_text()

    def _read_http_header(self, max_ms):
        data = b""
        start = time.ticks_ms()

        while True:
            if b"\r\n\r\n" in data:
                return data

            if time.ticks_diff(time.ticks_ms(), start) > max_ms:
                return None

            try:
                chunk = self.sock.read(1)

                if chunk != None and len(chunk) > 0:
                    data += chunk

                    if len(data) > 1200:
                        return data

            except:
                if time.ticks_diff(time.ticks_ms(), start) > max_ms:
                    return None

            time.sleep(0.001)

    def _read_exact(self, amount, max_ms=20):
        data = b""
        start = time.ticks_ms()

        while len(data) < amount:
            if time.ticks_diff(time.ticks_ms(), start) > max_ms:
                return None

            try:
                chunk = self.sock.read(amount - len(data))

                if chunk != None and len(chunk) > 0:
                    data += chunk

            except:
                if time.ticks_diff(time.ticks_ms(), start) > max_ms:
                    return None

            time.sleep(0.001)

        return data

    def send_text(self, text):
        if self.sock == None:
            return False

        try:
            payload = text.encode()
            length = len(payload)

            if length < 126:
                header = bytes([0x81, 0x80 | length])
            elif length < 65536:
                header = bytes([
                    0x81,
                    0x80 | 126,
                    (length >> 8) & 255,
                    length & 255
                ])
            else:
                return False

            frame = header + _mask_payload(payload)
            self.sock.write(frame)
            return True

        except:
            return False

    def recv_text(self):
        if self.sock == None:
            return None

        try:
            header = self._read_exact(2)

            if header == None:
                return None

            first = header[0]
            second = header[1]

            opcode = first & 0x0F
            masked = (second & 0x80) != 0
            length = second & 0x7F

            if length == 126:
                ext = self._read_exact(2)

                if ext == None:
                    return None

                length = (ext[0] << 8) | ext[1]

            elif length == 127:
                return None

            mask = None

            if masked:
                mask = self._read_exact(4)

                if mask == None:
                    return None

            payload = self._read_exact(length)

            if payload == None:
                return None

            if masked:
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

    def sync(self, data):
        ok = self.send_text("SYNC|" + str(data))

        if not ok:
            return None

        return self.recv_text()

    def close(self):
        try:
            self.sock.close()
        except:
            pass

        self.sock = None
