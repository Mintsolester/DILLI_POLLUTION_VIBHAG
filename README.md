# Delhi AQI Forecasting System

A production-style Streamlit forecasting system for Delhi Air Quality Index (AQI/PM2.5).

## System Architecture

```ascii
+-------------------+       +----------------------+       +-----------------------+
|   OpenAQ API      | ----> |   b) Offline Update  | ----> |   Historical Data     |
| (Historical Data) |       | (fetch_history.py)   |       | (Standardized CSV/DB) |
+-------------------+       +----------------------+       +-----------+-----------+
                                                                       |
                                                                       v
                                                           +-----------------------+
                                                           |   Feature Engineering |
                                                           |   (make_features.py)  |
                                                           +-----------+-----------+
                                                                       |
+-------------------+       +----------------------+                   v
|   OpenAQ API      | ----> |   Inference Engine   |       +-----------------------+
| (Real-time Data)  |       | (fetch_recent.py)    |       |   Model Training      |
+-------------------+       | (predict.py)         | <---- |   (train_models.py)   |
          |                 +-----------+----------+       |   (XGBoost 6h/12h/24h)|
          |                             |                  +-----------------------+
          v                             v
+--------------------------------------------------+
|               Streamlit Dashboard                |
|           (User selects 6h / 12h / 24h)          |
+--------------------------------------------------+
```

## Directory Structure

- `/data`: Scripts for data acquisition and storage.
- `/training`: Offline training pipeline (cleaning, feature engineering, modeling).
- `/inference`: Online inference logic (fetching recent data, generating predictions).
- `/models`: Trained model artifacts (`.pkl`).
- `app.py`: Main Streamlit application.

## Quick Start

### 1. Setup

```bash
pip install -r requirements.txt
```

### 2. Data Acquisition (Offline)

Fetch historical data (last 1 year +):

```bash
python data/fetch_history.py
```

### 3. Training

Train the XGBoost models for 6h, 12h, and 24h horizons:

```bash
# 1. Clean and resample to hourly
python training/build_hourly.py

# 2. Generate features and target
python training/make_features.py

# 3. Train models
python training/train_models.py
```

Models will be saved to the `/models` directory.

### 4. Running the App

```bash
streamlit run app.py
```

## Deployment

### Deploying to Streamlit Cloud (Free & Easy)

1.  **Push to GitHub**:
    *   Create a GitHub repository.
    *   Push all files, **including the `/models` directory** (this is crucial!).
    *   Make sure `requirements.txt` is in the root.

2.  **Connect to Streamlit Cloud**:
    *   Go to [share.streamlit.io](https://share.streamlit.io) and log in.
    *   Click **"New App"**.
    *   Select your GitHub repository.
    *   Set **Main file path** to `app.py`.

3.  **Add Your API Key (Secrets)**:
    *   Once deployed (or before), go to the app's **Settings** -> **Secrets**.
    *   Add your OpenAQ key like this:
        ```toml
        OPENAQ_API_KEY = "your_actual_api_key_here"
        ```
    *   Save. The app will restart and automatically pick up the key!

### Running Locally
To run locally, you can create a `.env` file in the root:
```bash
OPENAQ_API_KEY=your_key_here
```
Or verify it works by creating `.streamlit/secrets.toml`.

