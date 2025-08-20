"""
MOOD TRACKER APP - REFACTORED VERSION
====================================
A clean, well-structured mood tracking app with AI insights.
Organized into clear sections for easy UI modifications.
"""

# ============================================================================
# IMPORTS AND DEPENDENCIES
# ============================================================================
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

# ============================================================================
# AUTHENTICATION SECTION
# ============================================================================
def show_login():
    """Display login interface"""
    st.header("This app is private.")
    st.subheader("Please sign in with Google")
    if st.button("Sign in with Google"):
        st.login()

# Authentication gate
if not st.user.is_logged_in:
    show_login()
    st.stop()
else:
    user_email = st.user.email
    user_name = st.user.name
    st.sidebar.markdown(f"Signed in as **{user_name}** ({user_email})")
    if st.button("Log out"):
        st.logout()
        st.rerun()

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
@st.cache_resource
def init_supabase():
    """Initialize Supabase client"""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["anon_key"]
    return create_client(url, key)

supabase: Client = init_supabase()

# ============================================================================
# DATA MANAGEMENT FUNCTIONS
# ============================================================================
def load_data_from_supabase(user_email):
    """Load mood data from Supabase"""
    try:
        response = supabase.table("mood_entries").select("*").eq("user_email", user_email).order("date", desc=False).execute()
        data = []
        for entry in response.data:
            entry_data = {
                "date": datetime.strptime(entry["date"], '%Y-%m-%d').date(),
                "mood_score": entry["mood_score"],
                "note": entry["note"],
                "tags": entry["tags"],
                "ai_suggestion": entry.get("ai_suggestion", ""),
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
        supabase_entry = {
            "user_email": user_email,
            "date": entry_data["date"].strftime('%Y-%m-%d') if isinstance(entry_data["date"], date) else entry_data["date"],
            "mood_score": entry_data["mood_score"],
            "note": entry_data["note"],
            "tags": entry_data["tags"],
            "ai_suggestion": entry_data.get("ai_suggestion", ""),
            "timestamp": entry_data.get("timestamp", datetime.now().isoformat())
        }
        
        existing = supabase.table("mood_entries").select("id").eq("user_email", user_email).eq("date", supabase_entry["date"]).execute()
        if existing.data:
            response = supabase.table("mood_entries").update(supabase_entry).eq("user_email", user_email).eq("date", supabase_entry["date"]).execute()
        else:
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

def save_config_to_supabase(user_email, config):
    """Save app configuration to Supabase"""
    try:
        existing = supabase.table("user_configs").select("id").eq("user_email", user_email).execute()
        config_data = {
            "user_email": user_email,
            "config": config
        }
        if existing.data:
            response = supabase.table("user_configs").update(config_data).eq("user_email", user_email).execute()
        else:
            response = supabase.table("user_configs").insert(config_data).execute()
        return True
    except Exception as e:
        st.error(f"Error saving config to Supabase: {str(e)}")
        return False

# ============================================================================
# AI INTEGRATION
# ============================================================================
def get_global_openai_key():
    """Get global OpenAI API key from secrets"""
    try:
        if "openai_api_key" in st.secrets:
            key = st.secrets["openai_api_key"]
        elif "openai" in st.secrets and "openai_api_key" in st.secrets["openai"]:
            key = st.secrets["openai"]["openai_api_key"]
        elif "openai" in st.secrets and "api_key" in st.secrets["openai"]:
            key = st.secrets["openai"]["api_key"]
        else:
            return ""
        return key.strip() if key else ""
    except Exception as e:
        st.sidebar.error(f"Error accessing OpenAI key: {str(e)}")
        return ""

def get_ai_suggestion(mood_score, note_text, api_key):
    """Get AI suggestion from OpenAI"""
    if not api_key:
        return ""
    try:
        if mood_score <= 2:
            system_prompt = "You are a gentle, supportive counselor. Provide immediate emotional support with 3-4 sentences. Focus on comfort and small, manageable steps."
        elif mood_score <= 4:
            system_prompt = "You are an encouraging coach. Provide gentle motivation with 3-4 sentences. Focus on small positive actions and building momentum."
        elif mood_score <= 6:
            system_prompt = "You are an upbeat coach. Provide fun suggestions to boost mood with 3-4 sentences. Focus on enjoyable activities."
        else:
            system_prompt = "You are an enthusiastic coach. Celebrate their positive state with 3-4 sentences. Focus on maintaining and sharing positivity."

        user_prompt = f"Someone is feeling {mood_score}/10 today. {f'They shared: {note_text}' if note_text else ''} Please provide a supportive response."

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

# ============================================================================
# UI CONFIGURATION AND THEMES
# ============================================================================
TAG_PALETTE = [
    ("😊", "happy"), ("😔", "sad"), ("😰", "anxious"), ("😴", "sleep"),
    ("🏃‍♂️", "exercise"), ("💼", "work"), ("🍽️", "meals"), ("☀️", "sunlight"),
    ("🌧️", "rainy"), ("🤝", "social"), ("📚", "study"), ("🎵", "music"),
    ("👨‍👩‍👧", "Family"), ("🧘", "Quiet time"), ("📖", "reading"), ("🎮", "Gaming"),
    ("📺", "TV"), ("📱", "Social Media")
]

THEMES = {
    "🌊 Ocean": {
        "primary": "#3b82f6",
        "secondary": "#1e40af",
        "accent": "#60a5fa",
        "background": "#f8fafc",
        "surface": "#ffffff",
        "text": "#1f2937",
        "gradient_start": "#f1f5f9",
        "gradient_end": "#e2e8f0",
        "mood_colors": ["#1e40af", "#2563eb", "#3b82f6", "#60a5fa", "#93c5fd", "#dbeafe"]
    },
    "🌅 Sunrise": {
        "primary": "#f59e0b",
        "secondary": "#d97706",
        "accent": "#fbbf24",
        "background": "#fffbeb",
        "surface": "#ffffff",
        "text": "#92400e",
        "gradient_start": "#fef3c7",
        "gradient_end": "#fed7aa",
        "mood_colors": ["#dc2626", "#ef4444", "#f59e0b", "#fbbf24", "#fde047", "#fef3c7"]
    },
    "🌸 Blossom": {
        "primary": "#ec4899",
        "secondary": "#be185d",
        "accent": "#f472b6",
        "background": "#fdf2f8",
        "surface": "#ffffff",
        "text": "#831843",
        "gradient_start": "#fce7f3",
        "gradient_end": "#f3e8ff",
        "mood_colors": ["#be185d", "#ec4899", "#f472b6", "#f9a8d4", "#fbcfe8", "#fce7f3"]
    },
    "🌿 Nature": {
        "primary": "#10b981",
        "secondary": "#047857",
        "accent": "#34d399",
        "background": "#f0fdf4",
        "surface": "#ffffff",
        "text": "#064e3b",
        "gradient_start": "#ecfdf5",
        "gradient_end": "#d1fae5",
        "mood_colors": ["#047857", "#059669", "#10b981", "#34d399", "#6ee7b7", "#d1fae5"]
    },
    "🌙 Midnight": {
        "primary": "#8b5cf6",
        "secondary": "#7c3aed",
        "accent": "#a78bfa",
        "background": "#0f172a",
        "surface": "#1e293b",
        "text": "#e2e8f0",
        "gradient_start": "#1e293b",
        "gradient_end": "#334155",
        "mood_colors": ["#7c3aed", "#8b5cf6", "#a78bfa", "#c4b5fd", "#ddd6fe", "#ede9fe"]
    }
}

def get_current_theme():
    """Get current theme from session state or default"""
    return st.session_state.get("current_theme", "🌊 Ocean")

def apply_theme_css(theme_name):
    """Apply CSS variables based on selected theme"""
    if theme_name == "🎨 Custom":
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

    st.markdown(f"""
    <style>
    :root {{
        --primary-color: {theme['primary']};
        --secondary-color: {theme['secondary']};
        --accent-color: {theme['accent']};
        --background-color: {theme['background']};
        --surface-color: {theme['surface']};
        --text-color: {theme['text']};
        --gradient-start: {theme['gradient_start']};
        --gradient-end: {theme['gradient_end']};
    }}
    
    .stApp {{
        background: linear-gradient(135deg, {theme['gradient_start']}, {theme['gradient_end']});
        background-attachment: fixed;
    }}
    
    .main .block-container {{
        background-color: {theme['surface']};
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        margin-top: 2rem;
    }}
    
    .mood-display {{
        text-align: center;
        padding: 1rem;
        border-radius: 10px;
        background: linear-gradient(45deg, {theme['primary']}, {theme['accent']});
        color: white;
        margin: 1rem 0;
    }}
    
    .ai-suggestion {{
        background: linear-gradient(45deg, {theme['accent']}, {theme['primary']});
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }}
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# MOOD HELPER FUNCTIONS
# ============================================================================
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

def get_slider_color(value, theme_name):
    """Get color for slider based on mood value and current theme"""
    if theme_name == "🎨 Custom":
        theme = {"mood_colors": ["#1e40af", "#2563eb", "#3b82f6", "#60a5fa", "#93c5fd", "#dbeafe"]}
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

# ============================================================================
# APP INITIALIZATION
# ============================================================================
st.set_page_config(page_title="Daily Mood Check-in", page_icon="😊", layout="centered")

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
data = load_data_from_supabase(user_email)
config = load_config_from_supabase(user_email)
api_key = get_global_openai_key()

# Load theme preference
if "theme" in config:
    st.session_state.current_theme = config["theme"]

apply_theme_css(st.session_state.current_theme)

# ============================================================================
# SIDEBAR CONFIGURATION
# ============================================================================
st.sidebar.header("⚙️ Settings")

# Theme Picker
st.sidebar.subheader("🎨 Theme")
theme_options = list(THEMES.keys()) + ["🎨 Custom"]
selected_theme = st.sidebar.selectbox(
    "Choose your theme:",
    theme_options,
    index=theme_options.index(st.session_state.current_theme) if st.session_state.current_theme in theme_options else 0
)

# Handle theme change
if selected_theme != st.session_state.current_theme:
    st.session_state.current_theme = selected_theme
    config["theme"] = selected_theme
    save_config_to_supabase(user_email, config)
    st.rerun()

# Custom theme color pickers
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

# AI status display
if api_key:
    st.sidebar.success("🤖 AI Features Enabled")
else:
    st.sidebar.warning("🤖 AI Features Disabled")

# ============================================================================
# MAIN APP INTERFACE - TAB STRUCTURE
# ============================================================================
tab_checkin, tab_hints, tab_trends, tab_chat = st.tabs(["📝 Check-in", "💡 Hints", "📊 Trends", "💬 Chat"])

# ============================================================================
# CHECK-IN TAB
# ============================================================================
with tab_checkin:
    st.header("How are you feeling right now?")
    
    # Date and note input section
    col1, col2 = st.columns([2, 1])
    with col1:
        note = st.text_area("How is today?", placeholder="Add any details about your day...", height=120)
    with col2:
        selected_date = st.date_input("📅 Check-in date", value=date.today(), max_value=date.today())
    
    # Mood slider with dynamic styling
    slider_color = get_slider_color(5, st.session_state.current_theme)
    st.markdown(f"""
    <style>
    .stSlider > div > div > div > div {{
        background: linear-gradient(to right, {slider_color}, {slider_color});
    }}
    </style>
    """, unsafe_allow_html=True)
    
    mood = st.slider("Mood (0 = very low, 10 = very high)", 0, 10, 5)
    
    # Update slider color based on current value
    current_slider_color = get_slider_color(mood, st.session_state.current_theme)
    st.markdown(f"""
    <style>
    .stSlider > div > div > div > div {{
        background: linear-gradient(to right, {current_slider_color}, {current_slider_color});
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Update session state when slider changes
    if mood != st.session_state.mood_value:
        st.session_state.mood_value = mood
        st.rerun()
    
    # Mood display
    emoji, label, color = get_mood_emoji_and_label(mood)
    st.markdown(f"""
    <div class="mood-display">
        <h1>{emoji}</h1>
        <h3>{label}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Tags section
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
        tags_list = sorted(st.session_state.selected_tags)
        if tags_list:
            for i in range(0, len(tags_list), 4):
                cols = st.columns(4)
                for j, tag in enumerate(tags_list[i:i+4]):
                    with cols[j]:
                        if st.button(f"❌ {tag}", key=f"remove_{tag}", help=f"Remove {tag}"):
                            st.session_state.selected_tags.remove(tag)
                            st.rerun()
    
    # Manual tags input
    manual_tags = st.text_input("Additional tags (comma-separated)",
                               value=", ".join(sorted(st.session_state.selected_tags)))
    
    # Update selected tags from manual input
    if manual_tags:
        new_tags = set([t.strip() for t in manual_tags.split(",") if t.strip()])
        if new_tags != st.session_state.selected_tags:
            st.session_state.selected_tags = new_tags
    
    # AI suggestion section
    st.markdown("**🤖 AI Suggestion**")
    if api_key:
        current_time = time.time()
        if current_time - st.session_state.last_ai_call > 2:
            ai_suggestion = get_ai_suggestion(mood, note, api_key)
            st.session_state.last_ai_call = current_time
            st.session_state.current_ai_suggestion = ai_suggestion
        else:
            ai_suggestion = st.session_state.get("current_ai_suggestion", "")
        
        if ai_suggestion:
            st.markdown(f"""
            <div class="ai-suggestion">
                {ai_suggestion}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Move the mood slider to get AI suggestions")
    else:
        st.info("AI suggestions are currently disabled - contact admin to enable")
    
    # Submit button
    if st.button("Submit Check-in", type="primary"):
        new_entry = {
            "date": selected_date,
            "mood_score": mood,
            "note": note,
            "tags": manual_tags,
            "ai_suggestion": st.session_state.get("current_ai_suggestion", ""),
            "timestamp": datetime.now().isoformat()
        }
        if save_data_to_supabase(user_email, new_entry):
            st.success(f"Check-in saved for {selected_date.strftime('%B %d, %Y')}!")
            st.session_state.selected_tags = set()
            st.rerun()
        else:
            st.error("Failed to save check-in. Please try again.")

# ============================================================================
# HINTS TAB
# ============================================================================
with tab_hints:
    st.header("💡 Historical AI Suggestions")
    
    # Search functionality
    search_query = st.text_input("🔍 Search suggestions", placeholder="Search by note, or AI suggestion...")
    
    # Get all AI suggestions from data
    hints_data = []
    for entry in data:
        if entry.get('ai_suggestion'):
            hints_data.append({
                'Date': entry.get('date', 'Unknown'),
                'Mood': entry.get('mood_score', 0),
                'Note': entry.get('note', '')[:100] + ('...' if len(entry.get('note', '')) > 100 else ''),
                'AI Suggestion': entry.get('ai_suggestion', '')
            })
    
    # Filter hints based on search
    if search_query:
        filtered_hints = []
        for hint in hints_data:
            if (search_query.lower() in hint['Note'].lower() or
                search_query.lower() in hint['AI Suggestion'].lower()):
                filtered_hints.append(hint)
        hints_data = filtered_hints
    
    if hints_data:
        # Reverse to show most recent first
        hints_df = pd.DataFrame(hints_data[::-1])
        st.dataframe(hints_df, use_container_width=True, hide_index=True)
        
        # Show count
        st.caption(f"Showing {len(hints_data)} AI suggestions" + (f" matching '{search_query}'" if search_query else ""))
    else:
        st.info("No AI suggestions found" + (f" matching '{search_query}'" if search_query else "") + ". Complete some check-ins to see AI suggestions here!")

# ============================================================================
# TRENDS TAB
# ============================================================================
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
        
        # Stats display
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
        fig.add_hline(y=5, line_dash="dash", line_color="gray", annotation_text="Neutral")
        st.plotly_chart(fig, use_container_width=True)
        
        # Weekly average
        if len(data) > 7:
            st.subheader("Weekly Average")
            df_weekly = df.set_index('date').resample('W')['mood_score'].mean().reset_index()
            fig_weekly = px.bar(df_weekly, x='date', y='mood_score',
                               title="Weekly Average Mood",
                               labels={'mood_score': 'Average Mood', 'date': 'Week'})
            st.plotly_chart(fig_weekly, use_container_width=True)
        
        # Recent entries
        st.subheader("Recent Check-ins")
        recent_data = data[-10:][::-1]  # Last 10 entries, most recent first
        for entry in recent_data:
            emoji, label, _ = get_mood_emoji_and_label(entry['mood_score'])
            with st.expander(f"{entry['date']} - {emoji} {label} ({entry['mood_score']}/10)"):
                if entry['note']:
                    st.write(f"**Note:** {entry['note']}")
                if entry['tags']:
                    st.write(f"**Tags:** {entry['tags']}")
                if entry.get('ai_suggestion'):
                    st.write(f"**AI Suggestion:** {entry['ai_suggestion']}")

# ============================================================================
# CHAT TAB
# ============================================================================
with tab_chat:
    st.header("💬 Chat with Your Mood Companion")
    
    if not api_key:
        st.warning("AI chat is currently disabled. Contact admin to enable AI features.")
    else:
        # Display chat history
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f"**You:** {message['content']}")
            else:
                st.markdown(f"**Companion:** {message['content']}")
        
        # Chat input
        user_input = st.text_input("Type your message here...", key="chat_input")
        
        if st.button("Send") and user_input:
            # Add user message to history
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            # Get AI response
            try:
                # Create context from recent mood data
                recent_moods = data[-5:] if data else []
                context = f"Recent mood scores: {[entry['mood_score'] for entry in recent_moods]}"
                
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                chat_data = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": f"You are a supportive mood companion. Be empathetic and helpful. Context: {context}"},
                        {"role": "user", "content": user_input}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 300
                }
                
                response = requests.post("https://api.openai.com/v1/chat/completions",
                                       headers=headers, json=chat_data, timeout=30)
                
                if response.status_code == 200:
                    ai_response = response.json()["choices"][0]["message"]["content"].strip()
                    st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
                else:
                    st.session_state.chat_history.append({"role": "assistant", "content": "Sorry, I'm having trouble responding right now."})
                
                st.rerun()
                
            except Exception as e:
                st.session_state.chat_history.append({"role": "assistant", "content": "Sorry, I encountered an error. Please try again."})
                st.rerun()
        
        # Clear chat button
        if st.button("Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()
