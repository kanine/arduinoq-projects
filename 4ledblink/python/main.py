import time
from arduino.app_utils import App

# RGB LED 1 — MPU-controlled via sysfs
# RGB LED 2 — MPU-controlled via sysfs
LED_PATHS = {
    'rgb1_r': '/sys/class/leds/red:user/brightness',
    'rgb1_g': '/sys/class/leds/green:user/brightness',
    'rgb1_b': '/sys/class/leds/blue:user/brightness',
    'rgb2_r': '/sys/class/leds/red:panic/brightness',
    'rgb2_g': '/sys/class/leds/green:wlan/brightness',
    'rgb2_b': '/sys/class/leds/blue:bt/brightness',
}

# Colour sequence: Red → Green → Blue → repeat
COLOURS = [
    ('rgb1_r', 'rgb2_r'),
    ('rgb1_g', 'rgb2_g'),
    ('rgb1_b', 'rgb2_b'),
]

STEP_S = 0.5

_phase = 0


def write_led(name, value):
    try:
        with open(LED_PATHS[name], 'w') as f:
            f.write(str(value))
    except OSError:
        pass


def all_off():
    for name in LED_PATHS:
        write_led(name, 0)


def loop():
    global _phase
    all_off()
    ch1, ch2 = COLOURS[_phase]
    write_led(ch1, 255)
    write_led(ch2, 255)
    _phase = (_phase + 1) % len(COLOURS)
    time.sleep(STEP_S)


all_off()
App.run(user_loop=loop)
