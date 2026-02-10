import streamlit as st
import pandas as pd
import sys
import os
import joblib
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Add path to finding modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from inference.fetch_recent import fetch_recent_data
from inference.validators import validate_completeness
from inference.predict import preprocess_and_predict
from inference.advisories import get_aqi_category, get_age_specific_advisory

# Page Config
st.set_page_config(
    page_title="Delhi AQI Forecaster",
    page_icon="🌫️",
    layout="wide"
)

# Title
st.title("🌫️ Delhi AQI Forecasting System")
st.markdown("**Target Location**: Delhi, India (R K Puram)")

# --- GLOBAL SETTINGS (Sidebar) ---
st.sidebar.header("Configuration")
horizon_option = st.sidebar.selectbox("Select Forecast Horizon", options=[6, 12, 24], index=0)
st.sidebar.info("**Note**: Forecasts use the last 72 hours of data.")

# --- SESSION STATE INITIALIZATION ---
if 'forecast_data' not in st.session_state:
    st.session_state.forecast_data = None
if 'recent_df' not in st.session_state:
    st.session_state.recent_df = None

# --- MAIN LOGIC ---
if st.sidebar.button("Run Forecast"):
    with st.spinner("Fetching data & running models..."):
        recent_df = fetch_recent_data()
        
    if recent_df.empty:
        st.error("Failed to fetch data from OpenAQ. API might be down.")
    else:
        is_valid, message = validate_completeness(recent_df)
        
        if not is_valid:
            st.error(f"Cannot forecast: {message}")
        else:
            # --- PRE-CALCULATE ALL FORECASTS ---
            all_forecasts = {}
            pollutants = ["pm25", "pm10", "no2", "so2", "co", "ozone"]
            
            with st.spinner(f"Generating comprehensive forecast..."):
                for p in pollutants:
                    if p in recent_df.columns:
                        f_df, err = preprocess_and_predict(recent_df, horizon_option, target_col=p)
                        if not err and f_df is not None:
                            all_forecasts[p] = f_df[f'predicted_{p}']
            
            if not all_forecasts:
                st.error("Could not generate forecasts for any pollutant.")
            else:
                # Store in session state
                st.session_state.recent_df = recent_df
                st.session_state.forecast_data = pd.DataFrame(all_forecasts)
                st.success("Forecast generated! Switch tabs to view details.")

