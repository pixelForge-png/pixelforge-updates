import time

CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 _-.!?"

def type_text(oled, controls, title, start_text=""):
    text = start_text
    char_index = 0
    last_move = time.ticks_ms()

    while True:
        oled.fill(0)

        oled.text(title, 4, 2, 65535)

        oled.text("Text:", 4, 14, 65535)
        oled.text(text[-18:], 4, 25, 65535)

        oled.text("< " + CHARS[char_index] + " >", 50, 39, 65535)

        oled.text("Joy L/R: Letter", 4, 54, 65535)
        oled.text("Green:Add Yellow:Del", 4, 63, 65535)
        oled.text("Red:Done", 4, 72, 65535)

        oled.show()

        left, right, up, down = controls["joystick"]()
        now = time.ticks_ms()

        if time.ticks_diff(now, last_move) > 120:
            if left:
                char_index -= 1
                if char_index < 0:
                    char_index = len(CHARS) - 1
                last_move = now

            elif right:
                char_index += 1
                if char_index >= len(CHARS):
                    char_index = 0
                last_move = now

        if controls["green"]():
            text += CHARS[char_index]
            wait_buttons_release(controls)
            time.sleep(0.08)

        if controls["yellow"]():
            if len(text) > 0:
                text = text[:-1]
            wait_buttons_release(controls)
            time.sleep(0.08)

        if controls["red"]():
            wait_buttons_release(controls)
            time.sleep(0.2)
            return text

        time.sleep(0.02)

def wait_buttons_release(controls):
    while controls["green"]() or controls["yellow"]() or controls["red"]() or controls["blue"]():
        time.sleep(0.03)
