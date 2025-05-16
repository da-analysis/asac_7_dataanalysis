import streamlit as st
import os
import io
import pandas as pd
import matplotlib.pyplot as plt
from server.chatbot_run import ChatbotRun

# 세션 상태에 챗봇 인스턴스 저장
if "chatbot" not in st.session_state:
    st.session_state.chatbot = ChatbotRun()

chatbot = st.session_state.chatbot

# 페이지 제목
st.title("🤖 챗봇")
st.markdown("### 📖 사용설명서")

st.markdown("""
- 이 챗봇은 **상권 매출 분석**, **서울시 인구데이터**, **정부 지원 정책** 등 다양한 데이터를 기반으로 질문에 답변해줍니다.
""")

with st.expander("🔎 제공 데이터 항목 보기"):
    st.markdown("""
    - 전국 전통시장 및 관광특구의 **매출, 객단가, 업종별 정보**
    - **시간대별 유동인구** 및 **성별/연령대 비율**
    - **청년·소상공인 정책 데이터**
    - 👉 관련된 데이터가 궁금하시다면 **[데이터 확인하기](#)**  
    """)

st.markdown("""
- 예시 질문을 클릭하면 자동으로 질문이 입력됩니다.
- 제공하지 않는 데이터가 있을 수 있습니다.
- 매출 데이터의 경우 특정 카드사의 API를 활용하여 실제 데이터와 차이가 있을 수 있습니다.
- 응답이 제대로 나오지 않는 경우는 채팅창 우측상단의 '대화 초기화'를 누른 뒤 다시 시도해주세요.
""")

# 이전 대화 출력
for chat in chatbot.get_chat_history():
    with st.chat_message("user"):
        st.markdown(chat["question"])

    with st.chat_message("assistant"):
        answer = chat["answer"]

        if isinstance(answer, dict):
            if answer.get("response"):
                st.markdown(answer["response"].replace("\n", "  \n"))

            description = answer.get("description")
            if description:
                st.markdown(f"**📝 답변:** {description}")

            df = answer.get("response_df")
            if isinstance(df, pd.DataFrame):
                try:
                    formatted_df = df.copy()
                    for col in formatted_df.select_dtypes(include=["number"]).columns:
                        formatted_df[col] = formatted_df[col].apply(lambda x: f"{x:,.0f}")

                    st.dataframe(formatted_df)

                    numeric_cols = df.select_dtypes(include="number").columns
                    if len(numeric_cols) >= 2:
                        x_col = df.columns[0]
                        y1_col = numeric_cols[0]
                        y2_col = numeric_cols[1]

                        fig, ax1 = plt.subplots(figsize=(10, 5))
                        ax2 = ax1.twinx()

                        ax1.plot(df[x_col], df[y1_col], color='tab:blue', marker='o')
                        ax2.plot(df[x_col], df[y2_col], color='tab:orange', marker='x')

                        ax1.set_xlabel(x_col)
                        ax1.set_ylabel(y1_col, color='tab:blue')
                        ax2.set_ylabel(y2_col, color='tab:orange')
                        plt.title(f"{y1_col} & {y2_col} by {x_col}")
                        plt.xticks(rotation=45)
                        plt.tight_layout()

                        st.pyplot(fig)

                except Exception as e:
                    st.markdown(f"⚠️ 시각화 오류: {e}")

        elif isinstance(answer, pd.DataFrame):
            st.dataframe(answer)

        else:
            st.markdown(str(answer).replace("\n", "  \n"))

# 🔁 대화 초기화 버튼
cols = st.columns([5, 1])  # 왼쪽: 넓게, 오른쪽: 좁게
with cols[1]:  # 가장 오른쪽 열
    if st.button("대화 초기화"):
        st.session_state.chatbot = ChatbotRun()
        chatbot = st.session_state.chatbot
        st.rerun()
    

# 📝 질문 입력
example_prompt = st.session_state.pop("example_prompt") if "example_prompt" in st.session_state else ""
input_container = st.container()
with input_container:
    prompt = st.chat_input("질문을 입력하세요")
    if example_prompt:
        st.session_state["_input_chat"] = example_prompt
        st.rerun()

prompt = st.session_state.pop("_input_chat") if "_input_chat" in st.session_state else prompt

if prompt:
    with st.spinner("생성 중..."):
        result = chatbot.ask_question(prompt)
    st.rerun()

# 예시 질문 버튼
st.markdown("""
<div style="display: flex; justify-content: left; margin: 10px 0;">
    <div style="
        padding: 10px 20px;
        background-color: #FAFAFA;
        color: #333;
        border-radius: 10px;
        font-size: 16px;
        font-weight: bold;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        cursor: default;
    ">
        🗂️ 예시 질문
    </div>
</div>
""", unsafe_allow_html=True)
example_questions = [
    "전통시장에서 2024년 3분기에 가장 높은 객단가를 기록한 업종을 3개정도 보여주세요",
    "관광특구에서 남성에게 매출기준 가장 인기가 높은 업종 TOP10을 보여주세요",
    "오후 8시에 가장 유동인구가 많은 지역 10개를 보여줘",
    "지금 인구밀도가 가장 높은 곳은 어디인가요?",
    "청년이 창업하기 위해 지원받을 수 있는게 있을까요?",
    "요즘 장사가 너무 안되는데 도움을 받을 수 있는 지원이 있을까요?",
]

# 2열씩 나누어 출력
for i in range(0, len(example_questions), 2):
    cols = st.columns(2)
    for j in range(2):
        if i + j < len(example_questions):
            if cols[j].button(example_questions[i + j]):
                st.session_state["example_prompt"] = example_questions[i + j]
                st.rerun()