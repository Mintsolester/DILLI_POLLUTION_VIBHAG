import pandas as pd
import os

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_PATH = os.path.join(DATA_DIR, "raw_history.parquet")
PROCESSED_DATA_PATH = os.path.join(DATA_DIR, "hourly_data.parquet")

def save_raw_data(df: pd.DataFrame, path: str = RAW_DATA_PATH):
    """Saves raw data to parquet."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_parquet(path, index=False)
    print(f"Saved {len(df)} records to {path}")

def load_raw_data(path: str = RAW_DATA_PATH) -> pd.DataFrame:
    """Loads raw data from parquet."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"No data found at {path}")
    return pd.read_parquet(path)

def save_processed_data(df: pd.DataFrame, path: str = PROCESSED_DATA_PATH):
    """Saves processed hourly data."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_parquet(path)
    print(f"Saved processed data to {path}")

def load_processed_data(path: str = PROCESSED_DATA_PATH) -> pd.DataFrame:
    """Loads processed hourly data."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"No data found at {path}")
    return pd.read_parquet(path)
