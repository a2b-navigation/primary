import requests as r
import json

access_token = "pk.eyJ1IjoibWFnbmV0aWNub3J0aCIsImEiOiJjbG02OTdocW8xdzBlM3BzNm96bnA0NDdrIn0.vTO9vpyc49SgOAsAA1uqnA"

# Given starting and ending coordinates, generate beacons to go from start to end
def beacons(start, end):
    start = ",".join(start.replace(", ", ",").split(",")[::-1])
    end = ",".join(end.replace(", ", ",").split(",")[::-1])
    print("[Route Creation] Sending request to mapbox...")
    raw = r.get(f"https://api.mapbox.com/directions/v5/mapbox/cycling/{start};{end}?geometries=geojson&steps=true&access_token={access_token}")
    data = json.loads(raw.text)
    print(data)
    
    # Obtain beacons
    print("[Route Creation] Generating beacons...")
    beacons = []
    instructions = data["routes"][0]["legs"][0]["steps"]
    for i in instructions:
        i = i["maneuver"]
        match i["type"]:
            case "depart": do = "depart"
            case "arrive": do = "arrive"
            case other: do = i["modifier"]
        i = {"do": do, "at": i["location"][::-1]}
        beacons.append(i)

    # Return the result
    return beacons
