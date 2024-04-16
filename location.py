# A library that attempts to predict location based on patchy gps data
import json
import math

def direction_from_coordinates(lat1, lon1, lat2, lon2):
    """Calculate the direction from two sets of latitude and longitude coordinates."""
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Calculate differences in longitude and latitude
    delta_lon = lon2_rad - lon1_rad
    
    # Calculate direction angle
    y = math.sin(delta_lon) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon)
    angle_rad = math.atan2(y, x)
    
    # Convert angle from radians to degrees
    angle_degrees = math.degrees(angle_rad)
    
    # Ensure angle is between 0 and 360 degrees
    if angle_degrees < 0:
        angle_degrees += 360
    
    return angle_degrees

def move_coordinate(lat, lon, bearing_degrees, distance_km):
    """Move a coordinate along a bearing for a given distance."""
    # Radius of the Earth in kilometers
    earth_radius_km = 6371.0
    
    # Convert latitude and longitude from degrees to radians
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    
    # Convert bearing from degrees to radians
    bearing_rad = math.radians(bearing_degrees)
    
    # Calculate the new latitude using the formula: new = old + (distance / Earth radius) * (cos(bearing))
    new_lat_rad = lat_rad + (distance_km / earth_radius_km) * math.cos(bearing_rad)
    
    # Calculate the new longitude using the formula: new = old + (distance / radius) * (sin(bearing) / cos(latitude))
    new_lon_rad = lon_rad + (distance_km / earth_radius_km) * math.sin(bearing_rad) / math.cos(lat_rad)
    
    # Convert new latitude and longitude from radians to degrees
    new_lat = math.degrees(new_lat_rad)
    new_lon = math.degrees(new_lon_rad)
    
    return new_lat, new_lon

def interpolate_gps(latest_gps_coordinates, latest_gps_ago, speed, next_beacon):
    # Work out the direction the user should be going in (when heading towards the next beacon)
    lat, lon = latest_gps_coordinates
    bearing = direction_from_coordinates(lat, lon, next_beacon[0], next_beacon[1])
    
    # Guess how far you've travelled since the last GPS update
    travelled = (speed / 1000) * latest_gps_ago

    # Use these estimations to guess where the user would be
    return move_coordinate(*latest_gps_coordinates, bearing, travelled)
