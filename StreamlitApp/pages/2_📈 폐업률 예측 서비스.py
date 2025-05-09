import streamlit as st
import os 

# css load - main.css, prediction.css 
def load_css(file_path):
    if os.path.exists(file_path):
        with open(file_path, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_css(os.path.join(BASE_DIR, '..', 'assets', 'css', 'main.css'))
load_css(os.path.join(BASE_DIR, '..', 'assets', 'css', 'prediction.css'))

# 본문 
st.title("📈 폐업률 예측 서비스")
st.markdown("서울시 지역과 업종을 선택하여 폐업률을 예측합니다.")
st.write("---")

# 서울시 25개 구 리스트
seoul_gu_list = [
    "강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구", "노원구",
    "도봉구", "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구", "성북구",
    "송파구", "양천구", "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구"
]

# 업종 리스트 (예시)
industry_list = [
    "카페", "편의점", "음식점", "학원", "미용실", "의류점", "부동산중개업", "기타"
]

col1, col2 = st.columns(2)
with col1:
    region = st.selectbox("구 선택", seoul_gu_list)
with col2:
    industry = st.selectbox("업종 선택", industry_list)

if st.button("폐업률 예측하기"):
    st.success(f"🔹 선택한 지역: 서울특별시 {region}\n\n🔹 업종: {industry}\n\n (여기에 예측 결과가 표시됩니다.)")