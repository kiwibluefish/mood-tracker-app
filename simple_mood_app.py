# Simple Mood Tracking App - All-in-One Version (No Email)
# Run with: streamlit run simple_mood_app_fixed.py

import streamlit as st
import pandas as pd
import json
import os
import requests
import time
from datetime import date, datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# --- Authentication gate (Streamlit-managed OIDC) ---
def show_login():
    st.header("This app is private.")
    st.subheader("Please sign in with Google")
    if st.button("Sign in with Google"):
        st.login()

# If user not logged in, show login screen and stop execution
if not st.user.is_logged_in:
    show_login()
    st.stop()  # prevents the rest of the app from running until login
else:
    # Example: available identity fields
    user_email = st.user.email
    user_name = st.user.name
    st.sidebar.markdown(f"Signed in as **{user_name}** ({user_email})")
    if st.button("Log out"):
        st.logout()
        st.experimental_rerun()

# imports near top:
import psycopg2
from psycopg2.extras import Json, RealDictCursor
from datetime import datetime, date
import streamlit as st

def get_db_conn():
    db = st.secrets["connections"]["postgresql"]
    conn = psycopg2.connect(
        host=db["host"],
        port=db["port"],
        dbname=db["database"],
        user=db["username"],
        password=db["password"],
        sslmode=db.get("sslmode", "require")
    )
    return conn

def load_data_from_db(user_email):
    conn = get_db_conn()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT data FROM public.user_data WHERE email = %s", (user_email,))
        row = cur.fetchone()
        if not row:
            return []
        data = row["data"]
        # convert date strings back to date objects if needed
        for entry in data:
            if isinstance(entry.get('date'), str):
                entry['date'] = datetime.strptime(entry['date'], '%Y-%m-%d').date()
        return data
    finally:
        conn.close()

