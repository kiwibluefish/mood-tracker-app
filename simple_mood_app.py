"""
MOOD TRACKER APP - REFACTORED & ANNOTATED
=========================================

This refactored version separates concerns into clear sections:
1. Configuration & Constants
2. UI Components & Styling  
3. Data Management
4. Business Logic
5. Main App Structure

Each section is clearly marked for easy modification of UI/UX elements.
"""

import streamlit as st
import pandas as pd
import json
import os
import requests
import random
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
    "tag_columns": 6,        # Number of tag columns
    "stats_columns": 4,      # Number of stat metric columns
    "color_picker_columns": 2, # Color picker layout
    "tags_per_row": 4        # Tags displayed per row
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
# 2. UI THEMES & STYLING - MODIFY FOR DIFFERENT LOOK & FEEL
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
        
        /* Main container styling */
        .main-container {{
            background: linear-gradient(135deg, var(--gradient-start), var(--gradient-end));
            padding: 2rem;
            border-radius: 15px;
            margin: 1rem 0;
        }}
        
        /* Mood display styling */
        .mood-display {{
            text-align: center;
            padding: 1.5rem;
            background: var(--surface-color);
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin: 1rem 0;
        }}
        
        .mood-emoji {{
            font-size: 3rem;
            margin-bottom: 0.5rem;
        }}
        
        .mood-label {{
            font-size: 1.2rem;
            font-weight: bold;
            color: var(--text-color);
        }}
        
        /* AI suggestion styling */
        .ai-suggestion {{
            background: linear-gradient(45deg, var(--primary-color), var(--accent-color));
            color: white;
            padding: 1rem;
            border-radius: 8px;
            margin: 0.5rem 0;
        }}
        
        /* Custom slider styling */
        .stSlider > div > div > div > div {{
            background: var(--primary-color);
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
# 3. UI COMPONENTS - MODIFY THESE FOR DIFFERENT UI LAYOUTS
# ============================================================================

class UIComponents:
    """Reusable UI components for consistent styling"""
    
    @staticmethod
    def render_mood_display(mood_score):
        """Render mood emoji and label - CUSTOMIZE MOOD DISPLAY HERE"""
        emoji, label, color = MoodHelper.get_mood_info(mood_score)
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
# 4. DATA MANAGEMENT - BUSINESS LOGIC SEPARATED FROM UI
# ============================================================================

class DataManager:
    """Handle all data operations"""
    
    @staticmethod
    @st.cache_resource
    def init_supabase():
        """Initialize Supabase client"""
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["anon_key"]
        return create_client(url, key)
    
    @staticmethod
    def load_user_data(user_email):
        """Load mood data from Supabase"""
        try:
            supabase = DataManager.init_supabase()
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
# 5. BUSINESS LOGIC - AI & MOOD HELPERS
# ============================================================================

class MoodHelper:
    """Dynamic mood helper that searches web for sentiment-based quotes with citations"""
    
    # Mood sentiment mapping for targeted quote searches
    MOOD_SENTIMENTS = {
        "very_low": {
            "range": (0, 2),
            "keywords": ["depression quotes", "overcoming sadness", "hope during dark times", "mental health support quotes"],
            "emoji": "😢",
            "label": "Very Low",
            "search_focus": "supportive and healing"
        },
        "low": {
            "range": (3, 4), 
            "keywords": ["motivational quotes for difficult times", "encouragement quotes", "resilience quotes", "getting through tough days"],
            "emoji": "😔",
            "label": "Low", 
            "search_focus": "encouraging and uplifting"
        },
        "neutral": {
            "range": (5, 6),
            "keywords": ["positive daily quotes", "mindfulness quotes", "self-care quotes", "gentle motivation quotes"],
            "emoji": "😐",
            "label": "Neutral",
            "search_focus": "gentle and nurturing"
        },
        "good": {
            "range": (7, 8),
            "keywords": ["happiness quotes", "joy quotes", "positive energy quotes", "celebrating life quotes"],
            "emoji": "😊", 
            "label": "Good",
            "search_focus": "joyful and energizing"
        },
        "great": {
            "range": (9, 10),
            "keywords": ["success quotes", "achievement quotes", "gratitude quotes", "sharing positivity quotes"],
            "emoji": "😄",
            "label": "Great", 
            "search_focus": "celebratory and inspiring"
        }
    }
    
    # Curated quote sources with high-quality content
    TRUSTED_SOURCES = [
        "realsimple.com",
        "goodhousekeeping.com", 
        "prevention.com",
        "psychcentral.com",
        "thedepressionproject.com",
        "parade.com"
    ]
    
    @staticmethod
    def get_mood_info(mood_score: int) -> Tuple[str, str, str]:
        """Get emoji, label, and color for mood score with dynamic theming"""
        current_theme = st.session_state.get("current_theme", "🌊 Ocean")
        
        # Determine mood sentiment
        sentiment = MoodHelper._get_mood_sentiment(mood_score)
        mood_data = MoodHelper.MOOD_SENTIMENTS[sentiment]
        
        # Get theme colors (assuming UIThemes class is available)
        try:
            from mood_tracker_refactored import UIThemes
            theme_colors = UIThemes.get_theme(current_theme)
            color = theme_colors["primary"]
        except:
            color = "#3b82f6"  # Default blue
            
        return mood_data["emoji"], mood_data["label"], color
    
    @staticmethod
    def get_helpful_hint(score: int, note_text: str = "") -> str:
        """Generate dynamic helpful hint with web-sourced quotes"""
        sentiment = MoodHelper._get_mood_sentiment(score)
        
        # Get cached quotes or search for new ones
        quotes = MoodHelper._get_quotes_for_sentiment(sentiment, note_text)
        
        if quotes:
            # Select best quote based on context
            selected_quote = MoodHelper._select_best_quote(quotes, score, note_text)
            
            # Format the response with quote and source
            hint = MoodHelper._format_hint_with_quote(selected_quote, sentiment, score, note_text)
        else:
            # Fallback to static hints if web search fails
            hint = MoodHelper._get_fallback_hint(score, note_text)
        
        return hint
    
    @staticmethod
    def _get_mood_sentiment(mood_score: int) -> str:
        """Determine mood sentiment category from score"""
        for sentiment, data in MoodHelper.MOOD_SENTIMENTS.items():
            min_score, max_score = data["range"]
            if min_score <= mood_score <= max_score:
                return sentiment
        return "neutral"  # Default fallback
    
    @staticmethod
    def _get_quotes_for_sentiment(sentiment: str, note_text: str = "") -> List[Dict]:
        """Search web for quotes matching mood sentiment"""
        # Check cache first
        cache_key = f"quotes_{sentiment}_{hash(note_text[:50])}"
        
        if cache_key in st.session_state and MoodHelper._is_cache_valid(cache_key):
            return st.session_state[cache_key]["quotes"]
        
        # Search for new quotes
        mood_data = MoodHelper.MOOD_SENTIMENTS[sentiment]
        search_terms = mood_data["keywords"]
        
        # Add context from note if available
        if note_text:
            context_keywords = MoodHelper._extract_context_keywords(note_text)
            if context_keywords:
                search_terms = [f"{term} {context_keywords}" for term in search_terms[:2]]
        
        quotes = []
        for search_term in search_terms[:2]:  # Limit searches to avoid rate limits
            try:
                # Use web_search function if available
                search_results = MoodHelper._search_web_for_quotes(search_term)
                parsed_quotes = MoodHelper._parse_quotes_from_results(search_results, sentiment)
                quotes.extend(parsed_quotes)
                
                if len(quotes) >= 3:  # Enough quotes found
                    break
                    
            except Exception as e:
                st.error(f"Quote search error: {str(e)}")
                continue
        
        # Cache results
        st.session_state[cache_key] = {
            "quotes": quotes,
            "timestamp": datetime.now().timestamp()
        }
        
        return quotes
    
    @staticmethod
    def _search_web_for_quotes(search_term: str) -> List[Dict]:
        """Search web for quotes using available search functionality"""
        try:
            # Try to use the web_search function from the main app
            from main import web_search  # Adjust import as needed
            results = web_search(f"positive {search_term} with citations", num_results=3)
            return results
        except:
            # Fallback: return curated quotes if web search unavailable
            return MoodHelper._get_curated_quotes(search_term)
    
    @staticmethod
    def _get_curated_quotes(search_term: str) -> List[Dict]:
        """Fallback curated quotes when web search is unavailable"""
        curated_quotes = {
            "depression quotes": [
                {
                    "quote": "When everything feels heavy, start with the smallest possible anchor. Try one minute of slow breathing, counting 4-in and 6-out.",
                    "author": "The Depression Project",
                    "source": "thedepressionproject.com",
                    "url": "https://thedepressionproject.com/blogs/news/positive-uplifting-encouraging-quotes-for-depression"
                },
                {
                    "quote": "You are brave, courageous and strong for continuing to fight an illness that nobody else can see.",
                    "author": "The Depression Project", 
                    "source": "thedepressionproject.com",
                    "url": "https://thedepressionproject.com/blogs/news/positive-uplifting-encouraging-quotes-for-depression"
                }
            ],
            "motivational quotes": [
                {
                    "quote": "Nothing is impossible, the word itself says 'I'm possible.'",
                    "author": "Audrey Hepburn",
                    "source": "realsimple.com",
                    "url": "https://www.realsimple.com/work-life/life-strategies/inspiration-motivation/positive-quotes"
                },
                {
                    "quote": "Real change, enduring change, happens one step at a time.",
                    "author": "Ruth Bader Ginsberg",
                    "source": "realsimple.com", 
                    "url": "https://www.realsimple.com/work-life/life-strategies/inspiration-motivation/positive-quotes"
                }
            ],
            "happiness quotes": [
                {
                    "quote": "Happiness is not by chance, but by choice.",
                    "author": "Jim Rohn",
                    "source": "goodhousekeeping.com",
                    "url": "https://www.goodhousekeeping.com/health/wellness/g2401/inspirational-quotes/"
                },
                {
                    "quote": "Try to be a rainbow in someone else's cloud.",
                    "author": "Maya Angelou",
                    "source": "realsimple.com",
                    "url": "https://www.realsimple.com/work-life/life-strategies/inspiration-motivation/positive-quotes"
                }
            ]
        }
        
        # Find matching quotes
        for key, quotes in curated_quotes.items():
            if any(word in search_term.lower() for word in key.split()):
                return [{"content": quote} for quote in quotes]
        
        return []
    
    @staticmethod
    def _parse_quotes_from_results(search_results: List[Dict], sentiment: str) -> List[Dict]:
        """Parse quotes from web search results"""
        quotes = []
        
        for result in search_results:
            # Extract quotes from search result content
            content = result.get("content", "")
            url = result.get("url", "")
            title = result.get("title", "")
            
            # Simple quote extraction (look for quoted text)
            import re
            quote_patterns = [
                r'"([^"]{20,200})"[^"]*—\s*([^,\n]+)',  # "Quote" —Author
                r'"([^"]{20,200})"[^"]*-\s*([^,\n]+)',   # "Quote" -Author  
                r'["""]([^""]{20,200})["""][^""]*—\s*([^,\n]+)', # Smart quotes
            ]
            
            for pattern in quote_patterns:
                matches = re.findall(pattern, content)
                for quote_text, author in matches[:2]:  # Limit per source
                    if len(quote_text.strip()) > 20:  # Meaningful length
                        quotes.append({
                            "quote": quote_text.strip(),
                            "author": author.strip(),
                            "source": MoodHelper._extract_domain(url),
                            "url": url,
                            "sentiment_match": MoodHelper._calculate_sentiment_match(quote_text, sentiment)
                        })
        
        return quotes
    
    @staticmethod
    def _extract_context_keywords(note_text: str) -> str:
        """Extract relevant keywords from user's note for better quote matching"""
        # Common emotional keywords to enhance search
        emotion_keywords = {
            "work": "workplace stress",
            "family": "family relationships", 
            "sleep": "rest and recovery",
            "anxiety": "anxiety management",
            "tired": "energy and motivation",
            "overwhelmed": "stress management",
            "lonely": "connection and support",
            "grateful": "gratitude and appreciation"
        }
        
        note_lower = note_text.lower()
        for keyword, enhancement in emotion_keywords.items():
            if keyword in note_lower:
                return enhancement
        
        return ""
    
    @staticmethod
    def _select_best_quote(quotes: List[Dict], mood_score: int, note_text: str) -> Dict:
        """Select the most appropriate quote based on context"""
        if not quotes:
            return {}
        
        # Score quotes based on relevance
        scored_quotes = []
        for quote in quotes:
            score = 0
            
            # Sentiment match score
            score += quote.get("sentiment_match", 0) * 3
            
            # Source reliability score
            if quote.get("source", "") in MoodHelper.TRUSTED_SOURCES:
                score += 2
            
            # Length preference (not too short, not too long)
            quote_length = len(quote.get("quote", ""))
            if 50 <= quote_length <= 150:
                score += 1
            
            # Context relevance
            if note_text:
                note_words = set(note_text.lower().split())
                quote_words = set(quote.get("quote", "").lower().split())
                common_words = len(note_words.intersection(quote_words))
                score += common_words * 0.5
            
            scored_quotes.append((score, quote))
        
        # Return highest scoring quote
        scored_quotes.sort(key=lambda x: x[0], reverse=True)
        return scored_quotes[0][1] if scored_quotes else quotes[0]
    
    @staticmethod
    def _calculate_sentiment_match(quote_text: str, sentiment: str) -> float:
        """Calculate how well a quote matches the desired sentiment"""
        sentiment_words = {
            "very_low": ["hope", "healing", "support", "gentle", "comfort", "peace"],
            "low": ["strength", "courage", "overcome", "resilience", "better", "forward"],
            "neutral": ["balance", "mindful", "present", "calm", "steady", "centered"],
            "good": ["joy", "happiness", "positive", "bright", "energy", "smile"],
            "great": ["success", "achievement", "celebrate", "gratitude", "amazing", "wonderful"]
        }
        
        target_words = sentiment_words.get(sentiment, [])
        quote_lower = quote_text.lower()
        
        matches = sum(1 for word in target_words if word in quote_lower)
        return matches / len(target_words) if target_words else 0
    
    @staticmethod
    def _format_hint_with_quote(quote_data: Dict, sentiment: str, score: int, note_text: str) -> str:
        """Format the helpful hint with quote and citation"""
        if not quote_data:
            return MoodHelper._get_fallback_hint(score, note_text)
        
        quote_text = quote_data.get("quote", "")
        author = quote_data.get("author", "Unknown")
        source = quote_data.get("source", "")
        url = quote_data.get("url", "")
        
        # Create contextual intro based on sentiment
        sentiment_intros = {
            "very_low": "During difficult times, remember: ",
            "low": "For encouragement when things feel tough: ",
            "neutral": "A gentle reminder for today: ",
            "good": "To celebrate your positive energy: ",
            "great": "Embracing your wonderful mood: "
        }
        
        intro = sentiment_intros.get(sentiment, "Here's some inspiration: ")
        
        # Format with proper citation
        formatted_hint = f"{intro}\n\n*\"{quote_text}\"*\n\n— {author}"
        
        if source and url:
            formatted_hint += f"\n\n📖 Source: [{source}]({url})"
        elif source:
            formatted_hint += f"\n\n📖 Source: {source}"
        
        # Add contextual action suggestion
        action_suggestions = {
            "very_low": "\n\n💙 Take one small, gentle step today. You're not alone in this journey.",
            "low": "\n\n💪 Consider one small action that might help you move forward today.",
            "neutral": "\n\n🌱 Perhaps take a moment to appreciate where you are right now.",
            "good": "\n\n✨ Share this positive energy with someone who might need it today.",
            "great": "\n\n🎉 Celebrate this moment and consider how you can maintain this wonderful feeling."
        }
        
        formatted_hint += action_suggestions.get(sentiment, "")
        
        return formatted_hint
    
    @staticmethod
    def _get_fallback_hint(score: int, note_text: str = "") -> str:
        """Fallback to static hints if dynamic search fails"""
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
    
    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract domain name from URL"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc.replace("www.", "")
        except:
            return "web source"
    
    @staticmethod
    def _is_cache_valid(cache_key: str, max_age_hours: int = 24) -> bool:
        """Check if cached quotes are still valid"""
        if cache_key not in st.session_state:
            return False
        
        cache_data = st.session_state[cache_key]
        cache_time = cache_data.get("timestamp", 0)
        current_time = datetime.now().timestamp()
        
        age_hours = (current_time - cache_time) / 3600
        return age_hours < max_age_hours
    
    @staticmethod
    def clear_quote_cache():
        """Clear cached quotes (useful for testing or manual refresh)"""
        keys_to_remove = [key for key in st.session_state.keys() if key.startswith("quotes_")]
        for key in keys_to_remove:
            del st.session_state[key]
        st.success("Quote cache cleared! New quotes will be fetched on next mood check-in.")

# Usage example and testing function
def test_mood_helper():
    """Test function to demonstrate the dynamic MoodHelper"""
    st.subheader("🧪 Testing Dynamic MoodHelper")
    
    test_mood = st.slider("Test Mood Score", 0, 10, 5)
    test_note = st.text_input("Test Note", "Feeling a bit overwhelmed with work today")
    
    if st.button("Get Dynamic Hint"):
        with st.spinner("Searching for personalized quotes..."):
            hint = MoodHelper.get_helpful_hint(test_mood, test_note)
            st.markdown("### Generated Hint:")
            st.markdown(hint)
    
    if st.button("Clear Quote Cache"):
        MoodHelper.clear_quote_cache()

if __name__ == "__main__":
    # For testing purposes
    test_mood_helper()

class AIHelper:
    """AI-related functionality"""
    
    @staticmethod
    def get_openai_key():
        """Get OpenAI API key from secrets"""
        try:
            if "openai_api_key" in st.secrets:
                return st.secrets["openai_api_key"].strip()
            elif "openai" in st.secrets and "openai_api_key" in st.secrets["openai"]:
                return st.secrets["openai"]["openai_api_key"].strip()
            elif "openai" in st.secrets and "api_key" in st.secrets["openai"]:
                return st.secrets["openai"]["api_key"].strip()
            return ""
        except Exception as e:
            st.sidebar.error(f"Error accessing OpenAI key: {str(e)}")
            return ""
    
    @staticmethod
    def get_ai_suggestion(mood_score, note_text, api_key):
        """Get AI suggestion from OpenAI"""
        if not api_key:
            return ""
        
        try:
            # Determine system prompt based on mood
            if mood_score <= 2:
                system_prompt = "You are a gentle, supportive counselor. Provide immediate emotional support with 3-4 sentences. Focus on comfort and small, manageable steps."
            elif mood_score <= 4:
                system_prompt = "You are an encouraging coach. Provide gentle motivation with 3-4 sentences. Focus on small positive actions and building momentum."
            elif mood_score <= 6:
                system_prompt = "You are an upbeat coach. Provide fun suggestions to boost mood with 3-4 sentences. Focus on enjoyable activities."
            else:
                system_prompt = "You are an enthusiastic coach. Celebrate their positive state with 3-4 sentences. Focus on maintaining and sharing positivity."
            
            user_prompt = f"Someone is feeling {mood_score}/10 today. {f'They shared: {note_text}' if note_text else ''} Please provide a supportive response."
            
            # API call
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
# 6. AUTHENTICATION - MODIFY FOR DIFFERENT AUTH SYSTEMS
# ============================================================================

class AuthManager:
    """Handle authentication logic"""
    
    @staticmethod
    def show_login():
        """Show login interface - CUSTOMIZE LOGIN UI HERE"""
        st.header("This app is private.")
        st.subheader("Please sign in with Google")
        if st.button("Sign in with Google"):
            st.login()
    
    @staticmethod
    def check_authentication():
        """Check if user is authenticated"""
        if not st.user.is_logged_in:
            AuthManager.show_login()
            st.stop()
        return st.user.email, st.user.name
    
    @staticmethod
    def render_user_info(user_name, user_email):
        """Render user information in sidebar"""
        st.sidebar.markdown(f"Signed in as **{user_name}** ({user_email})")
        if st.sidebar.button("Log out"):
            st.logout()
            st.rerun()

# ============================================================================
# 7. MAIN APP STRUCTURE - MODIFY TAB LAYOUT & CONTENT HERE
# ============================================================================

def initialize_session_state():
    """Initialize session state variables"""
    defaults = {
        "selected_tags": set(),
        "chat_history": [],
        "last_ai_call": 0,
        "mood_value": MOOD_SCALE["default_value"],
        "current_theme": "🌊 Ocean"
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def render_checkin_tab(user_email, api_key):
    """Render the main check-in tab - CUSTOMIZE CHECKIN LAYOUT HERE"""
    st.header(CONTENT_TEXT["main_header"])
    
    # Date and note input
    col1, col2 = st.columns(UI_LAYOUT["main_columns"])
    with col1:
        note = st.text_area(
            "How is today?", 
            placeholder=CONTENT_TEXT["note_placeholder"], 
            height=120
        )
    with col2:
        selected_date = st.date_input(
            "📅 Check-in date", 
            value=date.today(), 
            max_value=date.today()
        )
    
    # Mood slider
    mood = st.slider(
        CONTENT_TEXT["mood_slider_label"],
        MOOD_SCALE["min_value"],
        MOOD_SCALE["max_value"], 
        MOOD_SCALE["default_value"]
    )
    
    # Update mood display
    UIComponents.render_mood_display(mood)
    
    # Tag selection
    UIComponents.render_tag_selector()
    UIComponents.render_selected_tags()
    
    # Manual tags input
    manual_tags = st.text_input(
        CONTENT_TEXT["manual_tags_label"],
        value=", ".join(sorted(st.session_state.selected_tags)),
        help="Type additional tags separated by commas, or edit existing ones"
    )
    
    # Update selected tags from manual input
    if manual_tags:
        new_tags = set([t.strip() for t in manual_tags.split(",") if t.strip()])
        if new_tags != st.session_state.selected_tags:
            st.session_state.selected_tags = new_tags
    
    # Hints and AI suggestions
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**💡 Helpful Hint**")
        hint = MoodHelper.get_helpful_hint(mood, note)
        st.write(hint)
    
    with col2:
        st.markdown("**🤖 AI Suggestion**")
        if api_key:
            current_time = time.time()
            if current_time - st.session_state.last_ai_call > 2:
                ai_suggestion = AIHelper.get_ai_suggestion(mood, note, api_key)
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
    if st.button(CONTENT_TEXT["submit_button"], type="primary"):
        new_entry = {
            "date": selected_date,
            "mood_score": mood,
            "note": note,
            "tags": manual_tags,
            "ai_suggestion": st.session_state.get("current_ai_suggestion", ""),
            "helpful_hint": hint,
            "timestamp": datetime.now().isoformat()
        }
        
        if DataManager.save_entry(user_email, new_entry):
            st.success(CONTENT_TEXT["success_message"].format(selected_date.strftime('%B %d, %Y')))
            st.session_state.selected_tags = set()
            st.rerun()
        else:
            st.error(CONTENT_TEXT["error_message"])

def render_trends_tab(data):
    """Render trends analysis tab - CUSTOMIZE CHARTS HERE"""
    st.header("📊 Your Mood Trends")
    
    if not data:
        st.info("No check-ins yet. Complete your first check-in to see trends!")
        return
    
    # Statistics row
    UIComponents.render_stats_row(data)
    
    # Convert to DataFrame for plotting
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Daily mood chart
    st.subheader("Daily Mood")
    fig = px.line(df, x='date', y='mood_score',
                  title="Mood Over Time",
                  labels={'mood_score': 'Mood Score', 'date': 'Date'},
                  range_y=[0, 10])
    fig.add_hline(y=5, line_dash="dash", line_color="gray", annotation_text="Neutral")
    st.plotly_chart(fig, use_container_width=True)
    
    # Weekly average (if enough data)
    if len(data) > 7:
        st.subheader("Weekly Average")
        df_weekly = df.set_index('date').resample('W')['mood_score'].mean().reset_index()
        fig_weekly = px.line(df_weekly, x='date', y='mood_score',
                           title="Weekly Average Mood",
                           labels={'mood_score': 'Average Mood', 'date': 'Week'},
                           range_y=[0, 10])
        fig_weekly.add_hline(y=5, line_dash="dash", line_color="gray", annotation_text="Neutral")
        st.plotly_chart(fig_weekly, use_container_width=True)

def render_hints_tab(data):
    """Render hints tab - CUSTOMIZE HINTS DISPLAY HERE"""
    st.header("💡 Helpful Hints")
    
    # Search functionality
    search_query = st.text_input("🔍 Search hints", placeholder="Search by note, hint, or AI suggestion...")
    
    # Process hints data
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
    
    # Filter based on search
    if search_query:
        filtered_hints = []
        for hint in hints_data:
            if (search_query.lower() in hint['Note'].lower() or
                search_query.lower() in hint['Helpful Hint'].lower() or
                search_query.lower() in hint['AI Suggestion'].lower()):
                filtered_hints.append(hint)
        hints_data = filtered_hints
    
    if hints_data:
        hints_df = pd.DataFrame(hints_data[::-1])  # Most recent first
        st.dataframe(hints_df, use_container_width=True, hide_index=True)
    else:
        st.info("No hints found" + (f" matching '{search_query}'" if search_query else "") + 
                ". Complete some check-ins to see helpful hints here!")

def render_chat_tab(api_key):
    """Render chat tab - CUSTOMIZE CHAT INTERFACE HERE"""
    st.header("💬 Mood Support Chat")
    
    if not api_key:
        st.info("Chat feature requires AI to be enabled. Contact admin to enable AI features.")
        return
    
    # Chat interface
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    # Display chat history
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("How are you feeling? Ask for support or advice..."):
        # Add user message
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = AIHelper.get_ai_suggestion(5, prompt, api_key)  # Default mood for chat
                st.write(response)
                st.session_state.chat_messages.append({"role": "assistant", "content": response})

def main():
    """Main application function - MODIFY APP STRUCTURE HERE"""
    # Configure page
    st.set_page_config(**APP_CONFIG)
    
    # Initialize session state
    initialize_session_state()
    
    # Authentication
    user_email, user_name = AuthManager.check_authentication()
    
    # Load data and configuration
    data = DataManager.load_user_data(user_email)
    config = DataManager.load_user_config(user_email)
    api_key = AIHelper.get_openai_key()
    
    # Load theme preference
    if "theme" in config:
        st.session_state.current_theme = config["theme"]
    
    # Apply theme
    UIThemes.apply_theme_css(st.session_state.current_theme)
    
    # Sidebar settings
    st.sidebar.header("⚙️ Settings")
    AuthManager.render_user_info(user_name, user_email)
    
    # Theme selection
    selected_theme = UIComponents.render_theme_selector()
    if selected_theme != st.session_state.current_theme:
        st.session_state.current_theme = selected_theme
        config["theme"] = selected_theme
        DataManager.save_user_config(user_email, config)
        st.rerun()
    
    # Custom theme picker
    UIComponents.render_custom_theme_picker()
    
    # AI status
    if api_key:
        st.sidebar.success("🤖 AI Features Enabled")
    else:
        st.sidebar.warning("🤖 AI Features Disabled")
    
    # Main app tabs - MODIFY TAB STRUCTURE HERE
    tab_checkin, tab_hints, tab_trends, tab_chat = st.tabs([
        "📝 Check-in", 
        "💡 Hints", 
        "📊 Trends", 
        "💬 Chat"
    ])
    
    with tab_checkin:
        render_checkin_tab(user_email, api_key)
    
    with tab_hints:
        render_hints_tab(data)
    
    with tab_trends:
        render_trends_tab(data)
    
    with tab_chat:
        render_chat_tab(api_key)

if __name__ == "__main__":
    main()
