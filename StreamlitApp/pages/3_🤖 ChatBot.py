import streamlit as st
import os 
from server.chatbot_test import ChatbotTest # server 폴더에서 ChatBotTest 클래스 import 


# 세션에 챗봇 객체 저장 
if "chatbot" not in st.session_state:
    st.session_state.chatbot = ChatbotTest()

chatbot = st.session_state.chatbot

# load css - main.css, chatbot.css 
def load_css(file_path):
    if os.path.exists(file_path):
        with open(file_path, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_css(os.path.join(BASE_DIR, '..', 'assets', 'css', 'main.css'))
load_css(os.path.join(BASE_DIR, '..', 'assets', 'css', 'chatbot.css'))

# 본문
st.title("🤖 ChatBot")
st.markdown("창업에 대한 궁금증을 입력하면 답변해드립니다.")
st.write("---")

# 대화 기록 표시
if chatbot.get_chat_history():
    st.subheader("📝 대화 기록")
    for chat in chatbot.get_chat_history():
        st.markdown(
            f"<div class='response-box'><b>질문:</b> {chat['question']}<br><b>답변:</b> {chat['answer']}</div>",
            unsafe_allow_html=True
        )
    st.caption("대화 기록은 최근 3개만 표시됩니다.")
    st.write("---")

# ✏️ 새로운 질문 입력
st.subheader("✏️ 새로운 질문 입력")
st.markdown("**질문을 입력하세요.**")

# 입력창
user_input = st.text_area(
    label=" ",
    placeholder="여기에 질문을 입력하세요.",
    key="user_input_inputbox",
    label_visibility="collapsed"
)

# 예시 문구
st.caption("예시 질문: 우리나라 국내 매출 TOP 3 기업을 알려줘")

# 버튼 클릭
if st.button("질문하기"):
    if not user_input.strip():
        st.warning("질문을 입력해주세요.")
    else:
        with st.spinner('답변 생성 중...'):
            chatbot.ask_question(user_input)  # chatbot에게 질문을 보내고 답변 받음
        st.rerun()

    