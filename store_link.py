import requests
from bs4 import BeautifulSoup
import urllib.parse
import time

def get_google_maps_place_url(name, lat, lon):
    """
    Method 1: Use Google Maps search and extract the redirect URL
    """
    # Create a search URL
    search_query = f"{name}"
    encoded_query = urllib.parse.quote(search_query)
    search_url = f"https://www.google.com/maps/search/{encoded_query}/@{lat},{lon},17z"
    
    # Set up headers to mimic a browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Make request and follow redirects
        response = requests.get(search_url, headers=headers, allow_redirects=True)
        
        # The final URL after redirect is what we want
        final_url = response.url
        
        return final_url
    except Exception as e:
        print(f"Error: {e}")
        return search_url

# Test it
name = "Willie's Grill and Icehouse"
lat = 30.0870329
lon = -95.5236512

result = get_google_maps_place_url(name, lat, lon)
print(f"Result URL: {result}")