import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server.graph_runner import run_chatbot  # LangGraph 연결 함수

class ChatbotRun:
    def __init__(self):
        self.chat_history = []

    def ask_question(self, question: str):
        print("[DEBUG] 보내는 history:", self.chat_history)
        result = run_chatbot(
            question,
            history=[f"Q: {item['question']}\nA: {item['answer'].get('response', '')}" for item in self.chat_history]
        )
        print("[DEBUG] 받은 history:", result.get("history"))
        print("[DEBUG] 받은 result:", result.get("response"))
        self.chat_history.append({
            "question": question,
            "answer": result
        })


    def get_chat_history(self):
        print("[DEBUG] 전체 히스토리:", self.chat_history)
        return self.chat_history
