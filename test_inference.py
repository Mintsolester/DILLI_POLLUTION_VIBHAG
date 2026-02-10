import sys
import os
import pandas as pd

# Add parent directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from inference.fetch_recent import fetch_recent_data
from inference.predict import preprocess_and_predict

def test_pipeline():
    print("1. Fetching recent data...")
    df = fetch_recent_data()
    print(f"Fetched Data Shape: {df.shape}")
    print("Columns:", df.columns)
    print("Head:\n", df.head())
    print("Tail:\n", df.tail())
    
    if df.empty:
        print("Test Failed: No data fetched.")
        return

    print("\n2. Running Prediction (Horizon=24h)...")
    try:
        forecast, error = preprocess_and_predict(df, horizon=24)
        
        if error:
            print(f"Prediction Error: {error}")
        else:
            print("Forecast Generated Successfully!")
            print(forecast)
            
    except Exception as e:
        print(f"Prediction Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pipeline()
