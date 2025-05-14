import streamlit as st
from utils.css_loader import load_css
from utils.dashboard_embbder import embed_dashboard 

# CSS 로드
load_css("main.css")
load_css("dashboard.css")

st.sidebar.markdown("### 📊 대시보드 탐색")

dashboard_type = st.sidebar.radio(
    "대시보드 유형 선택",
    ["지역기준 대시보드", "업종기준 대시보드", "폐업/개업 대시보드", "전통시장 매출 분석 대시보드"],
    key="dashboard_radio",
    label_visibility="collapsed"
)

# 본문
st.title(f"📊 {dashboard_type}")
st.write("---")

if dashboard_type == "지역기준 대시보드":
    st.markdown("- 서울시 상권/인구/매출/폐업 데이터 시각화")

elif dashboard_type == "업종기준 대시보드":
    st.markdown("- 업종별 점포수, 매출 증감, 폐업률 분석")

elif dashboard_type == "폐업/개업 대시보드":
    st.markdown("- 연도별 폐업/개업 트렌드 분석")

elif dashboard_type == "전통시장 매출 분석 대시보드":
    iframe_url = f"https://tacademykr-asacdataanalysis.cloud.databricks.com/embed/dashboardsv3/01f01ab73ff4171981953dbdf8f44c32?o=639069795658224&f_7621baaa%7E716c7a53=%25EB%25AF%25B8%25EA%25B3%25A1%25ED%258C%2590%25EB%25A7%25A4&f_7621baaa%7Edcc9cb7a=%25EB%2582%2599%25EC%259B%2590%25EC%258B%259C%25EC%259E%25A5%28%25EB%2582%2599%25EC%259B%2590%25EC%25A7%2580%25ED%2595%2598%25EC%258B%259C%25EC%259E%25A5%28%25EB%258C%2580%25EC%259D%25BC%25EC%2583%2581%25EA%25B0%2580%29%29"
    
    st.markdown("- 서울열린데이터광장의 전통시장 데이터를 기반으로 구성된 대시보드입니다.")
    st.markdown("- 상권별, 서비스별 매출 관련 시각화를 제공합니다.")
    
    embed_dashboard(dashboard_url=iframe_url, height=1500)