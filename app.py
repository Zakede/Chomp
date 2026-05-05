from flask import Flask, render_template, request, jsonify
import sqlite3
import requests
from datetime import datetime
import time

app = Flask(__name__)


def init_database(db_name="restaurants.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS searches (
            search_id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            radius INTEGER NOT NULL,
            center_lat REAL NOT NULL,
            center_lon REAL NOT NULL,
            timestamp TEXT NOT NULL,
            total_results INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS restaurants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            search_id INTEGER NOT NULL,
            osm_id TEXT,
            name TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            cuisine TEXT,
            address TEXT,
            phone TEXT,
            email TEXT,
            website TEXT,
            payment TEXT,
            FOREIGN KEY (search_id) REFERENCES searches (search_id)
        )
    """)

    conn.commit()
    conn.close()


def save_search_to_db(city, radius, latitude, longitude, total_results, db_name="restaurants.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO searches (city, radius, center_lat, center_lon, timestamp, total_results)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (city, radius, latitude, longitude, timestamp, total_results))

    search_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return search_id


def save_restaurants_to_db(search_id, restaurants, db_name="restaurants.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    for restaurant in restaurants:
        osm_id = f"{restaurant['latitude']}_{restaurant['longitude']}"

        try:
            cursor.execute("""
                INSERT INTO restaurants
                (search_id, osm_id, name, latitude, longitude, cuisine, address, phone, email, website, payment)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                search_id,
                osm_id,
                restaurant['name'],
                restaurant['latitude'],
                restaurant['longitude'],
                restaurant.get('cuisine'),
                restaurant.get('address'),
                restaurant.get('phone'),
                restaurant.get('email'),
                restaurant.get('website'),
                restaurant.get('payment')
            ))
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()


def get_coordinates(city):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": city,
        "format": "json",
        "limit": 1
    }
    headers = {
        "User-Agent": "Chomp/1.0"
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        if not data:
            return None

        return float(data[0]["lat"]), float(data[0]["lon"])

    except requests.exceptions.RequestException as e:
        print(f"Error fetching coordinates: {e}")
        return None


def fetch_restaurants_from_overpass(latitude, longitude, radius, max_retries=5):
    query = f"""
    [out:json];
    (
      node["amenity"="restaurant"](around:{radius},{latitude},{longitude});
      way["amenity"="restaurant"](around:{radius},{latitude},{longitude});
    );
    out center;
    """

    overpass_url = 'https://overpass-api.de/api/interpreter'

    for attempt in range(max_retries):
        try:
            print(f"Fetching data (attempt {attempt + 1}/{max_retries})...")

            response = requests.get(
                overpass_url,
                params={'data': query},
                headers={'User-Agent': 'MyRestoApp/1.0'},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                if 'elements' in data:
                    return data

            print(f"Attempt {attempt + 1} failed with status {response.status_code}")

            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                print(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)

        except requests.exceptions.Timeout:
            print(f"Request timed out on attempt {attempt + 1}")
            if attempt < max_retries - 1:
                time.sleep((attempt + 1) * 5)

        except Exception as e:
            print(f"Error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep((attempt + 1) * 5)

    return None


def parse_restaurant_data(elements):
    restaurants = []

    for element in elements:
        tags = element.get('tags', {})

        if element['type'] == 'node':
            lat = element.get('lat')
            lon = element.get('lon')
        elif 'center' in element:
            lat = element['center'].get('lat')
            lon = element['center'].get('lon')
        else:
            continue

        restaurant = {
            'name': tags.get('name', 'Unnamed Restaurant'),
            'latitude': lat,
            'longitude': lon,
            'cuisine': tags.get('cuisine'),
            'address': tags.get('addr:street'),
            'phone': tags.get('phone'),
            'email': tags.get('email'),
            'website': tags.get('website'),
            'payment': tags.get('payment')
        }

        restaurants.append(restaurant)

    return restaurants


def calculate_statistics(restaurants):
    total = len(restaurants)

    stats = {
        'total': total,
        'with_phone': sum(1 for r in restaurants if r.get('phone')),
        'with_email': sum(1 for r in restaurants if r.get('email')),
        'with_website': sum(1 for r in restaurants if r.get('website')),
        'with_cuisine': sum(1 for r in restaurants if r.get('cuisine')),
        'with_address': sum(1 for r in restaurants if r.get('address'))
    }

    return stats


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        location = data.get('location')
        radius = int(data.get('radius', 5000))

        if not location:
            return jsonify({'error': 'Location is required'}), 400

        if radius < 100 or radius > 50000:
            return jsonify({'error': 'Radius must be between 100 and 50000 meters'}), 400

        coords = get_coordinates(location)
        if not coords:
            return jsonify({'error': f'Could not find coordinates for {location}'}), 404

        latitude, longitude = coords

        overpass_data = fetch_restaurants_from_overpass(latitude, longitude, radius)
        if not overpass_data:
            return jsonify({'error': 'Failed to fetch restaurant data'}), 500

        restaurants = parse_restaurant_data(overpass_data.get('elements', []))
        stats = calculate_statistics(restaurants)

        try:
            search_id = save_search_to_db(location, radius, latitude, longitude, stats['total'])
            save_restaurants_to_db(search_id, restaurants)
            print(f"✓ Saved search to database with ID: {search_id}")
        except Exception as db_error:
            print(f"Warning: Failed to save to database: {db_error}")

        return jsonify({
            'restaurants': restaurants,
            'stats': stats,
            'location': {
                'name': location,
                'latitude': latitude,
                'longitude': longitude
            }
        })

    except ValueError:
        return jsonify({'error': 'Invalid input data'}), 400
    except Exception as e:
        print(f"Error in search endpoint: {e}")
        return jsonify({'error': 'An unexpected error occurred'}), 500


if __name__ == '__main__':
    init_database()
    print("✓ Database initialized")
    app.run(debug=True)
