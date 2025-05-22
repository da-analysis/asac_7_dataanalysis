import streamlit as st
from utils.css_loader import load_css
from utils.dashboard_embbder import embed_dashboard
from utils.js_scroll import scroll_to_element, render_scroll_to_top_button

st.set_page_config(page_title="대시보드", layout="wide")

# CSS 로드
load_css("main.css")
load_css("dashboard.css")

# 스크롤 기준점
st.markdown('<div id="scroll-anchor"></div>', unsafe_allow_html=True)

# 사이드바 메뉴
st.sidebar.markdown("### 대시보드 탐색")
dashboard_type = st.sidebar.radio(
    "대시보드 유형 선택",
    ["상권 대시보드", "업종 대시보드", "전통시장 매출 분석 대시보드"],
    key="dashboard_radio",
    label_visibility="collapsed"
)

# 접근 권한 링크 
st.sidebar.markdown("### 접근 권한")
st.sidebar.markdown("[📋 대시보드 열람 신청하기](/대시보드_열람_신청)")

st.markdown('<div id="dashboard-title" style="height: 1px;"></div>', unsafe_allow_html=True)

# 제목
st.markdown(f"<h1 class='dashboard-title'>📊 {dashboard_type}</h1>", unsafe_allow_html=True)
st.markdown("<hr style='margin-top: 1rem; margin-bottom: 1.2rem;'>", unsafe_allow_html=True)

# 스크롤 이동
scroll_to_element('document.querySelector("#dashboard-title")', offset=-100, delay=300)

# 대시보드 정보 
dashboard_mapping = {
    "상권 대시보드": {
        "url": "https://tacademykr-asacdataanalysis.cloud.databricks.com/embed/dashboardsv3/01f020d761b2102592b1ce19f46c255a?o=639069795658224",
        "height": 2500,
        "desc": "🔹서울시 상권별 점포 수, 유동인구, 점포 분포, 활성화 지수 등 상권 현황을 종합적으로 시각화한 대시보드입니다."
    },
    "업종 대시보드": {
        "url": "https://tacademykr-asacdataanalysis.cloud.databricks.com/embed/dashboardsv3/01f0314f619e1f72b4fb9aafbf093c64?o=639069795658224",
        "height": 2550,
        "desc": "🔹서울시 업종별 점포 수, 매출, 개폐업, 운영지속성 등 다양한 지표를 종합 분석한 대시보드입니다."
    },
    "전통시장 매출 분석 대시보드": {
        "url": "https://tacademykr-asacdataanalysis.cloud.databricks.com/embed/dashboardsv3/01f01ab73ff4171981953dbdf8f44c32?o=639069795658224",
        "height": 3150,
        "desc": "🔹서울시 전통시장 데이터를 기반으로 업종별 매출 추이와 소비 성향을 분석한 대시보드입니다."
    }
}

info = dashboard_mapping[dashboard_type]
st.markdown(f"<p class='dashboard-description'>{info['desc']}</p>", unsafe_allow_html=True)

embed_dashboard(dashboard_url=info["url"], height=info["height"])

render_scroll_to_top_button() 