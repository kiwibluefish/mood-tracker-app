# Simple Mood Tracking App - All-in-One Version (No Email)
# Run with: streamlit run simple_mood_app.py

import streamlit as st
import pandas as pd
import json
import os
import requests
import time
from datetime import date, datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

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
        "surface": "#ffff",
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
        "surface": "#ffff",
        "text": "#92400e",
        "gradient_start": "#f59e0b",
        "gradient_end": "#ef4444",
        "mood_colors": ["#dc2626", "#ef4444", "#f59e0b", "#fbbf24", "#fde047", "#fef3c7"]
    },
    ...
}

# App configuration
st.set_page_config(page_title="Daily Mood Check-in", page_icon="😊", layout="centered")

# ---------------- DATA FUNCTIONS ----------------
def load_data():
    """Load mood data from JSON file"""
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
        # Convert string dates back to date objects
        for entry in data:
            if isinstance(entry.get('date'), str):
                entry['date'] = datetime.strptime(entry['date'], '%Y-%m-%d').date()
        return data
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_data(data):
    """Save mood data to JSON file"""
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
        return {"openai_api_key": ""}

def save_config(config):
    """Save app configuration"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

# ---------------- HELPERS, UI, MAIN APP ----------------
# (All other functions and blocks fixed with proper indentation.)