# --- RENDER UI FROM SESSION STATE ---
if st.session_state.forecast_data is not None:
    combined_df = st.session_state.forecast_data
    recent_df = st.session_state.recent_df
    
    # --- TAB LAYOUT ---
    tab1, tab2 = st.tabs(["🏥 Health & Activity Planner", "🔬 Pollutant Deep Dive"])
    
    # ==========================================
    # TAB 1: HEALTH & ACTIVITY PLANNER
    # ==========================================
    with tab1:
        st.header("Health Advisory & Activity Planner")
        
        # Date Header
        forecast_date = combined_df.index[0].strftime('%A, %d %B %Y')
        st.subheader(f"📅 Forecast for {forecast_date}")
        
        # Legend Expander
        with st.expander("ℹ️ Understanding Data Colors"):
            st.markdown("""
            <div style="font-size: 14px;">
                <span style='color: #28a745; font-size: 16px;'>■</span> <b>Good</b>: Minimal impact.<br>
                <span style='color: #8fd19e; font-size: 16px;'>■</span> <b>Satisfactory</b>: Minor breathing discomfort to sensitive people.<br>
                <span style='color: #ffc107; font-size: 16px;'>■</span> <b>Moderate</b>: Breathing discomfort to people with lung/heart disease.<br>
                <span style='color: #fd7e14; font-size: 16px;'>■</span> <b>Poor</b>: Breathing discomfort to most people on prolonged exposure.<br>
                <span style='color: #dc3545; font-size: 16px;'>■</span> <b>Very Poor</b>: Respiratory illness on prolonged exposure.<br>
                <span style='color: #6f42c1; font-size: 16px;'>■</span> <b>Severe</b>: Affects healthy people and seriously impacts those with existing diseases.
            </div>
            """, unsafe_allow_html=True)
        
        # 1. Calculate Overall AQI Category per Hour
        def get_row_category(row):
            worst_cat_score = -1
            worst_cat_label = "Good"
            cat_rank = {"Good":0, "Satisfactory":1, "Moderate":2, "Poor":3, "Very Poor":4, "Severe":5}
            
            for col in row.index:
                    cat, _, _ = get_aqi_category(col, row[col])
                    score = cat_rank.get(cat, -1)
                    if score > worst_cat_score:
                        worst_cat_score = score
                        worst_cat_label = cat
            return worst_cat_label

        hourly_cat = combined_df.apply(get_row_category, axis=1)
        
        # 2. Timeline Visual (AM/PM)
        st.subheader(f"Hourly Timeline")
        
        timeline_html = "<div style='display: flex; overflow-x: scroll; gap: 5px; padding-bottom: 10px;'>"
        
        cat_colors = {
            "Good": "#28a745", "Satisfactory": "#8fd19e", 
            "Moderate": "#ffc107", "Poor": "#fd7e14", 
            "Very Poor": "#dc3545", "Severe": "#6f42c1"
        }
        
        for time, cat in hourly_cat.items():
            color = cat_colors.get(cat, "grey")
            time_str = time.strftime("%I:%M %p") # AM/PM format
            timeline_html += f"""
<div style='min-width: 65px; text-align: center;'>
    <div style='background-color: {color}; height: 40px; width: 100%; border-radius: 4px; margin-bottom: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.12);'></div>
    <span style='font-size: 11px; font-weight: bold;'>{time_str}</span><br>
    <span style='font-size: 10px; color: #555;'>{cat}</span>
</div>
"""
        timeline_html += "</div>"
        st.markdown(timeline_html, unsafe_allow_html=True)
        
        # 3. Detailed Advisory for the WORST hour
        worst_overall = get_row_category(combined_df.max()) 
        advisory = get_age_specific_advisory(worst_overall)
        
        st.subheader(f"⚠️ Activity Guidance (Peak Status: {worst_overall})")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**👶 Children**\n\n{advisory['Children']}")
        with col2:
            st.info(f"**👩 Adults**\n\n{advisory['Adults']}")
        with col3:
            st.info(f"**👴 Seniors**\n\n{advisory['Seniors']}")
            
        st.success(f"**💡 General Advice**: {advisory['General']}")
        
    # ==========================================
    # TAB 2: POLLUTANT DEEP DIVE (Grid View)
    # ==========================================
    with tab2:
        st.header("Detailed Pollutant Analysis")
        st.caption("Forecasts for all monitored pollutants.")
        
        pollutants = combined_df.columns.tolist()
        
        # CSS to hide default plotly mode bar to keep it clean, AND make plots smaller/tighter
        st.markdown("<style> .js-plotly-plot .plotly .modebar { display: none; } </style>", unsafe_allow_html=True)

        for i in range(0, len(pollutants), 2):
            cols = st.columns(2)
            
            # Chart 1
            if i < len(pollutants):
                p1 = pollutants[i]
                with cols[0]:
                    fig = go.Figure()
                    # History
                    if p1 in recent_df.columns:
                        hist = recent_df[p1].tail(24)
                        fig.add_trace(go.Scatter(x=hist.index, y=hist.values, name="Past 24h", line=dict(color='gray', width=1)))
                    # Forecast
                    pred = combined_df[p1]
                    fig.add_trace(go.Scatter(x=pred.index, y=pred.values, name="Forecast", line=dict(color='#d62728', width=2)))
                    
                    fig.update_layout(
                        title=f"<b>{p1.upper()}</b>", 
                        margin=dict(l=10, r=10, t=30, b=10),
                        height=250,
                        showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # Chart 2
            if i + 1 < len(pollutants):
                p2 = pollutants[i+1]
                with cols[1]:
                    fig = go.Figure()
                    # History
                    if p2 in recent_df.columns:
                        hist = recent_df[p2].tail(24)
                        fig.add_trace(go.Scatter(x=hist.index, y=hist.values, name="Past 24h", line=dict(color='gray', width=1)))
                    # Forecast
                    pred = combined_df[p2]
                    fig.add_trace(go.Scatter(x=pred.index, y=pred.values, name="Forecast", line=dict(color='#d62728', width=2)))
                    
                    fig.update_layout(
                        title=f"<b>{p2.upper()}</b>", 
                        margin=dict(l=10, r=10, t=30, b=10),
                        height=250,
                        showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("📋 Forecast Data Table")
        st.dataframe(combined_df.style.format("{:.1f}"))
        
        st.caption(f"Forecast Issued: {datetime.now().strftime('%d %b %Y, %H:%M %p')}")

else:
    st.info("👈 Click 'Run Forecast' in the sidebar to begin.")
    st.markdown("""
    ### Features:
    - **Health Planner**: Timelines and activity advice for your family.
    - **Deep Dive**: Detailed charts for PM2.5, NO2, Ozone, etc.
    """)
