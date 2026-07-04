import time

def main(oled, controls, settings, role, room_code):
    while True:
        oled.fill(0)
        oled.text("MP TEST", 48, 5, 65535)
        oled.text(role.upper(), 48, 22, 65535)
        oled.text("CODE " + room_code, 35, 39, 65535)
        oled.text("Y BACK", 50, 60, 65535)
        oled.show()

        if controls["yellow"]():
            time.sleep(0.3)
            return

        time.sleep(0.03)
