import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from graph_runner import run_chatbot  # LangGraph 연결 함수

class ChatbotRun:
    def __init__(self):
        self._chat_history = []

    def ask_question(self, question: str):
        result = run_chatbot(question)
        print("[DEBUG] ask_question 결과:", result)

        # 이전과 다른 새 응답이면 대화 히스토리에 추가
        self._chat_history.append({
            "question": question,
            "answer": result
        })

        return result


    def get_chat_history(self):
        print("[DEBUG] 전체 히스토리:", self._chat_history)
        return self._chat_history  # 제한 없이 전체 반환
