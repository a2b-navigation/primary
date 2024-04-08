import subprocess
import time as t

# Tell vibration motor to fire for a certain amount of time
def burst(length):
    length *= 1000 # Convert to ms
    subprocess.run(f"termux-vibrate -d {int(length)} -f")
    print("On")
    t.sleep(length)
    print("Off")

# This will actuate a device n_vibrations per second
def actuate(n_vibrations):
    time_between = 1 / n_vibrations
    while True:
        burst(time_between)
        t.sleep(time_between)

very_near = lambda: actuate(0.7)
near = lambda: actuate(1.2)
far = lambda: actuate(2)
very_far = lambda: actuate(4)