def save_data_to_db(user_email, data):
    # serialize dates
    data_to_save = []
    for entry in data:
        entry_copy = entry.copy()
        if isinstance(entry_copy.get('date'), date):
            entry_copy['date'] = entry_copy['date'].strftime('%Y-%m-%d')
        data_to_save.append(entry_copy)

    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO public.user_data (email, data)
            VALUES (%s, %s)
            ON CONFLICT (email) DO UPDATE SET data = EXCLUDED.data, updated_at = now()
            """, (user_email, Json(data_to_save)))
        conn.commit()
    finally:
        conn.close()

# Configuration
DATA_FILE = "mood_data.json"
CONFIG_FILE = "app_config.json"

# Tag palette
TAG_PALETTE = [
    ("😊", "happy"), ("😔", "sad"), ("😰", "anxious"), ("😴", "sleep"),
    ("🏃‍♂️", "exercise"), ("💼", "work"), ("🍽️", "meals"), ("☀️", "sunlight"),
    ("🌧️", "rainy"), ("🤝", "social"), ("📚", "study"), ("🎵", "music"),
    ("👨‍👩‍👧", "Family"), ("🧘", "Quiet time"), ("📖", "reading"), ("🎮", "Gaming"),
    ("📺", "TV"), ("📱", "Social Media")
]

# Theme definitions
THEMES = {
    "🌊 Ocean": {
        "primary": "#3b82f6",
        "secondary": "#1e40af",
        "accent": "#60a5fa",
        "background": "#f8fafc",
        "surface": "#ffffff",
        "text": "#1f2937",
        "gradient_start": "#667eea",
        "gradient_end": "#764ba2",
        "mood_colors": ["#1e40af", "#2563eb", "#3b82f6", "#60a5fa", "#93c5fd", "#dbeafe"]
    },
    "🌅 Sunrise": {
        "primary": "#f59e0b",
        "secondary": "#d97706",
        "accent": "#fbbf24",
        "background": "#fffbeb",
        "surface": "#ffffff",
        "text": "#92400e",
        "gradient_start": "#f59e0b",
        "gradient_end": "#ef4444",
        "mood_colors": ["#dc2626", "#ef4444", "#f59e0b", "#fbbf24", "#fde047", "#fef3c7"]
    },
    "🌸 Blossom": {
        "primary": "#ec4899",
        "secondary": "#be185d",
        "accent": "#f472b6",
        "background": "#fdf2f8",
        "surface": "#ffffff",
        "text": "#831843",
        "gradient_start": "#ec4899",
        "gradient_end": "#8b5cf6",
        "mood_colors": ["#be185d", "#ec4899", "#f472b6", "#f9a8d4", "#fbcfe8", "#fce7f3"]
    },
    "🌿 Nature": {
        "primary": "#10b981",
        "secondary": "#047857",
        "accent": "#34d399",
        "background": "#f0fdf4",
        "surface": "#ffffff",
        "text": "#064e3b",
        "gradient_start": "#10b981",
        "gradient_end": "#059669",
        "mood_colors": ["#047857", "#059669", "#10b981", "#34d399", "#6ee7b7", "#d1fae5"]
    },
    "🌙 Midnight": {
        "primary": "#8b5cf6",
        "secondary": "#7c3aed",
        "accent": "#a78bfa",
        "background": "#0f172a",
        "surface": "#1e293b",
        "text": "#e2e8f0",
        "gradient_start": "#8b5cf6",
        "gradient_end": "#3b82f6",
        "mood_colors": ["#7c3aed", "#8b5cf6", "#a78bfa", "#c4b5fd", "#ddd6fe", "#ede9fe"]
    }
}

# App configuration
st.set_page_config(page_title="Daily Mood Check-in", page_icon="😊", layout="centered")

# Theme management functions
def get_current_theme():
    """Get current theme from session state or default"""
    return st.session_state.get("current_theme", "🌊 Ocean")

def apply_theme_css(theme_name):
    """Apply CSS variables based on selected theme"""
    if theme_name == "🎨 Custom":
        # Use custom colors from session state
        theme = {
            "primary": st.session_state.get("custom_primary", "#3b82f6"),
            "secondary": st.session_state.get("custom_secondary", "#1e40af"),
            "accent": st.session_state.get("custom_accent", "#60a5fa"),
            "background": st.session_state.get("custom_background", "#f8fafc"),
            "surface": st.session_state.get("custom_surface", "#ffffff"),
            "text": st.session_state.get("custom_text", "#1f2937"),
            "gradient_start": st.session_state.get("custom_gradient_start", "#667eea"),
            "gradient_end": st.session_state.get("custom_gradient_end", "#764ba2"),
            "mood_colors": ["#1e40af", "#2563eb", "#3b82f6", "#60a5fa", "#93c5fd", "#dbeafe"]
        }
    else:
        theme = THEMES.get(theme_name, THEMES["🌊 Ocean"])

    # Apply CSS with theme variables
    st.markdown(f"""
    <style>
    :root {{
        --primary-color: {theme["primary"]};
        --secondary-color: {theme["secondary"]};
        --accent-color: {theme["accent"]};
        --background-color: {theme["background"]};
        --surface-color: {theme["surface"]};
        --text-color: {theme["text"]};
        --gradient-start: {theme["gradient_start"]};
        --gradient-end: {theme["gradient_end"]};
    }}

    /* Apply theme to body and main container */
    .stApp {{
        background-color: var(--background-color);
        color: var(--text-color);
    }}

    .mood-display {{
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 16px;
        margin: 12px 0;
        border-radius: 12px;
        font-size: 1.2rem;
        font-weight: 600;
        background-color: var(--surface-color);
    }}

    .ai-suggestion-box {{
        min-height: 120px;
        background: linear-gradient(135deg, var(--gradient-start) 0%, var(--gradient-end) 100%);
        color: white;
        padding: 16px;
        border-radius: 12px;
        margin: 8px 0;
    }}

    .tag-chip {{
        display: inline-block;
        background: var(--accent-color);
        color: var(--surface-color);
        padding: 4px 12px;
        margin: 2px 4px;
        border-radius: 20px;
        font-size: 0.85rem;
        opacity: 0.8;
    }}

    .stButton>button {{
        border-radius: 8px;
        min-height: 44px;
        background-color: var(--surface-color);
        color: var(--text-color);
        border: 1px solid var(--accent-color);
    }}

    /* Primary button styling with theme colors */
    .stButton>button[kind="primary"] {{
        background-color: var(--primary-color) !important;
        border-color: var(--primary-color) !important;
        color: white !important;
    }}

    .stButton>button[kind="primary"]:hover {{
        background-color: var(--secondary-color) !important;
        border-color: var(--secondary-color) !important;
    }}

    /* Tab styling with theme colors - Enhanced targeting */
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
        border-bottom-color: var(--primary-color) !important;
        color: var(--primary-color) !important;
    }}

    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"]:focus {{
        border-bottom-color: var(--primary-color) !important;
        color: var(--primary-color) !important;
    }}

    .stTabs [data-baseweb="tab-list"] button:hover {{
        color: var(--primary-color) !important;
    }}

    /* Additional tab underline targeting */
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"]::after {{
        border-bottom-color: var(--primary-color) !important;
    }}

    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] > div {{
        border-bottom-color: var(--primary-color) !important;
    }}

    /* Force tab border color override */
    .stTabs [data-baseweb="tab-list"] [role="tab"][aria-selected="true"] {{
        border-bottom: 2px solid var(--primary-color) !important;
    }}

    /* Sidebar styling */
    .css-1d391kg {{
        background-color: var(--surface-color);
    }}

    /* Dynamic mood slider styling - Enhanced targeting */
    .stSlider [data-baseweb="slider"] [data-baseweb="thumb"] {{
        background-color: var(--slider-color) !important;
        border-color: var(--slider-color) !important;
    }}

    .stSlider [data-baseweb="slider"] [data-baseweb="track"] {{
        background: var(--slider-color) !important;
        background-image: none !important;
    }}

    /* Force override of any red slider elements */
    .stSlider [data-baseweb="slider"] [data-baseweb="track"] [style*="background-color: rgb(255, 75, 75)"] {{
        background-color: var(--slider-color) !important;
    }}

    .stSlider [data-baseweb="slider"] [data-baseweb="track"] [style*="background: rgb(255, 75, 75)"] {{
        background: var(--slider-color) !important;
    }}

    .stSlider [data-baseweb="slider"] [data-baseweb="track"] > div {{
        background-color: var(--slider-color) !important;
    }}

    .stSlider [data-baseweb="slider"] [data-baseweb="track"] [data-baseweb="tick-bar"] {{
        background-color: var(--slider-color) !important;
    }}

    .stSlider div[role="slider"] {{
        background-color: var(--slider-color) !important;
    }}

    .stSlider [data-baseweb="slider"] > div > div > div {{
        background-color: var(--slider-color) !important;
    }}

    /* Additional slider track styling */
    .stSlider [data-baseweb="slider"] [data-baseweb="track"] [data-baseweb="inner-track"] {{
        background-color: var(--slider-color) !important;
    }}

    .stSlider [data-baseweb="slider"] [data-baseweb="track"] > div:first-child {{
        background-color: var(--slider-color) !important;
    }}

    .stSlider [data-baseweb="slider"] [data-baseweb="track"] > div:last-child {{
        background-color: var(--accent-color) !important;
        opacity: 0.3;
    }}

    /* Keep slider number/text readable */
    .stSlider .stMarkdown p,
    .stSlider div[data-testid="stMarkdownContainer"] p,
    .stSlider span {{
        color: var(--text-color) !important;
    }}

    /* Force slider track to use theme colors */
    .stSlider > div > div > div > div {{
        background-color: var(--slider-color) !important;
    }}

    .stSlider [role="slider"] {{
        background-color: var(--slider-color) !important;
    }}

    /* Target the actual slider track element */
    .stSlider [data-baseweb="slider"] [data-baseweb="track"] {{
        background-color: var(--slider-color) !important;
        background-image: none !important;
    }}

    /* Override any default styling */
    .stSlider [data-baseweb="slider"] [data-baseweb="track"] > div[style*="background"] {{
        background-color: var(--slider-color) !important;
        background-image: none !important;
    }}

    /* Ensure slider thumb matches theme */
    .stSlider [data-baseweb="slider"] [data-baseweb="thumb"] {{
        background-color: var(--slider-color) !important;
        border-color: var(--slider-color) !important;
    }}

    /* Global red color override - catch any missed red elements */
    .stApp [style*="color: rgb(255, 75, 75)"] {{
        color: var(--primary-color) !important;
    }}

    .stApp [style*="background-color: rgb(255, 75, 75)"] {{
        background-color: var(--primary-color) !important;
    }}

    .stApp [style*="border-color: rgb(255, 75, 75)"] {{
        border-color: var(--primary-color) !important;
    }}

    /* Streamlit default red override */
    .stApp [style*="#FF4B4B"] {{
        color: var(--primary-color) !important;
        background-color: var(--primary-color) !important;
        border-color: var(--primary-color) !important;
    }}

    /* Additional slider track targeting */
    .stSlider [data-baseweb="slider"] [data-baseweb="track"] > div[style] {{
        background-color: var(--slider-color) !important;
        background: var(--slider-color) !important;
    }}

    /* SIMPLE HARDCODED FIXES - Target specific red elements */

    /* Fix slider track - force blue instead of red */
    .stSlider [data-baseweb="slider"] [data-baseweb="track"] {{
        background: var(--primary-color) !important;
        background-color: var(--primary-color) !important;
    }}

    /* Fix tab underline - force blue instead of red */
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
        border-bottom-color: var(--primary-color) !important;
    }}

    /* Catch any remaining Streamlit red elements */
    [style*="rgb(255, 75, 75)"] {{
        background-color: var(--primary-color) !important;
        border-color: var(--primary-color) !important;
    }}

    [style*="#FF4B4B"] {{
        background-color: var(--primary-color) !important;
        border-color: var(--primary-color) !important;
    }}

    </style>
    """, unsafe_allow_html=True)

# Data management functions
def load_data():
    """Load mood data from JSON file"""
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            # Convert string dates back to date objects for processing
            for entry in data:
                if isinstance(entry.get('date'), str):
                    entry['date'] = datetime.strptime(entry['date'], '%Y-%m-%d').date()
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_data(data):
    """Save mood data to JSON file"""
    # Convert date objects to strings for JSON serialization
    data_to_save = []
    for entry in data:
        entry_copy = entry.copy()
        if isinstance(entry_copy.get('date'), date):
            entry_copy['date'] = entry_copy['date'].strftime('%Y-%m-%d')
        data_to_save.append(entry_copy)

    with open(DATA_FILE, 'w') as f:
        json.dump(data_to_save, f, indent=2)

def load_config():
    """Load app configuration"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "openai_api_key": ""
        }

