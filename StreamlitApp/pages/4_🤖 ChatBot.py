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
st.title("🤖 LangGraph 기반 챗봇")

# 🔁 대화 초기화 버튼
if st.button("대화 초기화"):
    st.session_state.chatbot = ChatbotRun()
    chatbot = st.session_state.chatbot
    st.rerun()

# 이전 대화 출력
for chat in chatbot.get_chat_history():
    with st.chat_message("user"):
        st.markdown(chat["question"])

    with st.chat_message("assistant"):
        answer = chat["answer"]

        if isinstance(answer, dict):
            # 텍스트 응답 출력 (가장 먼저)
            if answer.get("response"):
                st.markdown(answer["response"].replace("\n", "  \n"))

            # 설명 출력 (있을 때만)
            description = answer.get("description")
            if description:
                st.markdown(f"**📝 쿼리 설명:** {description}")

            # 데이터프레임 시각화
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

# 📝 질문 입력
if prompt := st.chat_input("질문을 입력하세요"):
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("생성 중..."):
        result = chatbot.ask_question(prompt)

    with st.chat_message("assistant"):
        if isinstance(result, dict):
            # 텍스트 응답 출력
            if result.get("response"):
                st.markdown(result["response"].replace("\n", "  \n"))

            # 설명 출력 (있을 때만)
            description = result.get("description")
            if description:
                st.markdown(f"**📝 쿼리 설명:** {description}")

            # 데이터프레임 출력
            if result.get("response_df") is not None:
                df = result["response_df"]
                st.dataframe(df)

        else:
            st.markdown(str(result))