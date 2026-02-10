import pandas as pd
import os
import sys

# Add parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.storage import load_raw_data, save_processed_data

def process_data():
    print("Loading raw data...")
    try:
        df = load_raw_data()
    except FileNotFoundError:
        print("Raw data not found. Please run fetch_history.py first.")
        return

    print(f"Raw shape: {df.shape}")
    
    # Ensure datetime
    df['date_utc'] = pd.to_datetime(df['date_utc'])
    
    # Drop invalid values if possible, but now we have multiple cols
    # We can clip negatives to 0 for specific columns
    if 'pm25' in df.columns:
        df = df[df['pm25'] >= 0]
    if 'wind_speed' in df.columns:
        df.loc[df['wind_speed'] < 0, 'wind_speed'] = 0 # outliers?
    if 'temperature' in df.columns:
        # Temp can be negative (though unlikely in Delhi), but -999 usually error
        df = df[df['temperature'] > -50]
    
    # Convert to Asia/Kolkata
    # date_utc is timezone aware (UTC)
    df['date_local'] = df['date_utc'].dt.tz_convert('Asia/Kolkata')
    
    # Set index
    df = df.set_index('date_local')
    
    # Sort
    df = df.sort_index()
    
    # Resample to Hourly
    print("Resampling to hourly frequency...")
    
    # Define aggregation rules
    # Pollutants -> median (robust to outliers)
    # Meteorology -> mean (vector average approximation)
    
    # Check which columns exist
    cols = df.columns
    agg_dict = {}
    
    pollutants = ['pm25', 'pm10', 'no2', 'so2', 'co', 'ozone']
    meteorology = ['wind_speed', 'temperature', 'humidity']
    
    for col in cols:
        if col in pollutants:
            agg_dict[col] = 'median'
        elif col in meteorology:
            agg_dict[col] = 'mean'
    
    if not agg_dict:
        print("No valid parameter columns found.")
        return

    hourly_df = df.resample('h').agg(agg_dict)
    
    # Interpolate short gaps (<= 2 hours)
    hourly_df_interpolated = hourly_df.interpolate(method='linear', limit=2)
    
    # Add metadata
    # Just creating a flag if ANY value was interpolated?
    # Keeping it simple for now, just saving the dataframe.
    
    print(f"Processed shape: {hourly_df_interpolated.shape}")
    print(f"Date range: {hourly_df_interpolated.index.min()} to {hourly_df_interpolated.index.max()}")
    print("Missing values per column:")
    print(hourly_df_interpolated.isna().sum())
    
    save_processed_data(hourly_df_interpolated)

if __name__ == "__main__":
    process_data()