def save_config(config):
    """Save app configuration"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

# Mood helper functions
def get_mood_emoji_and_label(mood_score):
    """Return emoji and label for mood score"""
    if mood_score <= 1:
        return "😢", "Very Low", "#1e40af"
    elif mood_score <= 3:
        return "😔", "Low", "#2563eb"
    elif mood_score <= 4:
        return "😐", "Below Average", "#3b82f6"
    elif mood_score <= 6:
        return "🙂", "Okay", "#60a5fa"
    elif mood_score <= 8:
        return "😊", "Good", "#93c5fd"
    else:
        return "😄", "Great", "#dbeafe"

def get_helpful_hint(score, note_text=""):
    """Generate helpful hint based on mood score and note"""
    note_lower = (note_text or "").lower()

    if score <= 3 or any(word in note_lower for word in ["overwhelmed", "anxious", "panic", "fear"]):
        return (
            "When everything feels heavy, start with the smallest possible anchor. "
            "Try one minute of slow breathing, counting 4-in and 6-out. "
            "Look around and name a few things you can see or touch. "
            "If distress continues, consider reaching out to someone you trust or a helpline. "
            "For now, choose one tiny action—roll your shoulders, sip water, or step outside."
        )
    elif score <= 5 or any(word in note_lower for word in ["stuck", "flat", "empty", "numb"]):
        return (
            "When energy is low, momentum comes from tiny wins. "
            "Pick a 5-minute task you can complete now—tidy one surface, stretch, or put on music. "
            "Consider a short walk or write about one thing you care about this week. "
            "Text a friend a simple check-in. Thank yourself for showing up today. "
            "Choose your next tiny action and commit to just two minutes."
        )
    else:
        return (
            "Great to see some positive energy! Savor this good moment for 20 seconds. "
            "Consider sharing this energy with someone—send a kind note or plan something you enjoy. "
            "Capture one doable plan for later so the momentum has somewhere to go. "
            "Mark this win in your memory—small joys add up over time."
        )

def get_ai_suggestion(mood_score, note_text, api_key):
    """Get AI suggestion from OpenAI"""
    if not api_key:
        return ""

    try:
        # Simple prompt based on mood level
        if mood_score <= 2:
            system_prompt = "You are a gentle, supportive counselor. Provide immediate emotional support with 3-4 sentences. Focus on comfort and small, manageable steps."
        elif mood_score <= 4:
            system_prompt = "You are an encouraging coach. Provide gentle motivation with 3-4 sentences. Focus on small positive actions and building momentum."
        elif mood_score <= 6:
            system_prompt = "You are an upbeat coach. Provide fun suggestions to boost mood with 3-4 sentences. Focus on enjoyable activities."
        else:
            system_prompt = "You are an enthusiastic coach. Celebrate their positive state with 3-4 sentences. Focus on maintaining and sharing positivity."

        user_prompt = f"Someone is feeling {mood_score}/10 today. {f'They shared: {note_text}' if note_text else ''} Please provide a supportive response."

        # Make API call to OpenAI
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 200
        }

        response = requests.post("https://api.openai.com/v1/chat/completions",
                               headers=headers, json=data, timeout=30)

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()
        else:
            return f"AI temporarily unavailable (Error {response.status_code})"

    except Exception as e:
        return f"AI temporarily unavailable: {str(e)[:50]}..."

# Initialize session state
if "selected_tags" not in st.session_state:
    st.session_state.selected_tags = set()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_ai_call" not in st.session_state:
    st.session_state.last_ai_call = 0
if "mood_value" not in st.session_state:
    st.session_state.mood_value = 5
if "current_theme" not in st.session_state:
    st.session_state.current_theme = "🌊 Ocean"

# Load data and config
data = load_data()
config = load_config()

# Load theme preference from config
if "theme" in config:
    st.session_state.current_theme = config["theme"]

# Apply current theme CSS
apply_theme_css(st.session_state.current_theme)

# Sidebar for settings
st.sidebar.header("⚙️ Settings")

# Theme Picker
st.sidebar.subheader("🎨 Theme")
theme_options = list(THEMES.keys()) + ["🎨 Custom"]
selected_theme = st.sidebar.selectbox(
    "Choose your theme:",
    theme_options,
    index=theme_options.index(st.session_state.current_theme) if st.session_state.current_theme in theme_options else 0,
    help="Select a theme to change the app's appearance instantly!"
)

# Handle theme change
if selected_theme != st.session_state.current_theme:
    st.session_state.current_theme = selected_theme
    config["theme"] = selected_theme
    save_config(config)
    st.rerun()

# Custom theme color pickers (only show if Custom theme is selected)
if selected_theme == "🎨 Custom":
    st.sidebar.subheader("🎨 Custom Colors")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.session_state.custom_primary = st.color_picker("Primary", st.session_state.get("custom_primary", "#3b82f6"))
        st.session_state.custom_accent = st.color_picker("Accent", st.session_state.get("custom_accent", "#60a5fa"))
        st.session_state.custom_background = st.color_picker("Background", st.session_state.get("custom_background", "#f8fafc"))

    with col2:
        st.session_state.custom_secondary = st.color_picker("Secondary", st.session_state.get("custom_secondary", "#1e40af"))
        st.session_state.custom_surface = st.color_picker("Surface", st.session_state.get("custom_surface", "#ffffff"))
        st.session_state.custom_text = st.color_picker("Text", st.session_state.get("custom_text", "#1f2937"))

    st.session_state.custom_gradient_start = st.sidebar.color_picker("Gradient Start", st.session_state.get("custom_gradient_start", "#667eea"))
    st.session_state.custom_gradient_end = st.sidebar.color_picker("Gradient End", st.session_state.get("custom_gradient_end", "#764ba2"))

    if st.sidebar.button("🔄 Apply Custom Theme"):
        st.rerun()

# OpenAI API Key
api_key = st.sidebar.text_input("OpenAI API Key",
                               value=config.get("openai_api_key", ""),
                               type="password",
                               help="Get your API key from https://platform.openai.com/api-keys")

if api_key != config.get("openai_api_key", ""):
    config["openai_api_key"] = api_key
    save_config(config)

# Main app tabs
tab_checkin, tab_hints, tab_trends, tab_chat = st.tabs(["📝 Check-in", "💡 Hints", "📊 Trends", "💬 Chat"])

# Tab 1: Check-in
with tab_checkin:
    st.header("How are you feeling right now?")

    # Date selection and note
    col1, col2 = st.columns([2, 1])
    with col1:
        note = st.text_area("How is today?", placeholder="Add any details about your day...", height=120)
    with col2:
        selected_date = st.date_input("📅 Check-in date", value=date.today(), max_value=date.today())

    # Mood slider with dynamic color
    def get_slider_color(value, theme_name):
        """Get color for slider based on mood value and current theme"""
        if theme_name == "🎨 Custom":
            # Use custom colors from session state
            theme = {
                "mood_colors": ["#1e40af", "#2563eb", "#3b82f6", "#60a5fa", "#93c5fd", "#dbeafe"]
            }
        else:
            theme = THEMES.get(theme_name, THEMES["🌊 Ocean"])

        mood_colors = theme["mood_colors"]

        if value == 0:
            return mood_colors[0]
        elif value <= 2:
            return mood_colors[1]
        elif value <= 4:
            return mood_colors[2]
        elif value <= 6:
            return mood_colors[3]
        elif value <= 8:
            return mood_colors[4]
        else:
            return mood_colors[5]

    slider_color = get_slider_color(5, st.session_state.current_theme)  # Default color

    # Add dynamic CSS for slider color
    st.markdown(f"""
    <style>
    :root {{
        --slider-color: {slider_color};
        --slider-track-color: {slider_color}40;
    }}
    </style>
    """, unsafe_allow_html=True)

    mood = st.slider("Mood (0 = very low, 10 = very high)", 0, 10, 5)

    # Update slider color based on current value
    current_slider_color = get_slider_color(mood, st.session_state.current_theme)
    st.markdown(f"""
    <style>
    :root {{
        --slider-color: {current_slider_color};
        --slider-track-color: {current_slider_color}40;
    }}
    </style>
    """, unsafe_allow_html=True)

    # Update session state when slider changes
    if mood != st.session_state.mood_value:
        st.session_state.mood_value = mood
        st.rerun()

    emoji, label, color = get_mood_emoji_and_label(mood)
    st.markdown(f"""
    <div class="mood-display" style="background: linear-gradient(135deg, {color}20, {color}10); border: 2px solid {color}40;">
        <span style="font-size: 2rem; margin-right: 12px;">{emoji}</span>
        <span style="color: {color}; font-weight: 700;">{label}</span>
    </div>
    """, unsafe_allow_html=True)

    # Tags
    st.caption("Quick tags (click to add):")
    tag_cols = st.columns(6)

    for i, (emoji_tag, tag) in enumerate(TAG_PALETTE):
        if tag_cols[i % 6].button(f"{emoji_tag} {tag}", key=f"tag_{tag}"):
            if tag in st.session_state.selected_tags:
                st.session_state.selected_tags.remove(tag)
            else:
                st.session_state.selected_tags.add(tag)
            st.rerun()

    # Display selected tags
    if st.session_state.selected_tags:
        st.markdown("**Selected tags:**")
        tags_html = ""
        for tag in sorted(st.session_state.selected_tags):
            tags_html += f'<span class="tag-chip">{tag}</span>'
        st.markdown(tags_html, unsafe_allow_html=True)

    # Manual tags
    manual_tags = st.text_input("Additional tags (comma-separated)",
                               value=", ".join(sorted(st.session_state.selected_tags)))

    # Update selected tags from manual input
    if manual_tags:
        st.session_state.selected_tags = set([t.strip() for t in manual_tags.split(",") if t.strip()])

    # Helpful hint and AI suggestion
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**💡 Helpful Hint**")
        hint = get_helpful_hint(mood, note)
        st.write(hint)

    with col2:
        st.markdown("**🤖 AI Suggestion**")
        if api_key:
            # Debounced AI calls (prevent too frequent API calls)
            current_time = time.time()
            if current_time - st.session_state.last_ai_call > 2:  # 2 second debounce
                ai_suggestion = get_ai_suggestion(mood, note, api_key)
                st.session_state.last_ai_call = current_time
                st.session_state.current_ai_suggestion = ai_suggestion
            else:
                ai_suggestion = st.session_state.get("current_ai_suggestion", "")

            if ai_suggestion:
                st.markdown(f"""
                <div class="ai-suggestion-box">
                    <div style="text-align: center;">{ai_suggestion}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Move the mood slider to get AI suggestions")
        else:
            st.info("Add your OpenAI API key in the sidebar to enable AI suggestions")

    # Submit button
    if st.button("Submit Check-in", type="primary"):
        # Save the check-in
        new_entry = {
            "date": selected_date,
            "mood_score": mood,
            "note": note,
            "tags": manual_tags,
            "ai_suggestion": st.session_state.get("current_ai_suggestion", ""),
            "helpful_hint": hint,
            "timestamp": datetime.now().isoformat()
        }

        data.append(new_entry)
        save_data(data)

        st.success(f"Check-in saved for {selected_date.strftime('%B %d, %Y')}!")

        # Reset form
        st.session_state.selected_tags = set()
        st.rerun()

