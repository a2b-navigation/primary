import subprocess
import time as t

# Tell vibration motor to fire for a certain amount of time
def burst(length):
    subprocess.run(f"termux-vibrate -d {int(length * 1000)} -f", shell=True)
    t.sleep(length)

# This will actuate a device n_vibrations per second
def actuate(n_vibrations):
    time_between = 1 / n_vibrations / 2
    for _ in range(int(n_vibrations)):
        burst(time_between)
        t.sleep(time_between)

very_near = lambda: actuate(1)
near = lambda: actuate(2)
far = lambda: actuate(4)
very_far = lambda: actuate(8)
