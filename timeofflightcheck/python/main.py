from arduino.app_utils import *
import time

def loop():
    distance = Bridge.call("get_distance")
    print(f"Distance: {distance} mm")
    time.sleep(0.1)

App.run(user_loop=loop)