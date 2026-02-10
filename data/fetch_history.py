import argparse
import requests
import pandas as pd
import time
from datetime import datetime, timedelta, timezone
import os
import sys
from dotenv import load_dotenv

# Add parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.storage import save_raw_data

# Load environment variables
load_dotenv()

BASE_URL = "https://api.openaq.org/v3"

def get_headers():
    # 1. Try Environment Variable (Local .env)
    api_key = os.environ.get("OPENAQ_API_KEY")
    
    # 2. Try Streamlit Secrets (Cloud Deployment)
    if not api_key:
        try:
            import streamlit as st
            # Secrets can be dict-like or nested
            if "OPENAQ_API_KEY" in st.secrets:
                api_key = st.secrets["OPENAQ_API_KEY"]
        except (ImportError, FileNotFoundError, AttributeError):
            pass # Streamlit not installed or not running in a context with secrets

    if api_key:
        return {"X-API-Key": api_key}
        
    print("Warning: No OPENAQ_API_KEY found in environment variables or Streamlit secrets.")
    return {}

# Hardcoded Sensor IDs for R K Puram based on check_params.py
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

def fetch_sensor_data(sensor_id, parameter_name, days=400):
    print(f"Fetching {parameter_name} (Sensor {sensor_id})...")
    url = f"{BASE_URL}/sensors/{sensor_id}/measurements"
    
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    all_results = []
    chunk_size_days = 30
    current_start = start_date
    
    while current_start < end_date:
        current_end = min(current_start + timedelta(days=chunk_size_days), end_date)
        
        params = {
            "datetime_from": current_start.isoformat(),
            "datetime_to": current_end.isoformat(),
            "limit": 1000,
            "page": 1
        }
        
        print(f"  Fetching {current_start.date()} to {current_end.date()}...")
        
        while True:
            try:
                response = requests.get(url, headers=get_headers(), params=params, timeout=20)
                if response.status_code != 200:
                    print(f"  Error {response.status_code}: {response.text}")
                    break
                    
                data = response.json()
                results = data.get("results", [])
                
                if not results:
                    break
                    
                all_results.extend(results)
                
                if len(results) < params["limit"]:
                    break
                
                params["page"] += 1
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  Exception: {e}")
                break
        
        current_start = current_end
        
    if not all_results:
        print(f"No data for {parameter_name}.")
        return pd.DataFrame()
        
    df = pd.DataFrame(all_results)
    
    # Normalize date
    if 'datetime' in df.columns:
        df['date_utc'] = df['datetime'].apply(lambda x: x.get('utc') if isinstance(x, dict) else None)
    elif 'period' in df.columns:
         df['date_utc'] = df['period'].apply(lambda x: x.get('datetimeTo', {}).get('utc') if isinstance(x, dict) else None)
    elif 'date' in df.columns:
        df['date_utc'] = df['date'].apply(lambda x: x.get('utc') if isinstance(x, dict) else None)
        
    if 'date_utc' not in df.columns:
         return pd.DataFrame()

    df['date_utc'] = pd.to_datetime(df['date_utc'])
    df['value'] = df['value']
    
    # Keep only what we need
    df = df[['date_utc', 'value']].rename(columns={'value': parameter_name})
    
    # Drop duplicates
    df = df.drop_duplicates(subset=['date_utc'])
    df = df.set_index('date_utc').sort_index()
    
    print(f"  Fetched {len(df)} records for {parameter_name}.")
    return df

def fetch_historical_data(days=400):
    combined_df = pd.DataFrame()
    
    for param, sensor_id in SENSOR_CONFIG.items():
        df_param = fetch_sensor_data(sensor_id, param, days=days)
        if df_param.empty:
            continue
            
        if combined_df.empty:
            combined_df = df_param
        else:
            # Join on index (timestamp)
            # Use outer join to keep all timestamps? Or inner to verify overlap?
            # Outer is safer, we can interpolate later.
            combined_df = combined_df.join(df_param, how='outer')
    
    if combined_df.empty:
        print("No data fetched for any parameter.")
        return

    # Reset index to make it a column for saving
    combined_df = combined_df.reset_index()
    
    # Ensure date_utc is preserved
    print(f"Total merged records: {len(combined_df)}")
    print(f"Columns: {combined_df.columns}")
    
    save_raw_data(combined_df)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch historical AQI data.")
    parser.add_argument("--days", type=int, default=400, help="Number of days to fetch.")
    args = parser.parse_args()
    
    fetch_historical_data(days=args.days)
