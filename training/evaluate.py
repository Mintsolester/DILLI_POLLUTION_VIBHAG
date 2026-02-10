import pandas as pd
import numpy as np
import joblib
import os
import sys
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Add parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TRAINING_DIR = os.path.dirname(os.path.abspath(__file__))
FEATURES_PATH = os.path.join(TRAINING_DIR, "features.parquet")
MODELS_DIR = os.path.join(os.path.dirname(TRAINING_DIR), "models")

def evaluate_models():
    print("Evaluating models...")
    if not os.path.exists(FEATURES_PATH):
        print("Features not found.")
        return
        
    df = pd.read_parquet(FEATURES_PATH)
    
    # Load config
    # We need to recreate the exact dataset structure (X, y) 
    # However, 'create_dataset' is in train_models.py. Ideally should be in a shared util or imported.
    # I'll import it from train_models
    sys.path.append(TRAINING_DIR)
    from train_models import create_dataset
    
    horizons = [6, 12, 24]
    
    metrics = []
    
    for h in horizons:
        model_path = os.path.join(MODELS_DIR, f"model_{h}h.pkl")
        if not os.path.exists(model_path):
            print(f"Model for {h}h not found.")
            continue
            
        model = joblib.load(model_path)
        
        # Create dataset
        X, y, _ = create_dataset(df, h)
        
        # Use only Test set (last 15%)
        n = len(X)
        test_start = int(n * 0.85)
        X_test, y_test = X[test_start:], y[test_start:]
        
        predictions = model.predict(X_test)
        
        # Metrics
        mae = mean_absolute_error(y_test, predictions)
        rmse = np.sqrt(mean_squared_error(y_test, predictions))
        
        # Peak Error (Top 10% of Actual AQI)
        # Flatten for global distribution check or check per-sample max?
        # Let's check error on high-value samples.
        # Max value in each target window?
        # Or simply, flatten everything.
        
        y_test_flat = y_test.flatten()
        pred_flat = predictions.flatten()
        
        threshold = np.percentile(y_test_flat, 90)
        mask = y_test_flat >= threshold
        
        peak_mae = mean_absolute_error(y_test_flat[mask], pred_flat[mask])
        
        print(f"\nHorizon {h}h Metrics (Test Set):")
        print(f"  MAE: {mae:.2f}")
        print(f"  RMSE: {rmse:.2f}")
        print(f"  Peak MAE (Top 10%): {peak_mae:.2f}")
        
        metrics.append({
            "Horizon": h,
            "MAE": mae,
            "RMSE": rmse,
            "PeakMAE": peak_mae
        })
        
    # Save report
    pd.DataFrame(metrics).to_csv(os.path.join(MODELS_DIR, "evaluation_metrics.csv"), index=False)
    print("\nMetrics saved to evaluation_metrics.csv")

if __name__ == "__main__":
    evaluate_models()
