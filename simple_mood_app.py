"""
MOOD TRACKER APP - SIMPLIFIED VERSION
====================================
This simplified version removes the complex MoodHelper class and replaces it with
simple functions while maintaining all functionality.
"""
import streamlit as st
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
