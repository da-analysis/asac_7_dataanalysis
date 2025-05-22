import streamlit as st
from utils.google_sheets_connector import add_user_to_sheet
from datetime import datetime
from utils.css_loader import load_css

st.set_page_config(page_title="대시보드 열람 신청", layout="wide")

@st.cache_resource
def load_styles():
    load_css("main.css")         
    load_css("dashboard_request.css")  

load_styles()

# 구글 시트 정보
sheet_url = "https://docs.google.com/spreadsheets/d/1uKpuD1Fk9DDaj-mOPRMrLwLNgHfGV6bcCSEPxVSqbWE"
sheet_name = "신청자"

# 타이틀 및 설명
st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
st.title("📋 Databricks 대시보드 열람 신청")
st.markdown("<hr style='margin-top: 1rem; margin-bottom: 1.5rem;'>", unsafe_allow_html=True)
st.markdown("""
🔹 해당 페이지는 Databricks 대시보드 접근 권한 요청을 위한 신청 페이지입니다.  
🔹 입력하신 이메일로 Databricks 초대 메일이 발송될 수 있으며, Google 계정을 사용하는 것을 권장합니다.  
🔹 사용자 편의를 위해 거치는 과정으로, 입력된 정보는 **대시보드 열람 이외의 목적으로는 사용되지 않습니다.**  
🔹 문의사항 이메일 : [syleeie@gmail.com](mailto:syleeie@gmail.com)
""")

# 입력 폼
st.write(" ")
with st.form("dashboard_access_form"):
    name = st.text_input("이름")
    email = st.text_input("이메일 (Google 계정)")
    affiliation = st.text_input("소속")

    submitted = st.form_submit_button("신청하기")

    if submitted:
        if email and name and affiliation:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = "대기 중"
            msg = add_user_to_sheet(sheet_url, sheet_name, name, email, affiliation, timestamp, status)
            st.success(msg)
        else:
            st.warning("모든 항목을 입력해주세요.")
