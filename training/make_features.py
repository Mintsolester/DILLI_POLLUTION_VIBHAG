import pandas as pd
import numpy as np
import os
import sys

# Add parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.storage import load_processed_data

FEATURES_DIR = os.path.dirname(os.path.abspath(__file__))
FEATURES_PATH = os.path.join(FEATURES_DIR, "features.parquet")

def create_features():
    print("Loading processed data...")
    try:
        df = load_processed_data()
    except FileNotFoundError:
        print("Processed data not found. Run build_hourly.py first.")
        return

    print("Generating features...")
    
    # Feature Engineering
    # 1. Time Features
    df['hour'] = df.index.hour
    df['day_of_week'] = df.index.dayofweek
    df['month'] = df.index.month
    
    # 2. Feature Engineering for ALL columns
    # We want to use past N hours to predict future.
    
    # Identify target columns (everything except date/time features)
    # We assume all numeric columns in df are potential features/targets
    feature_targets = [c for c in df.columns if c not in ['hour', 'day_of_week', 'month']]
    
    print(f"Generating features for: {feature_targets}")

    for col in feature_targets:
        # Lags
        # For Pollutants: Deep history (72h) is useful for periodic patterns
        # For Meteorology: Maybe 24h is enough?
        # Let's standardize to 72h for Pollutants, 24h for Met to save space/time?
        # Or just 72h for everything to be safe.
        # Given we have 28k rows, 72 cols * 10 vars = 720 features. XGBoost handles it fine.
        
        # Heuristic: 
        # Main pollutants (pm25, pm10, no2, etc): 72 lags
        # Met (wind, temp, humidity): 24 lags
        
        is_met = col in ['wind_speed', 'temperature', 'humidity']
        max_lag = 24 if is_met else 72
        
        lags = list(range(1, max_lag + 1))
        for lag in lags:
            col_name = f'lag_{lag}' if col == 'pm25' else f'{col}_lag_{lag}' # Keep compat for PM2.5
            df[col_name] = df[col].shift(lag)
            
        # Rolling Stats (6, 12, 24)
        for window in [6, 12, 24]:
            roll = df[col].shift(1).rolling(window=window)
            
            mean_name = f'rolling_mean_{window}' if col == 'pm25' else f'{col}_rolling_mean_{window}'
            std_name = f'rolling_std_{window}' if col == 'pm25' else f'{col}_rolling_std_{window}'
            
            df[mean_name] = roll.mean()
            df[std_name] = roll.std()
        
    # Drop rows with NaNs (caused by shifting/rolling)
    # We lose the first 72+ data points, which is fine.
    # Also if there were gaps in data, we lose more.
    initial_shape = df.shape
    df_clean = df.dropna()
    print(f"Dropped NaNs: {initial_shape[0] - df_clean.shape[0]} rows lost.")
    
    # Save
    df_clean.to_parquet(FEATURES_PATH)
    print(f"Saved features to {FEATURES_PATH}")
    print(f"Final shape: {df_clean.shape}")

if __name__ == "__main__":
    create_features()
