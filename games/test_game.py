import time

def run(display=None, buttons=None):
    print("Test Game started!")

    if display:
        display.fill(0)
        display.text("PIXELFORGE", 20, 10, 1)
        display.text("Test Game", 24, 30, 1)
        display.show()

    time.sleep(2)
