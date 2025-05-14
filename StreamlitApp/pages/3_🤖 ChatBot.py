import streamlit as st
import os 
from server.chatbot_run import ChatbotRun # server 폴더에서 ChatBotTest 클래스 import 

# 세션에 챗봇 객체 저장 
if "chatbot" not in st.session_state:
    st.session_state.chatbot = ChatbotRun()

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
    for history in chatbot.get_chat_history():
        st.markdown(f"**Q:** {history['question']}")
        answer = history["answer"]
        if isinstance(answer, dict):
            if "response_df" in answer:
                st.dataframe(answer["response_df"], use_container_width=True)
            elif "response" in answer:
                val = answer.get("response")

                if isinstance(val, dict):
                    # 중첩 구조일 경우 방어 처리
                    nested_response = val.get("response")
                    if isinstance(nested_response, str):
                        st.markdown(f"<div class='response-box'><b>답변:</b> {nested_response}</div>", unsafe_allow_html=True)
                    else:
                        st.write("🔍 중첩 응답 구조:", type(val), val)
                        st.error("❗중첩된 응답 구조에서 예외 발생")
                elif isinstance(val, str):
                    st.markdown(f"<div class='response-box'><b>답변:</b> {val}</div>", unsafe_allow_html=True)
                else:
                    st.write("🔍 응답 구조:", type(answer), answer)
                    st.error("❗예상치 못한 응답입니다.")


    st.caption("대화 기록은 최근 3개만 표시됩니다.")
    st.write("---")

# ✏️ 새로운 질문 입력
st.subheader("✏️ 새로운 질문 입력")
st.markdown("💡보고 싶은 데이터의 유형에 따라 키워드를 작성해주시면 더 정확한 답변을 드릴 수 있습니다.")
st.markdown("- 소상공인을 지원해주는 정책에 대해 보고 싶으시다면 '#지원정책'을 포함해주세요.")
st.markdown("- 상권들의 매출 및 상세 데이터에 대해 보고 싶으시다면 '#분석'을 포함해주세요.")

# 입력창
st.markdown("<div style='margin-top: 40px'></div>", unsafe_allow_html=True)
st.markdown("**🗂️질문 유형 선택**")
col1, col2 = st.columns(2)

with col1:
    if st.button("📊 분석데이터 질문", key="btn_analysis"):
        st.session_state.user_input_inputbox = "#분석 "

with col2:
    if st.button("🏛 지원정책 질문", key="btn_support"):
        st.session_state.user_input_inputbox = "#지원정책 "

# 스타일 추가
st.markdown("""
<style>
    div.stButton > button {
        border: 1px solid #ccc;
        border-radius: 10px;
        padding: 0.8em 1.2em;
        background-color: #f5f5f5;
        color: #333;
        font-weight: bold;
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button:hover {
        background-color: #e0e0e0;
        border-color: #999;
    }
</style>
""", unsafe_allow_html=True)

user_input = st.text_area(
    label=" ",
    placeholder="여기에 질문을 입력하세요.",
    key="user_input_inputbox",
    label_visibility="collapsed"
)

# 예시 문구
st.caption("예시 질문 1) : #분석 전통시장 상권에서 한식음식점의 분기별 매출과 구매건수를 보여줘")
st.caption("예시 질문 2): #지원정책 청년 지원 사업에는 어떤게 있는지 알려줘")

# 질문 제출 버튼 + 초기화버튼
col_submit, col_reset = st.columns([1, 1])

with col_submit:
    if st.button("질문하기"):
        if not user_input.strip():
            st.warning("질문을 입력해주세요.")
        else:
            with st.spinner("답변 생성 중..."):
                response = chatbot.ask_question(user_input)

            st.subheader("📝 답변")
            if isinstance(response, dict):
                if "response_df" in response:
                    st.dataframe(response["response_df"], use_container_width=True)
                elif "response" in response:
                    val = response["response"]
                    if isinstance(val, dict) and "response" in val:
                        st.markdown(
                            f"<div class='response-box'><b>질문:</b> {user_input}<br><b>답변:</b> {val['response']}</div>",
                            unsafe_allow_html=True
                        )
                    elif isinstance(val, str):
                        st.markdown(
                            f"<div class='response-box'><b>질문:</b> {user_input}<br><b>답변:</b> {val}</div>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.write("🔍 중첩 응답 구조:", type(val), val)
                        st.error("❗중첩된 응답 구조에서 예외 발생")
                else:
                    st.write("🔍 응답 구조:", type(response), response)
                    st.error("❗예상치 못한 딕셔너리 응답입니다.")
            elif isinstance(response, str):
                st.markdown(
                    f"<div class='response-box'><b>질문:</b> {user_input}<br><b>답변:</b> {response}</div>",
                    unsafe_allow_html=True
                )
            else:
                st.error("❗예상치 못한 응답입니다.")

            st.rerun()

with col_reset:
    if st.button("🔁 대화 초기화"):
        st.session_state.pop("genie_conversation_id", None)
        st.success("Genie 대화가 초기화되었습니다.")
