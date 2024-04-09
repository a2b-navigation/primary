"""
Duties of the primary device:
1. Query GPS location and store it [X]
2. Serve a website for the user to interact with [X]
3. Manage the route [X]
4. Create routes [X]
5. Very defensive input validation [X]
6. Actuate the primary server to issue commands based off route and gps [ ]
7. Allow the secondary server to receive commands based off route and gps [ ]
"""

from flask import *
import subprocess
import directions
import threading
import math as m
import actuation
import json
import time
import os

# Work out the distance between two polar coordinates
def distance(c1, c2):
    lat1, lat2 = c1[0], c2[0]
    lon1, lon2 = c1[1], c2[1]
    radius = 6371
    p = m.pi / 180
    a = 0.5 - m.cos((lat2 - lat1) * p) / 2 + m.cos(lat1 * p) * m.cos(lat2 * p) * (1 - m.cos((lon2 - lon1) * p)) / 2
    return 2 * radius * m.asin(m.sqrt(a)) * 1000

# Validate input
def validate(text):
    return text.replace("_", "").isalnum() and len(text) > 0

# Validate coordinate input
def validate_coord(coord):
    has_comma = coord.count(",") == 1
    has_points = coord.count(".") == 2
    raw_dig = lambda s: s.replace(".", "").replace(",", "").replace("-", "")
    is_numeric = raw_dig(coord).isnumeric()
    good_precision = True
    try:
        [lat, lon] = coord.replace(", ", ",").split(",")
        if len(raw_dig(lat)) < 7: good_precision = False
        if len(raw_dig(lon)) < 7: good_precision = False
        lat = float(lat)
        lon = float(lon)
        can_parse = True
    except:
        can_parse = False
    return has_comma and has_points and is_numeric and can_parse and good_precision

# Runs a command on the terminal and returns the output
def run_command(command):
    return subprocess.check_output(command, shell=True)

# Returns the server IP address
def open_command_centre():
    ip = json.loads(run_command("termux-wifi-connectioninfo"))["ip"]
    run_command(f"termux-open-url 'http://{ip}:5000'")
    return 

# Returns the GPS location
def where_am_i():
    print("[GPS] Querying...")
    try:
        return json.loads(run_command("termux-location"))
    except:
        print("[GPS] Failed, using termux cache")
        return json.loads(run_command("termux-location -r last"))

# Will update the gps cache
gps_cache = None
gps_accuracy = None
def update_gps():
    global gps_cache
    global gps_accuracy
    data = where_am_i()
    gps_cache = {"lat": data["latitude"], "lon": data["longitude"]}
    gps_accuracy = round(data["accuracy"], 1)
    print(f"[GPS] Cache updated with accuracy of {gps_accuracy}m")

# Begin execution!

# Find the initial gps location
print("[GPS] Aquiring initial GPS location")
update_gps()

# Set up route information
active = False # Whether we are following a route or not
route = None # The route we're currently following
route_pointer = 0 # How far we are through the route

# Returns a user friendly representation of the route
def display_route():
    global route
    if route is None:
        return "No route active, activate it above"
    else:
        name = route["name"]
        result = f"Route name: {name}\n"
        for c, beacon in enumerate(route["beacons"]):
            match beacon["do"]:
                case "left": instruction = "Turn left at"
                case "right": instruction = "Turn right at"
                case "depart": instruction = "Depart from"
                case "arrive": instruction = "Arrive at"
            # Output nice human readable instruction
            [lat, lon] = beacon["at"]
            result += f"Step {c + 1}: {instruction} {lat}, {lon}"
            if c == route_pointer: result += " <- Last Instruction" # Show the route progress
            result += "\n"
        return result

# List the available routes
def list_routes():
    routes = os.listdir("routes/")
    result = []
    for file in routes:
        f = open(f"routes/{file}", "r")
        route = json.loads(f.read())
        route["id"] = os.path.splitext(file)[0]
        f.close()
        result.append(route)
    return result

# Obtain a route
def get_route(name):
    routes = list_routes()
    for route in routes:
        if route["id"] == name:
            return route
    return None

