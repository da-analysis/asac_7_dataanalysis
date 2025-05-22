from pathlib import Path
from PIL import Image
import streamlit as st

# StreamlitApp 기준 경로
BASE_PATH = Path(__file__).parent.parent

@st.cache_data
def load_dashboard_preview():
    return Image.open(BASE_PATH / "assets/images/dashboard_preview.png")

@st.cache_data
def load_model_prediction_api_preview():
    return Image.open(BASE_PATH / "assets/images/model_prediction_api_preview.png")

@st.cache_data
def load_chatbot_preview():
    return Image.open(BASE_PATH / "assets/images/chatbot_preview.png")

@st.cache_data
def load_team_image():
    return Image.open(BASE_PATH / "assets/images/team_introduce.png")
