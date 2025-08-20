"""
MOOD TRACKER APP - SIMPLIFIED VERSION
====================================
This simplified version removes the complex MoodHelper class and replaces it with
simple functions while maintaining all functionality.
"""
import streamlit as st# Simple Mood Tracking App - Supabase Version
# Run with: streamlit run simple_mood_app_supabase.py

import streamlit as st
import pandas as pd
import json
import os
import requests
import time
from datetime import date, datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client, Client

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
        st.rerun()

# Supabase configuration
@st.cache_resource
def init_supabase():
    """Initialize Supabase client"""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["anon_key"]
    return create_client(url, key)

supabase: Client = init_supabase()

def load_data_from_supabase(user_email):
    """Load mood data from Supabase"""
    try:
        response = supabase.table("mood_entries").select("*").eq("user_email", user_email).order("date", desc=False).execute()

        data = []
        for entry in response.data:
            # Convert date string back to date object
            entry_data = {
                "date": datetime.strptime(entry["date"], '%Y-%m-%d').date(),
                "mood_score": entry["mood_score"],
                "note": entry["note"],
                "tags": entry["tags"],
                "ai_suggestion": entry.get("ai_suggestion", ""),
                "helpful_hint": entry.get("helpful_hint", ""),
                "timestamp": entry.get("timestamp", "")
            }
            data.append(entry_data)

        return data
    except Exception as e:
        st.error(f"Error loading data from Supabase: {str(e)}")
        return []

def save_data_to_supabase(user_email, entry_data):
    """Save a single mood entry to Supabase"""
    try:
        # Prepare data for Supabase
        supabase_entry = {
            "user_email": user_email,
            "date": entry_data["date"].strftime('%Y-%m-%d') if isinstance(entry_data["date"], date) else entry_data["date"],
            "mood_score": entry_data["mood_score"],
            "note": entry_data["note"],
            "tags": entry_data["tags"],
            "ai_suggestion": entry_data.get("ai_suggestion", ""),
            "helpful_hint": entry_data.get("helpful_hint", ""),
            "timestamp": entry_data.get("timestamp", datetime.now().isoformat())
        }

        # Check if entry already exists for this date
        existing = supabase.table("mood_entries").select("id").eq("user_email", user_email).eq("date", supabase_entry["date"]).execute()

        if existing.data:
            # Update existing entry
            response = supabase.table("mood_entries").update(supabase_entry).eq("user_email", user_email).eq("date", supabase_entry["date"]).execute()
        else:
            # Insert new entry
            response = supabase.table("mood_entries").insert(supabase_entry).execute()

        return True
    except Exception as e:
        st.error(f"Error saving data to Supabase: {str(e)}")
        return False

def load_config_from_supabase(user_email):
    """Load app configuration from Supabase"""
    try:
        response = supabase.table("user_configs").select("*").eq("user_email", user_email).execute()

        if response.data:
            return response.data[0]["config"]
        else:
            return {"theme": "🌊 Ocean"}
    except Exception as e:
        st.error(f"Error loading config from Supabase: {str(e)}")
        return {"theme": "🌊 Ocean"}

def get_global_openai_key():
    """Get global OpenAI API key from secrets"""
    try:
        # Try different possible key locations in secrets
        if "openai_api_key" in st.secrets:
            # Direct key in secrets
            key = st.secrets["openai_api_key"]
        elif "openai" in st.secrets and "openai_api_key" in st.secrets["openai"]:
            # Key in [openai] section
            key = st.secrets["openai"]["openai_api_key"]
        elif "openai" in st.secrets and "api_key" in st.secrets["openai"]:
            # Alternative key name in [openai] section
            key = st.secrets["openai"]["api_key"]
        else:
            return ""

        return key.strip() if key else ""
    except Exception as e:
        # For debugging - you can remove this later
        st.sidebar.error(f"Error accessing OpenAI key: {str(e)}")
        return ""

