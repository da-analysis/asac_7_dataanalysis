import streamlit as st
from utils.css_loader import load_css
from streamlit import switch_page 

# 페이지 제목  
st.set_page_config(page_title="폐업 예측 모델과 상권 인사이트 도구 개발", page_icon="🏪", layout="wide")

# CSS 로드
load_css("main.css")

# 제목
st.markdown("<div class='margin-top-md'></div>", unsafe_allow_html=True)
st.title("폐업 예측 모델과 상권 인사이트 도구 개발 🏪")
st.markdown("<hr style='margin-top: 1rem; margin-bottom: 0rem;'>", unsafe_allow_html=True)

# st.markdown("<div class='margin-bottom-sm'></div>", unsafe_allow_html=True)

# 버튼 스타일 커스텀 (외부 css로 버튼 크기조정이 불가 -> 마크다운으로 감싸서 커스텀)
st.markdown("""
    <style>
    div.stButton > button {
        width: 100%;
        height: 55px;
        font-size: 24px;
        font-weight: bold;
        margin-top: 1.5rem;
        border-radius: 12px;
        background-color: #f0f0f0;
        color: #333;
        transition: background-color 0.3s, transform 0.2s;
    } 
    div.stButton > button:hover {
        background-color: #d0d0d0;
        transform: scale(1.02);
        box-shadow: 0 3px 6px rgba(0, 0, 0, 0.15); 
    }
    </style>
    """, unsafe_allow_html=True) 

# 세션 초기화
if "selected_page" not in st.session_state:
    st.session_state.selected_page = "프로젝트 소개"

st.markdown('<div style="margin-top: 0rem;">', unsafe_allow_html=True)
cols = st.columns(3)

with cols[0]:
    if st.button("🗂️ 프로젝트 소개"):
        st.session_state.selected_page = "프로젝트 소개"

with cols[1]:
    if st.button("👨‍👩‍👧‍👦 팀원 소개"):
        st.session_state.selected_page = "팀원 소개"

with cols[2]:
    if st.button("🔗 기타 정보"):
        st.session_state.selected_page = "기타 정보"

# 본문 
st.write("")  

if st.session_state.selected_page == "프로젝트 소개":
    with st.expander("🗂️ 프로젝트 소개", expanded=True):
        st.markdown("""
            <div style='font-size:15px; line-height:1.8'>

            소상공인의 **폐업률이 높아지고** 지역별·업종별 성과 격차가 심해지는 가운데,  
            기존 상권 분석 플랫폼은 **폐업률이나 정책 사례까지 통합적으로 확인하기에는 한계**가 있습니다.  

            이러한 문제를 해결하기 위해 **공공데이터**를 바탕으로 폐업 위험을 예측하고 **상권·업종 정보와 정책 사례를 결합하여  
            대시보드, API, 챗봇 형태로 제공하는 시스템**을 구축했습니다.  

            본 프로젝트는 **데이터 수집·분석 및 대시보드를 통한 인사이트 도출, 예측 모델 개발, FastAPI 배포, LangGraph 기반 챗봇 구현**까지 총 네 단계로 구성되며,  
            최종적으로 **Streamlit 웹 서비스**로 통합 제공됩니다.
            <br><br>

            🔹 상권·인구·매출 등 실시간 데이터 수집 및 전처리<br>
            🔹 폐업 예측 모델 개발과 API화 (MLflow + FastAPI 기반)<br>
            🔹 LangGraph 챗봇 구축<br>
            🔹 Streamlit으로 통합 웹 서비스 제공
            </div>
        """, unsafe_allow_html=True)
    
    st.write(" ")
    st.markdown("<div class='preview-title'>페이지 미리보기 🔍</div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📊 대시보드", "🧾 Model Prediction API", "🤖 ChatBot"])
    with tab1:
        col1, col2 = st.columns([2.5, 2.5])  
        with col1:
            st.write(" ")
            st.image("assets/images/dashboard_preview.png", width=600)
        with col2:
            st.write(" ")
            st.markdown("### 📊 대시보드")
            st.markdown("""
                <div style="font-size:14px; line-height:1.6">
                <ul style="padding-left: 1.2rem">
                <li>서울시 상권/업종/전통시장에 대한 대시보드 제공</li>
                <li>상권별 유동인구, 점포 수, 매출, 소비 특성 등의 시각화 지표를 제공하여<br>
                    <strong>신규 창업자, 업종 전환자, 기존 소상공인</strong>이 활용 가능</li>
                <li>실시간 데이터를 반영하여 주요 상권 및 업종에 대한<br>
                    <strong>트렌드 분석</strong>, <strong>운영 지속성 평가</strong> 제공</li>
                </ul>
                </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="page-card-button-wrapper" style="margin-top: 4rem;">', unsafe_allow_html=True)
            if st.button("➡️ 페이지 바로가기", key="go_dashboard"):
                st.switch_page("pages/1_📊_대시보드.py")
            st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        col1, col2 = st.columns([2.5, 2.5])  
        with col1:
            st.write(" ")
            st.image("assets/images/model_prediction_api_preview.png", width=600)
        with col2:
            st.write(" ")
            st.markdown("### 🧾 Model Prediction API")
            st.markdown("""
                <div style="font-size:14px; line-height:1.6">
                <ul style="padding-left: 1.2rem">
                    <li>스마트치안 빅데이터 플랫폼 데이터를 활용한 <strong>서울특별시 폐업 예측 모델</strong></li>
                    <li>행정안전부 인허가 데이터를 활용한 <strong>전국 단위 폐업 예측 모델</strong></li>
                    <li><strong>'Try it out' 버튼</strong>을 통해 폐업 확률 및 예측값(0: 폐업, 1: 영업)을 확인 가능</li>
                </ul>
                </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="page-card-button-wrapper" style="margin-top: 3.5rem;">', unsafe_allow_html=True)
            if st.button("➡️ 페이지 바로가기", key="go_api"):
                st.switch_page("pages/2_🧾_Model_Prediction_API.py")
            st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        col1, col2 = st.columns([2.5, 2.5])  
        with col1:
            st.write(" ")
            st.image("assets/images/chatbot_preview.png", width=600)
        with col2:
            st.write(" ")
            st.markdown("### 🤖 ChatBot")
            st.markdown("""
                <div style="font-size:14px; line-height:1.6">
                <ul style="padding-left: 1.2rem">
                    <li>폐업률, 점포 수, 소비 비율 등 상권 기반 정형 데이터를 질의응답 형태로 제공</li>
                    <li>정책 사례, 지원사업 안내 등은 PDF·웹 문서를 기반으로 탐색</li>
                    <li>질문 내용에 따라 데이터 조회 또는 문서 검색으로 자동 분기</li>
                </ul>
                </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="page-card-button-wrapper" style="margin-top: 4.5rem;">', unsafe_allow_html=True)
            if st.button("➡️ 페이지 바로가기", key="go_chatbot"):
                st.switch_page("pages/4_🤖 ChatBot.py")
            st.markdown('</div>', unsafe_allow_html=True)


elif st.session_state.selected_page == "팀원 소개":
    with st.expander("👨‍👩‍👧‍👦 팀원 소개", expanded=True):
        st.markdown("팀원 소개 PNG")

elif st.session_state.selected_page == "기타 정보":
    with st.expander("📚 기타 정보", expanded=True):
        st.markdown("""
        🔹 프로젝트 Github 링크: [**ASAC 7기 Data Analysis Project**](https://github.com/da-analysis/asac_7_dataanalysis.git)<br>
        🔹 참고 데이터 출처 링크 추가 예정 
        """, unsafe_allow_html=True)

