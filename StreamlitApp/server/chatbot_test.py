# 테스트용 
from openai import OpenAI
import streamlit as st

class ChatbotTest:
    def __init__(self):
        self.api_key = st.secrets["openai"]["api_key"] # secrets.toml에 등록한 api key
        self.client = OpenAI(api_key=self.api_key)
        self._chat_history = []                        # 내부 전용(private) 속성 


    def ask_question(self, question):
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": question}]
        )
        answer = response.choices[0].message.content.strip()

        # 대화 기록 추가
        self._chat_history.append({
            "question": question,
            "answer": answer
        })

        return answer 


    def get_chat_history(self): 
        # 최근 대화 기록 3개까지만 반환 (뒤에서 3개)
        max_history = 3 
        return self._chat_history[-max_history:]