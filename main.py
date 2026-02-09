import json, requests, unicodedata



def cords(city):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": city,
        "format": "json",
        "limit": 1
    }
    headers = {
        "User-Agent": "YourAppName/1.0"  # IMPORTANT
    }

    r = requests.get(url, params=params, headers=headers)
    data = r.json()

    if not data:
        return None

    return float(data[0]["lat"]), float(data[0]["lon"])

latitude, longitude = cords("77388-4613")
radius = 5000

query = f"""
[out:json];
(
  node["amenity"="restaurant"](around:{radius},{latitude},{longitude});
  way["amenity"="restaurant"](around:{radius},{latitude},{longitude});
);
out center;
"""

overpass_url = 'http://overpass-api.de/api/interpreter'
response = requests.get(overpass_url, params={'data': query})

# # Don't convert to string yet! Keep it as a dictionary
data = response.json()
 
# # Now you can print it nicely if you want
# print(json.dumps(data, indent=2))

# The API returns 'elements' not 'nodes'!
for i, element in enumerate(data['elements']):
    print(f"Restaurant #{i+1}:")
    
    # Get tags (where all the info is)
    tags = element.get('tags', {})
    
    # Get name
    name = tags.get('name', 'UNNAMED')
    print(f"  Name: {name}")
    
    # Get coordinates (different for nodes vs ways)
    if element['type'] == 'node':
        lat = element['lat']
        lon = element['lon']
    elif 'center' in element:
        lat = element['center']['lat']
        lon = element['center']['lon']
    
    print(f"  Coordinates: {lat}, {lon}")
    
    # Get other info
    cuisine = tags.get('cuisine', 'Not specified')
    print(f"  Cuisine: {cuisine}")
    
    if 'addr:street' in tags:
        print(f"  Address: {tags['addr:street']}")
    
    if 'phone' in tags:
        print(f"  Phone: {tags['phone']}")

    if 'email' in tags:
        print(f"  Email: {tags['email']}")

    if 'website' in tags:
        print(f"  Website: {tags['website']}")

    if 'payment' in tags:
        print(f"Payment Methods: {tags['payment']}")

    if 'opening_hours' in tags:
        print(f"Opening Hours {tags['opening_hours']}")
    
    print()