import os
import sys

def verify_setup():
    print("Verifying Project Setup...")
    
    # Check Directories
    dirs = ['data', 'training', 'inference', 'models']
    for d in dirs:
        if os.path.exists(d):
            print(f"✅ Directory {d} exists.")
        else:
            print(f"❌ Directory {d} MISSING.")
            
    # Check Files
    files = [
        'data/fetch_history.py',
        'data/storage.py',
        'training/build_hourly.py',
        'training/make_features.py',
        'training/train_models.py',
        'training/evaluate.py',
        'inference/fetch_recent.py',
        'inference/validators.py',
        'inference/predict.py',
        'app.py',
        'requirements.txt',
        'README.md'
    ]
    
    for f in files:
        if os.path.exists(f):
            print(f"✅ File {f} exists.")
        else:
            print(f"❌ File {f} MISSING.")
            
    # Check Imports
    print("\nChecking Imports...")
    try:
        from data import fetch_history, storage
        print("✅ Data modules imported.")
    except ImportError as e:
        print(f"❌ Data module import failed: {e}")

    try:
        from training import build_hourly, make_features, train_models, evaluate
        print("✅ Training modules imported.")
    except ImportError as e:
        print(f"❌ Training module import failed: {e}")

    try:
        from inference import fetch_recent, validators, predict
        print("✅ Inference modules imported.")
    except ImportError as e:
        print(f"❌ Inference module import failed: {e}")
        
    print("\nVerification Complete.")

if __name__ == "__main__":
    verify_setup()
