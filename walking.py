from primary import run_command
import json
import time

def acceleration():
    values = json.loads(run_command("termux-sensor -s linear_acceleration -n 1"))["linear_acceleration"]["values"]
    speed = sum([abs(v) for v in values])
    return speed

while True:
    print(acceleration())