def save_config_to_supabase(user_email, config):
    """Save app configuration to Supabase"""
    try:
        # Check if config already exists
        existing = supabase.table("user_configs").select("id").eq("user_email", user_email).execute()

        config_data = {
            "user_email": user_email,
            "config": config
        }

        if existing.data:
            # Update existing config
            response = supabase.table("user_configs").update(config_data).eq("user_email", user_email).execute()
        else:
            # Insert new config
            response = supabase.table("user_configs").insert(config_data).execute()

        return True
    except Exception as e:
        st.error(f"Error saving config to Supabase: {str(e)}")
        return False

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

    /* Tag remove button styling */
    .stButton>button[key*="remove_"] {{
        background-color: #fee2e2 !important;
        border-color: #fca5a5 !important;
        color: #dc2626 !important;
        font-size: 0.85rem !important;
        min-height: 32px !important;
        padding: 4px 8px !important;
        margin: 2px !important;
    }}

    .stButton>button[key*="remove_"]:hover {{
        background-color: #fecaca !important;
        border-color: #f87171 !important;
        color: #b91c1c !important;
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

# Load data and config from Supabase
data = load_data_from_supabase(user_email)
config = load_config_from_supabase(user_email)

# Get global OpenAI API key
api_key = get_global_openai_key()

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
    save_config_to_supabase(user_email, config)
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

# Show AI status in sidebar
if api_key:
    st.sidebar.success("🤖 AI Features Enabled")
    # Debug info - remove this later
    st.sidebar.info(f"Key length: {len(api_key)} chars")
else:
    st.sidebar.warning("🤖 AI Features Disabled")
    # Debug info - remove this later
    st.sidebar.info("No API key found in secrets")

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

    # Display selected tags with remove buttons
    if st.session_state.selected_tags:
        st.markdown("**Selected tags:**")

        # Create columns for tag removal buttons
        tags_list = sorted(st.session_state.selected_tags)
        if tags_list:
            # Display tags in rows of 4
            for i in range(0, len(tags_list), 4):
                cols = st.columns(4)
                for j, tag in enumerate(tags_list[i:i+4]):
                    with cols[j]:
                        if st.button(f"❌ {tag}", key=f"remove_{tag}", help=f"Remove {tag}"):
                            st.session_state.selected_tags.remove(tag)
                            st.rerun()

    # Manual tags input
    manual_tags = st.text_input("Additional tags (comma-separated)",
                               value=", ".join(sorted(st.session_state.selected_tags)),
                               help="Type additional tags separated by commas, or edit existing ones")

    # Update selected tags from manual input
    if manual_tags:
        new_tags = set([t.strip() for t in manual_tags.split(",") if t.strip()])
        if new_tags != st.session_state.selected_tags:
            st.session_state.selected_tags = new_tags

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
            st.info("AI suggestions are currently disabled - contact admin to enable")

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

        if save_data_to_supabase(user_email, new_entry):
            st.success(f"Check-in saved for {selected_date.strftime('%B %d, %Y')}!")

            # Reset form
            st.session_state.selected_tags = set()
            st.rerun()
        else:
            st.error("Failed to save check-in. Please try again.")

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
        st.info("Chat functionality is currently disabled - contact admin to enable AI features.")
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

import pandas as pd
import json
import os
import requests
import time
from datetime import date, datetime, timedelta
from typing import List, Dict, Tuple, Optional
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client, Client

# ============================================================================
# 1. CONFIGURATION & CONSTANTS
# ============================================================================

# App Configuration
APP_CONFIG = {
    "page_title": "Daily Mood Check-in",
    "page_icon": "😊",
    "layout": "centered"
}

# UI Layout Constants - MODIFY THESE FOR DIFFERENT UI STYLES
UI_LAYOUT = {
    "sidebar_width": 300,
    "main_columns": [2, 1],  # Ratio for main content columns
    "tag_columns": 6,  # Number of tag columns
    "stats_columns": 4,  # Number of stat metric columns
    "color_picker_columns": 2,  # Color picker layout
    "tags_per_row": 4  # Tags displayed per row
}

# Content Text - MODIFY FOR DIFFERENT MESSAGING
CONTENT_TEXT = {
    "main_header": "How are you feeling right now?",
    "note_placeholder": "Add any details about your day...",
    "mood_slider_label": "Mood (0 = very low, 10 = very high)",
    "tags_caption": "Quick tags (click to add):",
    "selected_tags_label": "**Selected tags:**",
    "manual_tags_label": "Additional tags (comma-separated)",
    "submit_button": "Submit Check-in",
    "success_message": "Check-in saved for {}!",
    "error_message": "Failed to save check-in. Please try again."
}

# Tag Palette - EASILY MODIFY TAGS HERE
TAG_PALETTE = [
    ("😊", "happy"), ("😔", "sad"), ("😰", "anxious"), ("😴", "sleep"),
    ("🏃‍♂️", "exercise"), ("💼", "work"), ("🍽️", "meals"), ("☀️", "sunlight"),
    ("🌧️", "rainy"), ("🤝", "social"), ("📚", "study"), ("🎵", "music"),
    ("👨‍👩‍👧", "Family"), ("🧘", "Quiet time"), ("📖", "reading"), ("🎮", "Gaming"),
    ("📺", "TV"), ("📱", "Social Media")
]

# Mood Scale Configuration - MODIFY FOR DIFFERENT MOOD SCALES
MOOD_SCALE = {
    "min_value": 0,
    "max_value": 10,
    "default_value": 5,
    "labels": {
        1: ("😢", "Very Low"),
        3: ("😔", "Low"),
        4: ("😐", "Below Average"),
        6: ("🙂", "Okay"),
        8: ("😊", "Good"),
        10: ("😄", "Great")
    }
}

# ============================================================================
# 2. SIMPLIFIED MOOD FUNCTIONS (REPLACING MoodHelper CLASS)
# ============================================================================

def get_mood_info(mood_score: int) -> Tuple[str, str, str]:
    """Get emoji, label, and color for mood score"""
    current_theme = st.session_state.get("current_theme", "🌊 Ocean")
    
    # Simple mood mapping
    if mood_score <= 2:
        emoji, label = "😢", "Very Low"
    elif mood_score <= 4:
        emoji, label = "😔", "Low"
    elif mood_score <= 6:
        emoji, label = "😐", "Neutral"
    elif mood_score <= 8:
        emoji, label = "😊", "Good"
    else:
        emoji, label = "😄", "Great"
    
    # Get theme color
    theme_colors = UIThemes.get_theme(current_theme)
    color = theme_colors["primary"]
    
    return emoji, label, color



# ============================================================================
# 3. UI THEMES & STYLING - MODIFY FOR DIFFERENT LOOK & FEEL
# ============================================================================

class UIThemes:
    """Centralized theme management for easy UI customization"""
    
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
    
    @staticmethod
    def get_theme(theme_name):
        """Get theme configuration"""
        return UIThemes.THEMES.get(theme_name, UIThemes.THEMES["🌊 Ocean"])
    
    @staticmethod
    def apply_theme_css(theme_name):
        """Apply CSS for selected theme - MODIFY FOR DIFFERENT STYLING"""
        if theme_name == "🎨 Custom":
            theme = UIThemes._get_custom_theme()
        else:
            theme = UIThemes.get_theme(theme_name)
        
        css = f"""
        <style>
        .main-header {{
            background: linear-gradient(135deg, {theme['gradient_start']}, {theme['gradient_end']});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.5rem;
            font-weight: bold;
            text-align: center;
            margin-bottom: 2rem;
        }}
        
        .mood-display {{
            text-align: center;
            padding: 1rem;
            border-radius: 10px;
            background-color: {theme['surface']};
            border: 2px solid {theme['accent']};
            margin: 1rem 0;
        }}
        
        .mood-emoji {{
            font-size: 3rem;
            margin-bottom: 0.5rem;
        }}
        
        .mood-label {{
            font-size: 1.2rem;
            color: {theme['primary']};
            font-weight: bold;
        }}
        
        .stButton > button {{
            background-color: {theme['primary']};
            color: white;
            border: none;
            border-radius: 5px;
            padding: 0.5rem 1rem;
            transition: all 0.3s ease;
        }}
        
        .stButton > button:hover {{
            background-color: {theme['secondary']};
            transform: translateY(-2px);
        }}
        
        .tag-button {{
            background-color: {theme['accent']};
            color: {theme['text']};
            border: 1px solid {theme['primary']};
            border-radius: 20px;
            padding: 0.3rem 0.8rem;
            margin: 0.2rem;
            font-size: 0.9rem;
        }}
        
        .stats-container {{
            background-color: {theme['surface']};
            padding: 1rem;
            border-radius: 10px;
            border: 1px solid {theme['accent']};
            margin: 1rem 0;
        }}
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    
    @staticmethod
    def _get_custom_theme():
        """Get custom theme from session state"""
        return {
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

# ============================================================================
# 4. UI COMPONENTS - MODIFY THESE FOR DIFFERENT UI LAYOUTS
# ============================================================================

class UIComponents:
    """Reusable UI components for consistent styling"""
    
    @staticmethod
    def render_mood_display(mood_score):
        """Render mood emoji and label - CUSTOMIZE MOOD DISPLAY HERE"""
        emoji, label, color = get_mood_info(mood_score)
        st.markdown(f"""
        <div class="mood-display">
            <div class="mood-emoji">{emoji}</div>
            <div class="mood-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_tag_selector():
        """Render tag selection interface - CUSTOMIZE TAG LAYOUT HERE"""
        st.caption(CONTENT_TEXT["tags_caption"])
        
        # Create tag grid
        tag_cols = st.columns(UI_LAYOUT["tag_columns"])
        for i, (emoji_tag, tag) in enumerate(TAG_PALETTE):
            col_index = i % UI_LAYOUT["tag_columns"]
            if tag_cols[col_index].button(f"{emoji_tag} {tag}", key=f"tag_{tag}"):
                UIComponents._toggle_tag(tag)
                st.rerun()
    
    @staticmethod
    def render_selected_tags():
        """Render selected tags with remove buttons - CUSTOMIZE TAG DISPLAY HERE"""
        if st.session_state.selected_tags:
            st.markdown(CONTENT_TEXT["selected_tags_label"])
            tags_list = sorted(st.session_state.selected_tags)
            
            # Display tags in rows
            for i in range(0, len(tags_list), UI_LAYOUT["tags_per_row"]):
                cols = st.columns(UI_LAYOUT["tags_per_row"])
                for j, tag in enumerate(tags_list[i:i+UI_LAYOUT["tags_per_row"]]):
                    with cols[j]:
                        if st.button(f"❌ {tag}", key=f"remove_{tag}", help=f"Remove {tag}"):
                            st.session_state.selected_tags.remove(tag)
                            st.rerun()
    
    @staticmethod
    def render_stats_row(data):
        """Render statistics row - CUSTOMIZE STATS DISPLAY HERE"""
        if not data:
            return
        
        # Calculate stats
        stats = DataManager.calculate_stats(data)
        
        # Display in columns
        cols = st.columns(UI_LAYOUT["stats_columns"])
        with cols[0]:
            st.metric("Current Streak", f"{stats['streak']} days")
        with cols[1]:
            st.metric("Total Check-ins", stats['total_checkins'])
        with cols[2]:
            st.metric("Average Mood", f"{stats['avg_mood']:.1f}")
        with cols[3]:
            st.metric("Last 7 Days", f"{stats['recent_avg']:.1f}")
    
    @staticmethod
    def render_theme_selector():
        """Render theme selection interface - CUSTOMIZE THEME PICKER HERE"""
        st.sidebar.subheader("🎨 Theme")
        theme_options = list(UIThemes.THEMES.keys()) + ["🎨 Custom"]
        selected_theme = st.sidebar.selectbox(
            "Choose your theme:",
            theme_options,
            index=theme_options.index(st.session_state.current_theme) if st.session_state.current_theme in theme_options else 0,
            help="Select a theme to change the app's appearance instantly!"
        )
        return selected_theme
    
    @staticmethod
    def render_custom_theme_picker():
        """Render custom theme color pickers - CUSTOMIZE COLOR PICKER LAYOUT HERE"""
        if st.session_state.current_theme == "🎨 Custom":
            st.sidebar.subheader("🎨 Custom Colors")
            col1, col2 = st.sidebar.columns(UI_LAYOUT["color_picker_columns"])
            
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
    
    @staticmethod
    def _toggle_tag(tag):
        """Toggle tag selection"""
        if tag in st.session_state.selected_tags:
            st.session_state.selected_tags.remove(tag)
        else:
            st.session_state.selected_tags.add(tag)

# ============================================================================
# 5. DATA MANAGEMENT - BUSINESS LOGIC SEPARATED FROM UI
# ============================================================================

class DataManager:
    """Handle all data operations"""
    
    @staticmethod
    @st.cache_resource
    def init_supabase():
        """Initialize Supabase client"""
        try:
            url = st.secrets["supabase"]["url"]
            key = st.secrets["supabase"]["anon_key"]
            return create_client(url, key)
        except Exception as e:
            st.error(f"Error initializing Supabase: {str(e)}")
            st.error("Please check your Supabase configuration in secrets.toml")
            return None
    
    @staticmethod
    def load_user_data(user_email):
        """Load mood data from Supabase"""
        try:
            supabase = DataManager.init_supabase()
            if not supabase:
                return []
            response = supabase.table("mood_entries").select("*").eq("user_email", user_email).order("date", desc=False).execute()
            
            data = []
            for entry in response.data:
                entry_data = {
                    "date": datetime.strptime(entry["date"], '%Y-%m-%d').date(),
                    "mood_score": entry["mood_score"],
                    "note": entry["note"],
                    "tags": entry["tags"],
                    "ai_suggestion": entry.get("ai_suggestion", ""),
                    "helpful_hint": entry.get("helpful_hint", ""),
                    "timestamp": entry.get("timestamp", "")
                }
                data.append(entry_data)
            return data
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            return []
    
    @staticmethod
    def save_entry(user_email, entry_data):
        """Save mood entry to Supabase"""
        try:
            supabase = DataManager.init_supabase()
            if not supabase:
                return False
            supabase_entry = {
                "user_email": user_email,
                "date": entry_data["date"].strftime('%Y-%m-%d') if isinstance(entry_data["date"], date) else entry_data["date"],
                "mood_score": entry_data["mood_score"],
                "note": entry_data["note"],
                "tags": entry_data["tags"],
                "ai_suggestion": entry_data.get("ai_suggestion", ""),
                "helpful_hint": entry_data.get("helpful_hint", ""),
                "timestamp": entry_data.get("timestamp", datetime.now().isoformat())
            }
            
            # Check if entry exists
            existing = supabase.table("mood_entries").select("id").eq("user_email", user_email).eq("date", supabase_entry["date"]).execute()
            
            if existing.data:
                response = supabase.table("mood_entries").update(supabase_entry).eq("user_email", user_email).eq("date", supabase_entry["date"]).execute()
            else:
                response = supabase.table("mood_entries").insert(supabase_entry).execute()
            
            return True
        except Exception as e:
            st.error(f"Error saving data: {str(e)}")
            return False
    
    @staticmethod
    def load_user_config(user_email):
        """Load user configuration"""
        try:
            supabase = DataManager.init_supabase()
            if not supabase:
                return {"theme": "🌊 Ocean"}
            response = supabase.table("user_configs").select("*").eq("user_email", user_email).execute()
            
            if response.data:
                return response.data[0]["config"]
            else:
                return {"theme": "🌊 Ocean"}
        except Exception as e:
            st.error(f"Error loading config: {str(e)}")
            return {"theme": "🌊 Ocean"}
    
    @staticmethod
    def save_user_config(user_email, config):
        """Save user configuration"""
        try:
            supabase = DataManager.init_supabase()
            if not supabase:
                return False
            existing = supabase.table("user_configs").select("id").eq("user_email", user_email).execute()
            
            config_data = {"user_email": user_email, "config": config}
            
            if existing.data:
                response = supabase.table("user_configs").update(config_data).eq("user_email", user_email).execute()
            else:
                response = supabase.table("user_configs").insert(config_data).execute()
            
            return True
        except Exception as e:
            st.error(f"Error saving config: {str(e)}")
            return False
    
    @staticmethod
    def calculate_stats(data):
        """Calculate mood statistics"""
        if not data:
            return {"streak": 0, "total_checkins": 0, "avg_mood": 0, "recent_avg": 0}
        
        # Calculate streak
        dates = sorted([entry['date'] for entry in data])
        streak = 0
        current_date = date.today()
        while current_date in dates:
            streak += 1
            current_date = current_date - timedelta(days=1)
        
        # Calculate averages
        total_checkins = len(data)
        avg_mood = sum(entry['mood_score'] for entry in data) / total_checkins
        recent_avg = sum(entry['mood_score'] for entry in data[-7:]) / min(total_checkins, 7)
        
        return {
            "streak": streak,
            "total_checkins": total_checkins,
            "avg_mood": avg_mood,
            "recent_avg": recent_avg
        }

# ============================================================================
# 6. AI INTEGRATION - SIMPLIFIED
# ============================================================================

def get_ai_suggestion(mood_score, note_text, tags):
    """Get AI suggestion using OpenAI API"""
    try:
        # Try to get API key from secrets first, then session state
        api_key = None
        if "openai" in st.secrets and "api_key" in st.secrets["openai"]:
            api_key = st.secrets["openai"]["api_key"]
        else:
            api_key = st.session_state.get("openai_api_key")
        
        if not api_key:
            return "Add your OpenAI API key in the sidebar to get personalized AI suggestions!"
        
        # Create context from mood data
        emoji, mood_label, _ = get_mood_info(mood_score)
        context = f"Mood: {mood_score}/10 ({mood_label} {emoji})"
        if note_text:
            context += f"\nNote: {note_text}"
        if tags:
            context += f"\nTags: {', '.join(tags)}"
        
        # Simple prompt for AI
        prompt = f"""Based on this mood check-in, provide a brief, supportive suggestion (2-3 sentences max):

{context}

Provide a helpful, empathetic response that acknowledges their current state and offers a gentle suggestion."""
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 150,
            "temperature": 0.7
        }
        
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()
        else:
            return "Unable to get AI suggestion at the moment. Try again later!"
            
    except Exception as e:
        return f"AI suggestion unavailable: {str(e)}"

# ============================================================================
# 7. VISUALIZATION FUNCTIONS
# ============================================================================

def create_mood_chart(data):
    """Create mood trend chart"""
    if not data:
        return None
    
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Create line chart
    fig = px.line(df, x='date', y='mood_score', 
                  title='Mood Trend Over Time',
                  labels={'mood_score': 'Mood Score', 'date': 'Date'},
                  line_shape='spline')
    
    fig.update_traces(line_color='#3b82f6', line_width=3)
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#1f2937',
        title_font_size=20,
        title_x=0.5
    )
    
    return fig

