import requests
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.openaq.org/v3"
API_KEY = os.environ.get("OPENAQ_API_KEY")

def get_headers():
    if API_KEY:
        return {"X-API-Key": API_KEY}
    return {}

def find_location_sensors():
    # 1. Search for R K Puram location to get ID (or use known ID if we had it, but searching is safer)
    print("Searching for 'R K Puram' in Delhi...")
    url = f"{BASE_URL}/locations"
    params = {
        "limit": 10,
        "page": 1,
        "bbox": "76.842520,28.404620,77.347652,28.879322" # Delhi bbox roughly
    }
    
    # Alternatively, just list sensors and filter by name if location search is fuzzy
    # But v3 has a good locations endpoint.
    
    # Let's try to get the sensors for the location ID we implicitly used before?
    # In fetch_history, we used sensor IDs directly.
    # PM2.5 ID was 12234787. Let's get that sensor details to find its Location ID.
    
    # known_sensor_id = 12234787
    # print(f" getting details for known sensor {known_sensor_id}...")
    # resp = requests.get(f"{BASE_URL}/sensors/{known_sensor_id}", headers=get_headers())
    
    # Direct search for location might be easier if we know it's R K Puram.
    # Let's search locations directly.
    print("Searching for 'R K Puram' location...")
    url = f"{BASE_URL}/locations"
    # Using small bbox around Delhi to find it
    params = {
        "limit": 100,
        "page": 1,
        "bbox": "77.10,28.50,77.25,28.65" # Tighter bbox around South Delhi (RK Puram)
    }
    
    resp = requests.get(url, headers=get_headers(), params=params)
    if resp.status_code != 200:
        print(f"Error searching locations: {resp.status_code}")
        return
        
    locations = resp.json().get("results", [])
    target_location = None
    
    for loc in locations:
        name = loc.get("name", "").lower()
        if "puram" in name or "r.k. puram" in name:
            target_location = loc
            print(f"Found candidate: {loc.get('name')} (ID: {loc.get('id')})")
            # Break on first good match or list?
            # R K Puram usually has name like "R K Puram" or similar.
            break
            
    if not target_location:
        print("Could not find R K Puram location in search results. Trying broader search.")
        return

    location_id = target_location.get("id")
    
    if not location_id:
        print("Could not determine Location ID.")
        return

    # 2. List all sensors for this location
    print(f"Listing all sensors for Location {location_id}...")
    url = f"{BASE_URL}/locations/{location_id}/sensors"
    resp = requests.get(url, headers=get_headers())
    
    if resp.status_code == 200:
        sensors = resp.json().get("results", [])
        print(f"Found {len(sensors)} sensors.")
        
        data = []
        for s in sensors:
            param = s.get("parameter", {}).get("name")
            s_id = s.get("id")
            name = s.get("name")
            data.append({"id": s_id, "parameter": param, "name": name})
            
        df = pd.DataFrame(data)
        print(df)
        df.to_csv("r_k_puram_sensors.csv", index=False)
    else:
        print(f"Error: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    find_location_sensors()