# Start the thread to continuously update the gps location and route status
def update():
    global gps_cache
    global route
    global route_pointer
    global active
    while True:
        if active:
            # Update GPS
            update_gps()
            print(gps_cache)
            # Update route if necessary
            print("[Route Management] Checking if update is needed...")
            next_beacon = route["beacons"][route_pointer]["at"]
            location = [gps_cache["lat"], gps_cache["lon"]]
            distance_away = distance(next_beacon, location)
            print(f"[Route Management] Beacon is {round(distance_away, 1)}m away")
            if distance_away < gps_accuracy + 10:
                arrived = route["beacons"][route_pointer]["do"] == "arrive"
                last_instruction = route_pointer + 1 >= len(route["beacons"])
                if arrived or last_instruction:
                    # Route has ended, deactivate
                    other_device = "none"
                    active = False
                    route_pointer = 0
                    route = None
                    print("[Route Management] Route Finished")
                else:
                    # On to the next instruction
                    other_device = "none"
                    route_pointer += 1
                    print("[Route Management] Beacon Reached, on to the next one")

updater = threading.Thread(target=update)
updater.setDaemon(True)
updater.start()

# Determine self-actuation pattern based off route information and gps location
side = "right" # by default, the primary device is on the right hand side
other_device = "none" # This governs what actuation pattern the other device should perform
def actuation_checker():
    global route
    global route_pointer
    global active
    global other_device
    while True:
        if active:
            print("[Actuation] Determining pattern...")
            # Where are we going?
            next_beacon = route["beacons"][route_pointer]["at"]
            # Where are we now?
            location = [gps_cache["lat"], gps_cache["lon"]]
            # How far away are we?
            distance_away = distance(next_beacon, location)
            # Determine actuation pattern
            if route["beacons"][route_pointer]["do"] == side:
                # It is this device's responsibility to actuate
                other_device = "none"
                if distance_away < 20: actuation.very_near()
                elif distance_away < 40: actuation.near()
                elif distance_away < 60: actuation.far()
                elif distance_away < 80: actuation.very_far()
                else: time.sleep(0.5)
            else:
                # It is the other device's responsibility to actuate
                if distance_away < 20: other_device = "very_near"
                elif distance_away < 40: other_device = "near"
                elif distance_away < 60: other_device = "far"
                elif distance_away < 80: other_device = "very_far"
                else: other_device = "none"
                time.sleep(1)

actuation_checker = threading.Thread(target=actuation_checker)
actuation_checker.setDaemon(True)
actuation_checker.start()

# Host a webpage for the user to control the device
app = Flask(__name__)

# User frontend
@app.route("/")
def control_centre():
    global route
    global active
    return render_template("app.html", route=display_route(), routes=list_routes())

# Request to update route
@app.route("/route", methods=["POST"])
def route_control():
    global active
    global route
    global route_pointer
    route_request = request.form["route"]
    if route_request == "none":
        # User wishes to cancel the route
        other_device = "none"
        active = False
        route_pointer = 0
        route = None
        print("[Route Management] Route Cancelled")
    else:
        # User wishes to start a new route
        route = get_route(route_request)
        route_pointer = 0
        active = True
        print("[Route Management] Route Activated")
    # Redirect user back to the control centre
    return redirect(url_for("control_centre"))

# Request to create route
@app.route("/route/create", methods=["POST"])
def route_creation():
    route_start = request.form["start"]
    route_end = request.form["end"]
    route_name = request.form["name"]
    # Fill blank fields with the current GPS location
    if route_start == "" or route_end == "":
        gps = where_am_i()
        if route_start == "": route_start = str(gps["latitude"]) + "," + str(gps["longitude"])
        if route_end == "": route_end = str(gps["latitude"]) + "," + str(gps["longitude"])
    # Perform validation
    if not validate_coord(route_start):
        return redirect(url_for("error", msg="Starting coordinates are invalid"))
    if not validate_coord(route_end):
        return redirect(url_for("error", msg="Ending coordinates are invalid"))
    if not validate(route_name):
        return redirect(url_for("error", msg="Name of route must only contain letters, numbers and underscores and can't be empty"))
    # Use the directions library to obtain a route
    new_route = {
        "name": route_name,
        "beacons": directions.beacons(route_start, route_end),
    }
    # Write the route to a file
    print("[Route Creation] Saving route...")
    file_name = f"routes/{route_name.lower()}.json"
    f = open(file_name, "w")
    f.write(json.dumps(new_route, indent=4))
    f.close()
    # Redirect user back to control centre
    print("[Route Creation] Completed")
    return redirect(url_for("control_centre"))

@app.route("/error/<msg>")
def error(msg):
    return render_template("error.html", msg=msg)

if __name__ == "__main__":
    open_command_centre()
    app.run(host="0.0.0.0")