def create_mood_distribution(data):
    """Create mood distribution chart"""
    if not data:
        return None
    
    df = pd.DataFrame(data)
    
    # Create histogram
    fig = px.histogram(df, x='mood_score', nbins=11,
                      title='Mood Distribution',
                      labels={'mood_score': 'Mood Score', 'count': 'Frequency'})
    
    fig.update_traces(marker_color='#3b82f6', opacity=0.7)
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#1f2937',
        title_font_size=20,
        title_x=0.5
    )
    
    return fig

# ============================================================================
# 8. MAIN APPLICATION
# ============================================================================

def init_session_state():
    """Initialize session state variables"""
    if "selected_tags" not in st.session_state:
        st.session_state.selected_tags = set()
    if "current_theme" not in st.session_state:
        st.session_state.current_theme = "🌊 Ocean"
    if "user_email" not in st.session_state:
        st.session_state.user_email = ""
    if "openai_api_key" not in st.session_state:
        st.session_state.openai_api_key = ""

def render_sidebar():
    """Render sidebar with configuration options"""
    st.sidebar.title("⚙️ Settings")
    
    # User email input
    user_email = st.sidebar.text_input(
        "📧 Your Email",
        value=st.session_state.user_email,
        help="Used to save your mood data"
    )
    st.session_state.user_email = user_email
    
    # OpenAI API key input
    api_key = st.sidebar.text_input(
        "🤖 OpenAI API Key",
        type="password",
        value=st.session_state.openai_api_key,
        help="Add your OpenAI API key for AI suggestions"
    )
    st.session_state.openai_api_key = api_key
    
    # Theme selection
    selected_theme = UIComponents.render_theme_selector()
    if selected_theme != st.session_state.current_theme:
        st.session_state.current_theme = selected_theme
        st.rerun()
    
    # Custom theme picker
    UIComponents.render_custom_theme_picker()
    
    # Instructions
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📝 How to use:")
    st.sidebar.markdown("1. Set your mood on the slider")
    st.sidebar.markdown("2. Add tags and notes")
    st.sidebar.markdown("3. Submit your check-in")
    st.sidebar.markdown("4. View your trends over time")

