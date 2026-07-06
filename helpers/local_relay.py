import network
import socket
import time

LOCAL_SSID = "PixelForgeLocal"
LOCAL_PASSWORD = "pixelforge"
LOCAL_HOST_IP = "192.168.4.1"
LOCAL_PORT = 5050


class LocalSocketClient:
    def __init__(self):
        self.role = None
        self.sock = None
        self.peer_addr = None
        self.peer_data = ""
        self.message_id = 0

    def connect(self, code, player):
        self.role = player

        if player == "host":
            self._host_connect()
        else:
            self._join_connect()

    def _host_connect(self):
        # Fully shut down normal Wi-Fi.
        try:
            sta = network.WLAN(network.STA_IF)
            sta.disconnect()
            sta.active(False)
        except:
            pass

        time.sleep(1)

        ap = network.WLAN(network.AP_IF)

        try:
            ap.active(False)
        except:
            pass

        time.sleep(1)

        # Set AP settings before turning it on.
        try:
            ap.config(essid=LOCAL_SSID, password=LOCAL_PASSWORD)
        except:
            try:
                ap.config(ssid=LOCAL_SSID, password=LOCAL_PASSWORD)
            except:
                pass

        try:
            ap.ifconfig((LOCAL_HOST_IP, "255.255.255.0", LOCAL_HOST_IP, LOCAL_HOST_IP))
        except:
            pass

        ap.active(True)

        time.sleep(6)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", LOCAL_PORT))

        try:
            self.sock.settimeout(0.05)
        except:
            pass

        # Wait for joiner hello.
        start = time.ticks_ms()

        while True:
            try:
                data, addr = self.sock.recvfrom(128)

                try:
                    text = data.decode()
                except:
                    text = ""

                if text.startswith("HELLO"):
                    self.peer_addr = addr
                    self.sock.sendto(b"WELCOME", self.peer_addr)
                    break

            except:
                pass

            if time.ticks_diff(time.ticks_ms(), start) > 30000:
                raise Exception("no joiner")

            time.sleep(0.05)

        try:
            self.sock.settimeout(0)
        except:
            pass

    def _join_connect(self):
        # Turn off AP mode on joiner.
        try:
            ap = network.WLAN(network.AP_IF)
            ap.active(False)
        except:
            pass

        wlan = network.WLAN(network.STA_IF)

        try:
            wlan.disconnect()
        except:
            pass

        wlan.active(False)
        time.sleep(1)
        wlan.active(True)
        time.sleep(1)

        # Find PixelForgeLocal.
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

                    if ssid == LOCAL_SSID:
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

        wlan.connect(target_ssid, LOCAL_PASSWORD)

        start = time.ticks_ms()

        while not wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), start) > 15000:
                raise Exception("wifi 110")

            time.sleep(0.2)

        time.sleep(1)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            self.sock.settimeout(0.05)
        except:
            pass

        self.peer_addr = (LOCAL_HOST_IP, LOCAL_PORT)

        # Send hello until host answers.
        start = time.ticks_ms()

        while True:
            try:
                self.sock.sendto(b"HELLO", self.peer_addr)

                data, addr = self.sock.recvfrom(128)

                try:
                    text = data.decode()
                except:
                    text = ""

                if text.startswith("WELCOME"):
                    self.peer_addr = addr
                    break

            except:
                pass

            if time.ticks_diff(time.ticks_ms(), start) > 30000:
                raise Exception("no host")

            time.sleep(0.1)

        try:
            self.sock.settimeout(0)
        except:
            pass

    def _read_all_latest(self):
        # Read every waiting packet and keep only the newest useful one.
        while True:
            try:
                data, addr = self.sock.recvfrom(256)

                try:
                    text = data.decode().strip()
                except:
                    text = ""

                if self.role == "host":
                    if text.startswith("J|"):
                        self.peer_data = text[2:]
                        self.peer_addr = addr
                        self.message_id += 1

                else:
                    if text.startswith("H|"):
                        self.peer_data = text[2:]
                        self.peer_addr = addr
                        self.message_id += 1

            except:
                break

    def sync(self, data):
        if self.sock == None or self.peer_addr == None:
            return None

        # First drain old packets so we keep the newest peer data.
        self._read_all_latest()

        try:
            if self.role == "host":
                self.sock.sendto(("H|" + str(data)).encode(), self.peer_addr)
            else:
                self.sock.sendto(("J|" + str(data)).encode(), self.peer_addr)
        except:
            return None

        # Read again in case a fresh packet arrived right after sending.
        self._read_all_latest()

        return "PEER|" + str(self.message_id) + "|" + self.peer_data

    def close(self):
        try:
            self.sock.close()
        except:
            pass

        self.sock = None
        self.peer_addr = None