# Tab 2: Hints
with tab_hints:
    st.header("💡 Helpful Hints")

    # Search functionality
    search_query = st.text_input("🔍 Search hints", placeholder="Search by note, hint, or AI suggestion...")

    # Get all hints from data
    hints_data = []
    for entry in data:
        if entry.get('helpful_hint') or entry.get('ai_suggestion'):
            hints_data.append({
                'Date': entry.get('date', 'Unknown'),
                'Mood': entry.get('mood_score', 0),
                'Note': entry.get('note', '')[:100] + ('...' if len(entry.get('note', '')) > 100 else ''),
                'Helpful Hint': entry.get('helpful_hint', ''),
                'AI Suggestion': entry.get('ai_suggestion', '')
            })

    # Filter hints based on search
    if search_query:
        filtered_hints = []
        for hint in hints_data:
            if (search_query.lower() in hint['Note'].lower() or
                search_query.lower() in hint['Helpful Hint'].lower() or
                search_query.lower() in hint['AI Suggestion'].lower()):
                filtered_hints.append(hint)
        hints_data = filtered_hints

    if hints_data:
        # Reverse to show most recent first
        hints_df = pd.DataFrame(hints_data[::-1])
        st.dataframe(hints_df, use_container_width=True, hide_index=True)
    else:
        st.info("No hints found" + (f" matching '{search_query}'" if search_query else "") + ". Complete some check-ins to see helpful hints here!")

