from math import radians, sin, cos, sqrt, atan2

def haversine(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    # Radius of the Earth in kilometers (change it to 3958.8 for miles)
    radius = 6371.0

    # Calculate the distance
    distance = radius * c

    return distance

# Example usage
lat1, lon1 = 37.7749, -122.4194  # San Francisco, CA
lat2, lon2 = 34.0522, -118.2437  # Los Angeles, CA

distance = haversine(lat1, lon1, lat2, lon2)
print(f"The distance between the two coordinates is {distance:.2f} kilometers.")
