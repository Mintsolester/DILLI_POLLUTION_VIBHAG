def get_aqi_category(parameter, value):
    """
    Returns the AQI category and color based on pollutant value.
    Breakpoints based on a mix of India CPCB and US EPA standards for approximate guidance.
    
    Units assumed:
    - pm25, pm10, ozone: µg/m³
    - no2, so2, co: ppb
    """
    value = float(value)
    
    # Define (Threshold, Category, Color, Description)
    # Threshold is the UPPER limit for that category
    breakpoints = {
        "pm25": [
            (30, "Good", "green", "Air quality is satisfactory, and air pollution poses little or no risk."),
            (60, "Satisfactory", "lightgreen", "Sensitive people should consider reducing prolonged or heavy exertion."),
            (90, "Moderate", "yellow", "Unusually sensitive people should reduce prolonged or heavy exertion."),
            (120, "Poor", "orange", "People with heart/lung disease, older adults, and children should reduce exertion."),
            (250, "Very Poor", "red", "Everyone should avoid prolonged or heavy exertion."),
            (float('inf'), "Severe", "purple", "Health warning of emergency conditions. The entire population is more likely to be affected.")
        ],
        "pm10": [
            (50, "Good", "green", "Air quality is satisfactory."),
            (100, "Satisfactory", "lightgreen", "Sensitive people should consider reducing exertion."),
            (250, "Moderate", "yellow", "People with respiratory disease should reduce exertion."),
            (350, "Poor", "orange", "Older adults and children should reduce exertion."),
            (430, "Very Poor", "red", "Everyone should avoid prolonged or heavy exertion."),
            (float('inf'), "Severe", "purple", "Serious risk of respiratory effects.")
        ],
        "no2": [ # Converted approx from µg/m3 (1 ppb ~ 1.88 µg/m3)
            (40/1.88, "Good", "green", "No significant risk."),
            (80/1.88, "Satisfactory", "lightgreen", "Minor breathing discomfort to sensitive people."),
            (180/1.88, "Moderate", "yellow", "Breathing discomfort to people with lung disease."),
            (280/1.88, "Poor", "orange", "Breathing discomfort to most people on prolonged exposure."),
            (400/1.88, "Very Poor", "red", "Respiratory illness on prolonged exposure."),
            (float('inf'), "Severe", "purple", "Affects healthy people and seriously impacts those with existing diseases.")
        ],
        "ozone": [ # 8-hr standard approx
            (50, "Good", "green", "No risk."),
            (100, "Satisfactory", "lightgreen", "Minor breathing discomfort to sensitive people."),
            (168, "Moderate", "yellow", "Breathing discomfort to people with lung disease."),
            (208, "Poor", "orange", "Breathing discomfort to most people."),
            (748, "Very Poor", "red", "Significant health effects."),
            (float('inf'), "Severe", "purple", "Serious health effects.")
        ],
        "so2": [ # 1 ppb ~ 2.62 µg/m3
            (40/2.62, "Good", "green", "No risk."),
            (80/2.62, "Satisfactory", "lightgreen", "Minor breathing discomfort to sensitive people."),
            (380/2.62, "Moderate", "yellow", "Breathing discomfort to people with lung disease."),
            (800/2.62, "Poor", "orange", "Breathing discomfort to most people."),
            (1600/2.62, "Very Poor", "red", "Significant health effects."),
            (float('inf'), "Severe", "purple", "Serious health effects.")
        ],
        "co": [ # 1 ppb = 0.001 ppm. 1 ppm = 1.15 mg/m3. 
            # Let's assume standard ppb input. CO standards are usually in mg/m3 (e.g. 2 mg/m3 = Good)
            # 2 mg/m3 ~= 1750 ppb
            (1000, "Good", "green", "No risk."),
            (2000, "Satisfactory", "lightgreen", "Minor risk."),
            (10000, "Moderate", "yellow", "Risk to sensitive groups."),
            (17000, "Poor", "orange", "Significant risk."),
            (34000, "Very Poor", "red", "High risk."),
            (float('inf'), "Severe", "purple", "Critical risk.")
        ]
    }
    
    param_breaks = breakpoints.get(parameter)
    if not param_breaks:
        return "Unknown", "grey", "No data available."
        
    for threshold, label, color, desc in param_breaks:
        if value <= threshold:
            return label, color, desc
            
    return "Severe", "purple", "Health warning of emergency conditions."

def get_activity_guidance(category):
    # Keep backward compatibility for now, but redirect to new logic if needed or just simple string
    guidance = {
        "Good": "✅ **Outdoor Activities**: Perfect time for outdoor activities! Go for a run, walk, or picnic.",
        "Satisfactory": "✅ **Outdoor Activities**: Good for outdoor activities. Unusually sensitive people should consider reducing heavy exertion.",
        "Moderate": "⚠️ **Outdoor Activities**: Okay to go out, but sensitive groups (asthma, lung disease) should reduce prolonged exertion.",
        "Poor": "🚫 **Exercises**: Avoid heavy outdoor exercise. \n😷 **Protection**: Wear a mask if you have respiratory issues.",
        "Very Poor": "🚫 **Exercises**: Avoid all outdoor physical activities. \n🏠 **Indoors**: Keep windows closed.\n😷 **Protection**: Wear an N95 mask if you must go out.",
        "Severe": "⛔ **Emergency**: Stay indoors! Close all windows and use an air purifier if available. Avoid all outdoor exposure."
    }
    return guidance.get(category, "No specific guidance.")

def get_age_specific_advisory(category):
    """
    Returns a dictionary of advisories for different age groups.
    """
    advisories = {
        "Good": {
            "Children": "✅ Full outdoor play allowed.",
            "Adults": "✅ Perfect for jogging/cycling.",
            "Seniors": "✅ Safe for walks.",
            "General": "Enjoy the fresh air!"
        },
        "Satisfactory": {
            "Children": "✅ Good for play.",
            "Adults": "✅ Good for outdoor workouts.",
            "Seniors": "✅ Safe, but monitor if sensitive.",
            "General": "Air quality is acceptable."
        },
        "Moderate": {
            "Children": "⚠️ Reduce prolonged outdoor exertion.",
            "Adults": "⚠️ Sensitive individuals should reduce heavy exertion.",
            "Seniors": "⚠️ Short walks only. Avoid heavy exertion.",
            "General": "Concern for sensitive people."
        },
        "Poor": {
            "Children": "🚫 Avoid prolonged outdoor play.",
            "Adults": "⚠️ Reduce intense outdoor exercises.",
            "Seniors": "🚫 Stay indoors mainly. Avoid morning walks.",
            "General": "Wear a mask if sensitive."
        },
        "Very Poor": {
            "Children": "⛔ NO outdoor play. Keep indoors.",
            "Adults": "🚫 Avoid all outdoor exercise.",
            "Seniors": "⛔ Stay strictly indoors.",
            "General": "Wear N95 mask. Use air purifiers."
        },
        "Severe": {
            "Children": "⛔ RESTRICT INDOORS. No going out.",
            "Adults": "⛔ Avoid all outdoor exposure.",
            "Seniors": "⛔ RESTRICT INDOORS. Medical emergency level.",
            "General": "Emergency conditions. Seal windows."
        }
    }
    return advisories.get(category, {
        "Children": "No data", "Adults": "No data", "Seniors": "No data", "General": "No data"
    })