# Tab 3: Trends
with tab_trends:
    st.header("📊 Your Mood Trends")

    if not data:
        st.info("No check-ins yet. Complete your first check-in to see trends!")
    else:
        # Convert data to DataFrame
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')

        # Calculate streak
        dates = sorted([entry['date'] for entry in data])
        streak = 0
        current_date = date.today()
        while current_date in dates:
            streak += 1
            current_date = current_date - timedelta(days=1)

        # Stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Current Streak", f"{streak} days")
        with col2:
            st.metric("Total Check-ins", len(data))
        with col3:
            avg_mood = sum(entry['mood_score'] for entry in data) / len(data)
            st.metric("Average Mood", f"{avg_mood:.1f}")
        with col4:
            recent_avg = sum(entry['mood_score'] for entry in data[-7:]) / min(len(data), 7)
            st.metric("Last 7 Days", f"{recent_avg:.1f}")

        # Daily mood chart
        st.subheader("Daily Mood")
        fig = px.line(df, x='date', y='mood_score',
                     title="Mood Over Time",
                     labels={'mood_score': 'Mood Score', 'date': 'Date'},
                     range_y=[0, 10])
        fig.add_hline(y=5, line_dash="dash", line_color="gray",
                     annotation_text="Neutral")
        st.plotly_chart(fig, use_container_width=True)

        # Weekly average
        if len(data) > 7:
            st.subheader("Weekly Average")
            df_weekly = df.set_index('date').resample('W')['mood_score'].mean().reset_index()
            fig_weekly = px.line(df_weekly, x='date', y='mood_score',
                               title="Weekly Average Mood",
                               labels={'mood_score': 'Average Mood', 'date': 'Week'},
                               range_y=[0, 10])
            fig_weekly.add_hline(y=5, line_dash="dash", line_color="gray",
                               annotation_text="Neutral")
            st.plotly_chart(fig_weekly, use_container_width=True)

        # Weekly trend analysis
        if len(data) > 14:  # Need at least 2 weeks for trend
            st.subheader("Weekly Trend Analysis")

            # Calculate weekly averages and trend
            df_weekly_trend = df.set_index('date').resample('W')['mood_score'].mean().reset_index()
            df_weekly_trend['week_number'] = range(1, len(df_weekly_trend) + 1)

            # Create trend chart with both line and trend line
            fig_trend = go.Figure()

            # Add weekly averages
            fig_trend.add_trace(go.Scatter(
                x=df_weekly_trend['date'],
                y=df_weekly_trend['mood_score'],
                mode='lines+markers',
                name='Weekly Average',
                line=dict(color='#3b82f6', width=3),
                marker=dict(size=8)
            ))

            # Add trend line if we have enough data points
            if len(df_weekly_trend) >= 3:
                import numpy as np
                x_numeric = np.arange(len(df_weekly_trend))
                z = np.polyfit(x_numeric, df_weekly_trend['mood_score'], 1)
                p = np.poly1d(z)

                trend_color = '#10b981' if z[0] > 0 else '#3b82f6' if z[0] < 0 else '#6b7280'
                trend_direction = 'Improving' if z[0] > 0 else 'Declining' if z[0] < 0 else 'Stable'

                fig_trend.add_trace(go.Scatter(
                    x=df_weekly_trend['date'],
                    y=p(x_numeric),
                    mode='lines',
                    name=f'Trend ({trend_direction})',
                    line=dict(color=trend_color, width=2, dash='dash')
                ))

            # Add neutral line
            fig_trend.add_hline(y=5, line_dash="dot", line_color="gray",
                              annotation_text="Neutral", annotation_position="bottom right")

            fig_trend.update_layout(
                title="Weekly Mood Trend Analysis",
                xaxis_title="Week",
                yaxis_title="Average Mood Score",
                yaxis=dict(range=[0, 10]),
                hovermode='x unified',
                showlegend=True
            )

            st.plotly_chart(fig_trend, use_container_width=True)

            # Show trend insights
            if len(df_weekly_trend) >= 3:
                recent_weeks = df_weekly_trend.tail(4)
                if len(recent_weeks) >= 2:
                    recent_change = recent_weeks.iloc[-1]['mood_score'] - recent_weeks.iloc[0]['mood_score']
                    if abs(recent_change) > 0.5:
                        trend_emoji = "📈" if recent_change > 0 else "📉"
                        trend_text = "improving" if recent_change > 0 else "declining"
                        st.info(f"{trend_emoji} Your mood has been **{trend_text}** over the last {len(recent_weeks)} weeks (change: {recent_change:+.1f} points)")
                    else:
                        st.info("📊 Your mood has been **stable** over recent weeks")

        # Mood distribution
        st.subheader("Mood Distribution")
        fig_hist = px.histogram(df, x='mood_score', nbins=11,
                              title="How Often You Feel Each Mood Level",
                              labels={'mood_score': 'Mood Score', 'count': 'Number of Days'})
        st.plotly_chart(fig_hist, use_container_width=True)

        # Export data
        st.subheader("Export Data")
        csv_data = df.to_csv(index=False)
        st.download_button("📥 Download CSV", csv_data, "mood_data.csv", "text/csv")

