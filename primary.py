"""
Duties of the primary device:
1. Query GPS location and store it [X]
2. Serve a website for the user to interact with [X]
3. Manage the route [X]
4. Create routes [ ]
5. Actuate the primary server to issue commands based off route and gps [ ]
5. Allow the secondary server to receive commands based off route and gps [ ]
"""

from flask import *
import subprocess
import threading
import json
import time
import os

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
def update_gps():
    global gps_cache
    data = where_am_i()
    gps_cache = {"lat": data["latitude"], "lon": data["longitude"]}
    accuracy = round(data["accuracy"], 1)
    print(f"[GPS] Cache updated with accuracy of {accuracy}m")

# Begin execution!

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
    while True:
        if active:
            update_gps()
            print(gps_cache)

updater = threading.Thread(target=update)
updater.start()

# Find the initial gps location
print("[GPS] Aquiring initial GPS location")
update_gps()

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

if __name__ == "__main__":
    open_command_centre()
    app.run(host="0.0.0.0")
