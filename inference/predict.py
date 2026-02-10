import pandas as pd
import numpy as np
import joblib
import os
import json
import sys
from datetime import timedelta

# Add parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
CONFIG_PATH = os.path.join(MODELS_DIR, "feature_config.json")

def load_model(target, horizon):
    path = os.path.join(MODELS_DIR, f"model_{target}_{horizon}h.pkl")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model for {target} ({horizon}h) not found. Have you trained it?")
    return joblib.load(path)
def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError("Feature config not found.")
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def preprocess_and_predict(recent_df, horizon, target_col='pm25'):
    """
    recent_df: DataFrame with datetime index.
    target_col: The pollutant to forecast (e.g., 'pm25', 'pm10', 'no2')
    Returns: DataFrame with index (future times) and 'predicted_{target}'
    """
    if recent_df.empty:
        return None, "Empty data provided."
        
    # 1. Resample to Hourly & Interpolate
    # We follow build_hourly.py logic
    
    # Define aggregation rules
    agg_dict = {}
    
    pollutants = ['pm25', 'pm10', 'no2', 'so2', 'co', 'ozone']
    meteorology = ['wind_speed', 'temperature', 'humidity']
    
    for col in recent_df.columns:
        if col in pollutants:
            agg_dict[col] = 'median'
        elif col in meteorology:
            agg_dict[col] = 'mean'
            
    if not agg_dict:
        return None, "No valid parameters found in input data."

    hourly_df = recent_df.resample('h').agg(agg_dict)
    
    # Interpolate
    # We allow generous interpolation for inference to be robust
    hourly_df = hourly_df.interpolate(method='linear', limit=24)
    df = hourly_df 
    
    # 2. Generate Features (Sync with make_features.py)
    # Time
    df['hour'] = df.index.hour
    df['day_of_week'] = df.index.dayofweek
    df['month'] = df.index.month
    
    # Feature Engineering for ALL columns present
    # We assume recent_df contains all the sensors we are tracking
    
    feature_targets = [c for c in df.columns if c not in ['hour', 'day_of_week', 'month']]
    new_features = {}
    
    for col in feature_targets:
        # Lags
        is_met = col in meteorology
        max_lag = 24 if is_met else 72
        
        lags = list(range(1, max_lag + 1))
        for lag in lags:
            col_name = f'lag_{lag}' if col == 'pm25' else f'{col}_lag_{lag}' # Keep compat
            new_features[col_name] = df[col].shift(lag)
            
        # Rolling Stats (6, 12, 24)
        for window in [6, 12, 24]:
            roll = df[col].shift(1).rolling(window=window)
            
            mean_name = f'rolling_mean_{window}' if col == 'pm25' else f'{col}_rolling_mean_{window}'
            std_name = f'rolling_std_{window}' if col == 'pm25' else f'{col}_rolling_std_{window}'
            
            new_features[mean_name] = roll.mean()
            new_features[std_name] = roll.std()
            
    # Concat all new features at once
    if new_features:
        features_df = pd.DataFrame(new_features, index=df.index)
        df = pd.concat([df, features_df], axis=1)
        
    # 3. Select Last Row
    last_row = df.iloc[[-1]].copy()
    
    # Check config
    try:
        config = load_config()
        required_features = config['features']
    except FileNotFoundError:
        return None, "Model feature config not found. Please train models first."
    
    # Ensure all features exist
    # Missing features usually mean a sensor is down or not fetched
    missing = [f for f in required_features if f not in last_row.columns]
    if missing:
        # We can try to fill with 0 or fallback?
        # For now, strict failure is safer than garbage prediction
        return None, f"Missing features for model: {missing[:3]}... Input data might be incomplete."
        
    X_input = last_row[required_features]
    
    # 4. Predict
    try:
        model = load_model(target_col, horizon)
    except FileNotFoundError as e:
        return None, str(e)
        
    preds = model.predict(X_input)[0] 
    
    # 5. Format Output
    last_time = last_row.index[0]
    future_times = [last_time + timedelta(hours=i) for i in range(1, horizon+1)]
    
    result_df = pd.DataFrame({
        'date': future_times,
        f'predicted_{target_col}': preds
    })
    result_df.set_index('date', inplace=True)
    
    return result_df, None
