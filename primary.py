"""
Duties of the primary device:
1. Query GPS location and store it
2. Serve a website for the user to interact with
3. Manage the route
4. Allow the secondary server to receive commands
"""

import subprocess
import threading
import json
import time

# Runs a command on the terminal and returns the output
def run_command(command):
    return subprocess.check_output("termux-location", shell=True)

# Returns the GPS location
def where_am_i():
    print("[GPS] Querying...")
    try:
        return json.loads(run_command("termux-location"))
    except:
        print("[GPS] Failed, using termux cache")
        return json.loads(run_command("termux-location -r last"))
    print("[GPS] Cache updated")

# Begin execution!

# Start the thread to continuously update the gps location
gps_cache = None
def update_location():
    global gps_cache
    while True:
        gps_cache = where_am_i()

locator = threading.Thread(target=update_location)
locator.start()

# Wait for the initial GPS location to be found
print("[GPS] Waiting for initial location to be found...")
while gps_cache is None:
    time.sleep(1)
print("[GPS] Initial location found")

while True:
    print(gps_cache)
    time.sleep(1)
