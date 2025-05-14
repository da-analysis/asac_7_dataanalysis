import os
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# assets/css 디렉토리의 CSS 파일을 로드 
def load_css(filename: str):
    css_path = os.path.join(BASE_DIR, '..', 'assets', 'css', filename)

    if not os.path.exists(css_path):
        st.warning(f"[load_css] File not found: {css_path}")  
    else:
        with open(css_path, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)