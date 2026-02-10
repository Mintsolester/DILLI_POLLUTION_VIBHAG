import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("OPENAQ_API_KEY")
HEADERS = {"X-API-Key": API_KEY} if API_KEY else {}
BASE_URL = "https://api.openaq.org/v3"

def explore_locations():
    url = f"{BASE_URL}/locations"
    params = {
        "limit": 100,
        "page": 1,
        "iso": "IN",
        # "bbox": "76.8,28.4,77.3,28.9" # Removing bbox for now
    }
    
    print(f"Fetching locations from {url} with params {params}...")
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            print(f"Found {len(results)} locations. Filtering for 'Delhi'...")
            for loc in results:
                name = loc.get('name', 'Unknown')
                if 'Delhi' in name or 'delhi' in name.lower():
                    print(f"ID: {loc.get('id')}, Name: {name}, Sensors: {len(loc.get('sensors', []))}")
                    # Print sensor details
                    for s in loc.get('sensors', []):
                        if s.get('parameter', {}).get('name') == 'pm25':
                            print(f"  - Sensor ID: {s.get('id')}, Param: pm25")
        else:
            print(response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    explore_locations()
