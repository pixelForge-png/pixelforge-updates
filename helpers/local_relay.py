import network
import socket
import time

LOCAL_SSID = "PixelForgeLocal"
LOCAL_HOST_IP = "192.168.4.1"
LOCAL_PORT = 5050


class LocalSocketClient:
    def __init__(self):
        self.role = None
        self.sock = None
        self.conn = None
        self.buffer = b""
        self.peer_data = ""
        self.message_id = 0

    def connect(self, code, player):
        self.role = player

        if player == "host":
            self._host_connect()
        else:
            self._join_connect()

    def _host_connect(self):
        try:
            sta = network.WLAN(network.STA_IF)
            sta.active(False)
        except:
            pass

        ap = network.WLAN(network.AP_IF)

        try:
            ap.active(False)
            time.sleep(0.8)
        except:
            pass

        ap.active(True)
        time.sleep(0.5)

        # Try to rename the hotspot.
        # If the Pico ignores this, it may still show as PICO####.
        try:
            ap.config(essid=LOCAL_SSID)
        except:
            pass

        try:
            ap.ifconfig((LOCAL_HOST_IP, "255.255.255.0", LOCAL_HOST_IP, LOCAL_HOST_IP))
        except:
            pass

        # Give the hotspot time to fully appear.
        time.sleep(5)

        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("0.0.0.0", LOCAL_PORT))
        self.sock.listen(1)

        self.conn, addr = self.sock.accept()

        try:
            self.conn.settimeout(0.02)
        except:
            pass

    def _join_connect(self):
        try:
            ap = network.WLAN(network.AP_IF)
            ap.active(False)
        except:
            pass

        wlan = network.WLAN(network.STA_IF)

        wlan.active(False)
        time.sleep(0.8)
        wlan.active(True)
        time.sleep(1)

        # Look for either PixelForgeLocal or the Pico's default PICO#### hotspot.
        target_ssid = None
        scan_start = time.ticks_ms()

        while time.ticks_diff(time.ticks_ms(), scan_start) < 15000:
            try:
                networks = wlan.scan()

                for net in networks:
                    try:
                        ssid = net[0].decode()
                    except:
                        ssid = str(net[0])

                    ssid_upper = ssid.upper()

                    if ssid == LOCAL_SSID:
                        target_ssid = ssid
                        break

                    if ssid_upper.startswith("PICO"):
                        target_ssid = ssid
                        break

                if target_ssid != None:
                    break

            except:
                pass

            time.sleep(0.5)

        if target_ssid == None:
            raise Exception("no local ap")

        try:
            wlan.disconnect()
        except:
            pass

        time.sleep(0.5)

        # Connect to the network we actually found.
        wlan.connect(target_ssid)

        start = time.ticks_ms()

        while not wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), start) > 15000:
                raise Exception("wifi 110 " + target_ssid[:8])

            time.sleep(0.2)

        time.sleep(1)

        self.conn = socket.socket()

        try:
            self.conn.settimeout(8)
        except:
            pass

        self.conn.connect((LOCAL_HOST_IP, LOCAL_PORT))

        try:
            self.conn.settimeout(0.02)
        except:
            pass

    def _send_line(self, text):
        if self.conn == None:
            return False

        try:
            self.conn.send((text + "\n").encode())
            return True
        except:
            return False

    def _read_lines(self, max_ms=20):
        start = time.ticks_ms()

        while time.ticks_diff(time.ticks_ms(), start) < max_ms:
            try:
                chunk = self.conn.recv(64)

                if chunk == None or len(chunk) == 0:
                    return

                self.buffer += chunk

                while b"\n" in self.buffer:
                    index = self.buffer.find(b"\n")
                    line = self.buffer[:index]
                    self.buffer = self.buffer[index + 1:]

                    try:
                        text = line.decode().strip()
                    except:
                        text = ""

                    self._handle_line(text)

            except:
                return

    def _handle_line(self, text):
        if self.role == "host":
            if text.startswith("J|"):
                self.peer_data = text[2:]
                self.message_id += 1
        else:
            if text.startswith("H|"):
                self.peer_data = text[2:]
                self.message_id += 1

    def sync(self, data):
        if self.conn == None:
            return None

        if self.role == "host":
            self._read_lines(8)
            self._send_line("H|" + str(data))
            return "PEER|" + str(self.message_id) + "|" + self.peer_data

        else:
            self._send_line("J|" + str(data))
            self._read_lines(20)
            return "PEER|" + str(self.message_id) + "|" + self.peer_data

    def close(self):
        try:
            self.conn.close()
        except:
            pass

        try:
            self.sock.close()
        except:
            pass

        self.conn = None
        self.sock = None
