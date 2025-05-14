import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from graph_runner import run_chatbot  # LangGraph 연결 함수

class ChatbotRun:
    def __init__(self):
        self._chat_history = []

    def ask_question(self, question: str):
        result = run_chatbot(question)  # dict로 받음
        self._chat_history.append({
            "question": question,
            "answer": result
        })
        return result


    def get_chat_history(self):
        return self._chat_history[-3:]