def render_main_content():
    """Render main content area"""
    # Apply theme
    UIThemes.apply_theme_css(st.session_state.current_theme)
    
    # Main header
    st.markdown('<h1 class="main-header">How are you feeling right now?</h1>', unsafe_allow_html=True)
    
    # Check if user email is provided
    if not st.session_state.user_email:
        st.warning("Please enter your email in the sidebar to save your mood data.")
        return
    
    # Load user data
    user_data = DataManager.load_user_data(st.session_state.user_email)
    
    # Display stats if data exists
    if user_data:
        UIComponents.render_stats_row(user_data)
    
    # Mood input section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Mood slider
        mood_score = st.slider(
            CONTENT_TEXT["mood_slider_label"],
            min_value=MOOD_SCALE["min_value"],
            max_value=MOOD_SCALE["max_value"],
            value=MOOD_SCALE["default_value"],
            help="Rate your current mood from 0 (very low) to 10 (very high)"
        )
        
        # Note input
        note_text = st.text_area(
            "📝 Notes (optional)",
            placeholder=CONTENT_TEXT["note_placeholder"],
            height=100
        )
        
        # Tag selection
        UIComponents.render_tag_selector()
        UIComponents.render_selected_tags()
        
        # Manual tags
        manual_tags = st.text_input(
            CONTENT_TEXT["manual_tags_label"],
            placeholder="happy, productive, grateful..."
        )
    
    with col2:
        # Mood display
        UIComponents.render_mood_display(mood_score)
    
    # Submit button
    if st.button(CONTENT_TEXT["submit_button"], type="primary", use_container_width=True):
        # Prepare tags
        all_tags = list(st.session_state.selected_tags)
        if manual_tags:
            manual_tag_list = [tag.strip() for tag in manual_tags.split(",") if tag.strip()]
            all_tags.extend(manual_tag_list)
        
        # Get AI suggestion
        ai_suggestion = get_ai_suggestion(mood_score, note_text, all_tags)
        
        # Prepare entry data
        entry_data = {
            "date": date.today(),
            "mood_score": mood_score,
            "note": note_text,
            "tags": all_tags,
            "ai_suggestion": ai_suggestion,
            "helpful_hint": "",
            "timestamp": datetime.now().isoformat()
        }
        
        # Save entry
        if DataManager.save_entry(st.session_state.user_email, entry_data):
            st.success(CONTENT_TEXT["success_message"].format(date.today().strftime("%B %d, %Y")))
            
            # Show AI suggestion
            if ai_suggestion and "API key" not in ai_suggestion:
                st.markdown("### 🤖 AI Suggestion")
                st.markdown(ai_suggestion)
            
            # Clear selected tags
            st.session_state.selected_tags = set()
            
            # Refresh data
            time.sleep(1)
            st.rerun()
        else:
            st.error(CONTENT_TEXT["error_message"])
    
    # Display charts if data exists
    if user_data and len(user_data) > 1:
        st.markdown("---")
        st.markdown("### 📊 Your Mood Trends")
        
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            mood_chart = create_mood_chart(user_data)
            if mood_chart:
                st.plotly_chart(mood_chart, use_container_width=True)
        
        with chart_col2:
            dist_chart = create_mood_distribution(user_data)
            if dist_chart:
                st.plotly_chart(dist_chart, use_container_width=True)
        
        # Recent entries
        st.markdown("### 📝 Recent Check-ins")
        recent_data = sorted(user_data, key=lambda x: x['date'], reverse=True)[:5]
        
        for entry in recent_data:
            emoji, label, _ = get_mood_info(entry['mood_score'])
            with st.expander(f"{entry['date']} - {emoji} {label} ({entry['mood_score']}/10)"):
                if entry['note']:
                    st.write(f"**Note:** {entry['note']}")
                if entry['tags']:
                    st.write(f"**Tags:** {', '.join(entry['tags'])}")
                if entry.get('ai_suggestion'):
                    st.write(f"**AI Suggestion:** {entry['ai_suggestion']}")

def main():
    """Main application function"""
    # Configure page
    st.set_page_config(
        page_title=APP_CONFIG["page_title"],
        page_icon=APP_CONFIG["page_icon"],
        layout=APP_CONFIG["layout"]
    )
    
    # Initialize session state
    init_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Render main content
    render_main_content()

if __name__ == "__main__":
    main()
