import os
import subprocess
import sys

def run_step(script_path, description):
    print(f"\n=== {description} ===")
    print(f"Running {script_path}...")
    try:
        # Use simple run, assuming same python environment
        result = subprocess.run([sys.executable, script_path], check=True)
        print(f"✅ {description} completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with error code {e.returncode}.")
        sys.exit(1)

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Fetch History (Optional? No, let's assume user wants to update)
    # run_step(os.path.join(base_dir, "data", "fetch_history.py"), "Fetching Historical Data")
    # For now, let's assume 'fetch_history.py' is run manually or separately as it takes long.
    # But for a full pipeline, we should include it.
    # If the user is running this, they probably want to refresh everything.
    
    # Check if we should skip fetch
    skip_fetch = len(sys.argv) > 1 and sys.argv[1] == "--skip-fetch"
    
    if not skip_fetch:
        run_step(os.path.join(base_dir, "data", "fetch_history.py"), "Fetching Historical Data")
    else:
        print("\n=== Skipping Data Fetch (User Request) ===")

    # 2. Build Hourly
    run_step(os.path.join(base_dir, "training", "build_hourly.py"), "Processing & Resampling Data")

    # 3. Make Features
    run_step(os.path.join(base_dir, "training", "make_features.py"), "Generating Features")

    # 4. Train Models
    run_step(os.path.join(base_dir, "training", "train_models.py"), "Training Multi-Target Models")

    print("\n🎉 Pipeline Finished! You can now run the dashboard:")
    print("streamlit run app.py")

if __name__ == "__main__":
    main()
