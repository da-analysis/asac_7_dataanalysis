import streamlit as st
import os

# css load  - main, dashboard 
def load_css(file_path):
    if os.path.exists(file_path):
        with open(file_path, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_css(os.path.join(BASE_DIR, '..', 'assets', 'css', 'main.css'))
load_css(os.path.join(BASE_DIR, '..', 'assets', 'css', 'dashboard.css'))

# 사이드바
st.sidebar.header("📊 대시보드 탐색")

with st.sidebar.expander("지역기준 대시보드", expanded=False):
    selected_region = st.selectbox(
        "지역기준 선택",
        ["기본 상권 정보", "상권활성화지수", "유동인구", "지역별 가맹점 수", "상권별 추정매출", "소비특성", "상권변화지표"],
        key="region"
    )

with st.sidebar.expander("업종기준 대시보드", expanded=False):
    selected_category = st.selectbox(
        "업종기준 선택",
        ["업종 실시간 상권현황", "업종별 사업체 현황", "업종별 창업위험도", "업종별 추정매출", "상권변화지표"],
        key="category"
    )

with st.sidebar.expander("폐업/개업 대시보드", expanded=False):
    selected_openclose = st.selectbox(
        "폐업/개업 선택",
        ["개업, 폐업, 재창업 수", "업종, 지역별 개폐업률", "상권변화지표", "영세자영업 폐업 점포 수", "영세자영업 평균 영업기간별 점포 수"],
        key="openclose"
    )

# 본문
st.title("📊 대시보드")

tab1, tab2, tab3 = st.tabs(["지역기준 대시보드", "업종기준 대시보드", "폐업/개업 대시보드"])

with tab1:
    st.subheader("지역기준 대시보드")
    st.markdown("- 서울시 상권/인구/매출/폐업 데이터 시각화")

with tab2:
    st.subheader("업종기준 대시보드")
    st.markdown("- 업종별 점포수, 매출 증감, 폐업률 분석")

with tab3:
    st.subheader("폐업/개업 대시보드")
    st.markdown("- 연도별 폐업/개업 트렌드 분석")
