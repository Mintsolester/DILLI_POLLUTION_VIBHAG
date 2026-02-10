import pandas as pd
from datetime import datetime, timedelta

REQUIRED_HOURS_FOR_FEATURES = 72
MAX_GAP_HOURS = 24

def validate_completeness(df: pd.DataFrame):
    """
    Checks if the dataframe has enough hourly data to generate features.
    Need enough history to compute lag_72.
    """
    if df.empty:
        return False, "No data fetched."
        
    # Resample to hourly first to see gaps
    # We aggregate by median
    if 'pm25' not in df.columns:
        return False, "Missing 'pm25' column data."
        
    hourly_df = df.resample('h')['pm25'].median()
    
    # Check total span
    start_time = hourly_df.index.min()
    end_time = hourly_df.index.max()
    duration = (end_time - start_time).total_seconds() / 3600
    
    if duration < REQUIRED_HOURS_FOR_FEATURES:
        return False, f"Insufficient history duration. Need {REQUIRED_HOURS_FOR_FEATURES}h, got {duration:.1f}h."
    
    # Check completeness in the last 72 hours specifically relative to NOW?
    # Actually relative to the last available timestamp. 
    # If the last timestamp is 10 hours ago, we are predicting for 10 hours ago, which is useless?
    # We want to predict for NOW + Forecast Horizon.
    # So we need data up to NOW.
    
    now_local = pd.Timestamp.now(tz='Asia/Kolkata')
    last_data_point = df.index.max()
    
    # If data is stale (provider hasn't updated in > 2 hours)
    lag_since_update = (now_local - last_data_point).total_seconds() / 3600
    if lag_since_update > 4: # Allow some delay
        return False, f"Data is stale. Last update was {lag_since_update:.1f} hours ago."
        
    # Count valid hours in the window of interest (Last 72 hours from end_time)
    # We take the tail 72 hours
    mask = hourly_df.index >= (end_time - timedelta(hours=REQUIRED_HOURS_FOR_FEATURES))
    window = hourly_df[mask]
    
    missing_hours = window.isna().sum()
    total_hours = len(window)
    
    if missing_hours > (total_hours * 0.3): # Allow 30% missing? Maybe less.
        return False, f"Too much missing data in last 72h ({missing_hours} missing)."

    # Check for contiguous gaps > MAX_GAP_HOURS
    # Identify gaps in the index (which is resampled, so gaps are NaNs)
    is_nan = window.isna()
    # Group consecutive NaNs
    gap_lengths = is_nan.groupby((~is_nan).cumsum()).sum()
    max_gap = gap_lengths.max()
    
    if max_gap > MAX_GAP_HOURS:
        return False, f"Found a data gap of {max_gap} hours, limit is {MAX_GAP_HOURS}."
        
    return True, "Data sufficient."
