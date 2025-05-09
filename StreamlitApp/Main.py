import streamlit as st
import os

# 페이지 제목  
st.set_page_config(page_title="소상공인 현황 분석 및 폐업률 예측", page_icon="🏪", layout="wide")

# load css 
def load_css(file_path):
    if os.path.exists(file_path):
        with open(file_path, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
main_css_path = os.path.join(BASE_DIR, 'assets', 'css', 'main.css')
load_css(main_css_path)

# 제목
st.markdown("""
<h1>멀티소스 데이터를 활용한<br>소상공인 현황 분석 및 폐업률 예측 시스템 개발 🏪</h1>
""", unsafe_allow_html=True)

# 버튼 스타일 커스텀 (외부 css로 버튼 크기조정이 불가 -> 마크다운으로 감싸서 커스텀)
st.markdown("""
<style>
div.stButton > button {
    width: 100%;
    height: 55px;
    font-size: 24px;
    font-weight: bold;
    margin-top: 0.5rem;
    border-radius: 12px;
    background-color: #f0f0f0;
    color: #333;
    transition: background-color 0.3s, transform 0.2s;
} 
div.stButton > button:hover {
    background-color: #d0d0d0;
    transform: scale(1.02);
}
</style>
# """, unsafe_allow_html=True) 

# 세션 초기화
if "selected_page" not in st.session_state:
    st.session_state.selected_page = "프로젝트 소개"

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
    with st.expander("🗂️ 프로젝트 소개 (예시)", expanded=True):
        st.markdown("""
        <div class="intro-container">
          <strong>
            전국 상권·인구·매출 데이터를 수집·전처리해  
            소상공인 폐업 확률을 예측하고,  
            대시보드와 챗봇으로 관련 정보를 제공합니다.
          </strong><br><br>
          🔹 데이터 수집 & 전처리<br>
          🔹 폐업 확률 예측 & API화<br>
          🔹 창업 지원 정책 챗봇 개발
        </div>
        """, unsafe_allow_html=True)

    st.write("---")
    st.markdown("<h3 style='font-size:26px;'>📄 페이지 미리보기</h3>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📊 대시보드", "📈 폐업률 예측 서비스", "🤖 ChatBot"])

    with tab1:
        st.subheader("📊 대시보드")
        st.markdown("""
        🔹 지역/업종/폐업개업 현황 시각화  
        🔹 서울시 실시간 상권/인구/매출 데이터 분석
        """)
        st.info("대시보드 미리보기 이미지 준비 중입니다.")

    with tab2:
        st.subheader("📈 폐업률 예측 서비스")
        st.markdown("""
        🔹 지역/업종 기반 폐업 확률(%) 예측  
        🔹 폐업 여부 분류 제공
        """)
        st.info("예측 서비스 화면 준비 중입니다.")

    with tab3:
        st.subheader("🤖 ChatBot")
        st.markdown("""
        🔹 창업 지원 정책에 대한 Q&A 챗봇  
        🔹 LLM과 RAG 기법 기반 답변 제공
        """)
        st.info("챗봇 인터페이스 준비 중입니다.")

elif st.session_state.selected_page == "팀원 소개":
    with st.expander("👨‍👩‍👧‍👦 팀원 소개", expanded=True):
        st.markdown("팀원 소개 PNG")

elif st.session_state.selected_page == "기타 정보":
    with st.expander("📚 기타 정보", expanded=True):
        st.markdown("""
        🔹 프로젝트 Github 링크: [**ASAC 7기 Data Analysis Project**](https://github.com/da-analysis/asac_7_dataanalysis.git)<br>
        🔹 참고 데이터 출처 링크 추가 예정 
        """, unsafe_allow_html=True)

