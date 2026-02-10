import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.multioutput import MultiOutputRegressor
import joblib
import os
import sys
import json

# Add parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Paths
TRAINING_DIR = os.path.dirname(os.path.abspath(__file__))
FEATURES_PATH = os.path.join(TRAINING_DIR, "features.parquet")
MODELS_DIR = os.path.join(os.path.dirname(TRAINING_DIR), "models")

# Ensure models dir exists
os.makedirs(MODELS_DIR, exist_ok=True)

def create_dataset(df, horizon, target_col='pm25'):
    """
    Creates (X, y) pairs for a given forecast horizon and target column.
    """
    X = []
    y = []
    
    # Feature columns: all except 'target' or keys we don't want
    # We use ALL available numeric columns as features (including other pollutants)
    # This allows PM10 to help predict PM2.5, etc.
    
    # Exclude non-numeric or non-feature cols if any exist
    feature_cols = [c for c in df.columns if c not in ['is_interpolated', 'date_local', 'date_utc']]
    
    data_values = df[feature_cols].values
    target_values = df[target_col].values
    
    n_samples = len(df) - horizon
    
    X_list = []
    y_list = []
    
    # print(f"Building dataset for {target_col} (h={horizon})...")
    
    for i in range(n_samples):
        # Check if target window has NaNs (data gaps)
        future_window = target_values[i+1 : i+1+horizon]
        if np.isnan(future_window).any():
            continue
            
        current_features = data_values[i]
        if np.isnan(current_features).any():
            continue 
            
        X_list.append(current_features)
        y_list.append(future_window)
        
    return np.array(X_list), np.array(y_list), feature_cols

def train_models():
    print("Loading features...")
    if not os.path.exists(FEATURES_PATH):
        print("Features not found. Run make_features.py first.")
        return
        
    df = pd.read_parquet(FEATURES_PATH)
    print(f"Data shape: {df.shape}")
    
    # Identify Potential Targets
    # We want to train for: pm25, pm10, no2, so2, co, ozone
    # But only if they exist in the data
    possible_targets = ['pm25', 'pm10', 'no2', 'so2', 'co', 'ozone']
    available_targets = [t for t in possible_targets if t in df.columns]
    
    if not available_targets:
        print("No valid target columns found in data.")
        return
        
    print(f"Training models for targets: {available_targets}")
    
    horizons = [6, 12, 24]
    
    # Save feature config once (features are same for all)
    # We do it after first dataset creation to get feature list
    feature_config_saved = False
    
    for target in available_targets:
        print(f"\n=== Training for Target: {target} ===")
        
        for h in horizons:
            print(f"  Horizon {h}h...")
            X, y, feature_names = create_dataset(df, h, target_col=target)
            
            if len(X) == 0:
                print(f"  Not enough data for {target} horizon {h}!")
                continue
            
            # Save feature config if not done
            if not feature_config_saved:
                config_path = os.path.join(MODELS_DIR, "feature_config.json")
                with open(config_path, "w") as f:
                    json.dump({"features": feature_names}, f)
                print(f"  Saved feature config to {config_path}")
                feature_config_saved = True
                
            # Train (Use all data for production model)
            # We skip train/val split print for brevity now as we have many models
            
            model = MultiOutputRegressor(xgb.XGBRegressor(
                n_estimators=100,
                learning_rate=0.05,
                max_depth=6,
                objective='reg:squarederror',
                n_jobs=-1
            ))
            
            model.fit(X, y)
            
            model_path = os.path.join(MODELS_DIR, f"model_{target}_{h}h.pkl")
            joblib.dump(model, model_path)
            print(f"  Saved {os.path.basename(model_path)}")

if __name__ == "__main__":
    train_models()
