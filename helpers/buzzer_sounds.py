from machine import Pin, PWM
import time

buzzer = PWM(Pin(6))
buzzer.freq(440)
buzzer.duty_u16(0)

def sound(frequency, volume, t):
    buzzer.freq(frequency)
    buzzer.duty_u16(volume)
    time.sleep(t)
    buzzer.duty_u16(0)
