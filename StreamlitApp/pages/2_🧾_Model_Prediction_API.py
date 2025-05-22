import streamlit as st
from utils.css_loader import load_css 

st.set_page_config(page_title="Model Prediction API", layout="wide")

# CSS 로드
load_css("main.css")
load_css("api_document.css")

# Swagger UI iframe
st.markdown("""
<iframe src="https://asacdataanalysis.co.kr/docs"
        width="100%" height="2500"
        style="border: none; border-radius: 12px;"></iframe>
""", unsafe_allow_html=True)