# Tab 4: Chat
with tab_chat:
    st.header("💬 Supportive Chat")

    if not api_key:
        st.info("Add your OpenAI API key in the sidebar to enable chat functionality.")
    else:
        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        # Chat input
        if prompt := st.chat_input("Type your message..."):
            # Add user message
            st.session_state.chat_history.append({"role": "user", "content": prompt})

            with st.chat_message("user"):
                st.write(prompt)

            # Get AI response
            try:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }

                messages = [
                    {"role": "system", "content": "You are a warm, supportive mental health companion. Provide helpful, empathetic responses. Avoid giving medical advice. Encourage professional help when appropriate."}
                ] + st.session_state.chat_history

                data_payload = {
                    "model": "gpt-4o-mini",
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 300
                }

                response = requests.post("https://api.openai.com/v1/chat/completions",
                                       headers=headers, json=data_payload, timeout=30)

                if response.status_code == 200:
                    ai_response = response.json()["choices"][0]["message"]["content"]
                    st.session_state.chat_history.append({"role": "assistant", "content": ai_response})

                    with st.chat_message("assistant"):
                        st.write(ai_response)
                else:
                    st.error(f"AI temporarily unavailable (Error {response.status_code})")

            except Exception as e:
                st.error(f"Chat error: {str(e)}")

        # Clear chat button
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()

# Footer
st.markdown("---")
st.markdown("💙 **Simple Mood Tracker** - Take care of yourself, one day at a time.")
