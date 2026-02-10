import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.openaq.org/v3"
SENSOR_ID = 12234787 # The one we are using

def get_headers():
    api_key = os.environ.get("OPENAQ_API_KEY")
    if api_key:
        return {"X-API-Key": api_key}
    return {}

def check_sensor_params():
    # Get sensor details directly? Or parent location?
    # v3/sensors/{id} gives details about that specific sensor (one parameter).
    # We need to find the parent location and see what OTHER sensors it has.
    
    url = f"{BASE_URL}/sensors/{SENSOR_ID}"
    print(f"Fetching sensor details: {url}")
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        data = response.json()
        
        # In v3, a 'sensor' is a specific parameter stream.
        # It should have a 'locations_id' or similar link.
        results = data.get('results', [])
        if not results:
            # Maybe it returns dict directly?
            results = [data] if 'id' in data else []
            
        if not results:
            print("No sensor details found.")
            return

        sensor_data = results[0]
        # v3 structure: check parent location
        # Usually 'sensors' endpoint returns list.
        # Let's check keys.
        # print(sensor_data.keys()) 
        
        parent_loc_id = None
        # Try to find location link
        # It seems v3 'sensors' response might contain 'owners', 'locations' etc.
        
        # Let's just fetch the location if we can find the ID.
        pass
        
    except Exception as e:
        print(e)

    # Alternative: Search locations by ID if we knew it, or search by coordinates of this sensor?
    # Actually, we can just query /locations with the ID if we have it.
    # But wait, earlier log showed: "Checking Sensor 12234787 at R K Puram, Delhi - DPCC..."
    # We can search for this name "R K Puram" to get the Location ID.
    
    print("Searching for location 'R K Puram'...")
    url = f"{BASE_URL}/locations"
    params = {
        "iso": "IN",
        "bbox": "76.8,28.4,77.3,28.9",
        "limit": 100
    }
    
    response = requests.get(url, headers=get_headers(), params=params)
    results = response.json().get('results', [])
    
    for loc in results:
        if "R K Puram" in loc.get('name', ''):
            print(f"Found Location: {loc.get('name')} (ID: {loc.get('id')})")
            print("Available Sensors/Parameters:")
            for s in loc.get('sensors', []):
                print(f"  - {s.get('parameter', {}).get('name')} (ID: {s.get('id')})")
            return

if __name__ == "__main__":
    check_sensor_params()
