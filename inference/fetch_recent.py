import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
import time
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.fetch_history import get_headers, BASE_URL

REQUIRED_HOURS = 75

# Hardcoded Sensor IDs for R K Puram (Sync with fetch_history.py)
# Hardcoded Sensor IDs for R K Puram (Verified via find_sensors.py)
SENSOR_CONFIG = {
    "pm25": 12234787,
    "pm10": 12234786,
    "no2": 12234784,
    "so2": 12234789,
    "co": 12234782,
    "ozone": 12234785,
    "wind_speed": 14340715,
    "temperature": 12234790,
    "humidity": 12234788
}

REQUIRED_HOURS = 75

def fetch_sensor_recent(sensor_id, parameter_name, hours=REQUIRED_HOURS):
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(hours=hours)
    
    # print(f"Fetching {parameter_name} (Sensor {sensor_id})...")
    url = f"{BASE_URL}/sensors/{sensor_id}/measurements"
    
    params = {
        "datetime_from": start_date.isoformat(),
        "datetime_to": end_date.isoformat(),
        "limit": 1000,
        "page": 1,
        "order_by": "datetime", 
        "sort": "asc"
    }
    
    try:
        response = requests.get(url, headers=get_headers(), params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                return pd.DataFrame()
                
            df = pd.DataFrame(results)
            
            # Extract date
            if 'datetime' in df.columns:
                df['date_utc'] = df['datetime'].apply(lambda x: x.get('utc') if isinstance(x, dict) else None)
            elif 'period' in df.columns:
                 df['date_utc'] = df['period'].apply(lambda x: x.get('datetimeTo', {}).get('utc') if isinstance(x, dict) else None)
            elif 'date' in df.columns:
                df['date_utc'] = df['date'].apply(lambda x: x.get('utc') if isinstance(x, dict) else None)

            if 'date_utc' not in df.columns:
                return pd.DataFrame()
                
            df['date_utc'] = pd.to_datetime(df['date_utc'])
            
            # Simple clean
            df['value'] = df['value']
            # We don't filter negatives strictly for all params here, handle in processing
            
            # Keep necessary cols
            df = df[['date_utc', 'value']].rename(columns={'value': parameter_name})
            
            # Convert to Local Time
            df['date_local'] = df['date_utc'].dt.tz_convert('Asia/Kolkata')
            df = df.set_index('date_local').sort_index()
            
            # Drop duplicates
            df = df[~df.index.duplicated(keep='first')]
            
            # Drop date_utc to avoid join issues (it's redundant with index)
            df = df.drop(columns=['date_utc'], errors='ignore')
            
            return df
            
        else:
            print(f"Error fetching {parameter_name}: {response.status_code}")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"Exception fetching {parameter_name}: {e}")
        return pd.DataFrame()

def fetch_recent_data(hours=REQUIRED_HOURS):
    """
    Fetches the last N hours of data + buffer from OpenAQ v3 for all configured sensors.
    Returns specific columns: pm25, wind_speed, temperature
    """
    combined_df = pd.DataFrame()
    
    print(f"Fetching recent data for last {hours} hours...")
    
    for param, sensor_id in SENSOR_CONFIG.items():
        df_param = fetch_sensor_recent(sensor_id, param, hours=hours)
        if df_param.empty:
            print(f"Warning: No recent data for {param}.")
            continue
            
        if combined_df.empty:
            combined_df = df_param
        else:
            # Join on index (timestamp)
            # using outer join to preserve timepoints, interpolate later
            combined_df = combined_df.join(df_param, how='outer')
            
    if combined_df.empty:
        print("No recent data fetched for any parameter.")
        return pd.DataFrame()

    # Determine if we have enough coverage?
    # validators.py will check completeness.
    # Just return whatever we have.
    
    return combined_df

if __name__ == "__main__":
    df = fetch_recent_data()
    print(df.tail())
