from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal
from handlers.genie_api_handler import GenieAPIHandler
from handlers.local_rag_handler import LocalRAGHandler
from handlers.router import LLMRouter
from dotenv import load_dotenv
import time
import pandas as pd
import streamlit as st
import os, sys
sys.path.insert(0, "../handlers")
load_dotenv()

# OpenAI API Key 설정
os.environ["OPENAI_API_KEY"]

# ─────────────────────────────────────────────────────────────
# 1. 시스템 클래스 인스턴스 정의
genie_api = GenieAPIHandler(
    workspace=os.environ["DATABRICKS_WORKSPACE"],
    token=os.environ["DATABRICKS_TOKEN"],
    space_id=os.environ["DATABRICKS_SPACE_ID"]
)


rag_api = LocalRAGHandler(
    bucket= os.environ["BUCKET_NAME"],
    key=os.environ["BUCKET_KEY"]
)

router = LLMRouter()

# ─────────────────────────────────────────────────────────────
# 2. 상태 타입 정의
class GraphState(TypedDict, total=False):
    question: str
    route: Literal["A", "B"]
    response: str
    response_df: pd.DataFrame

# ─────────────────────────────────────────────────────────────
# 3. LangGraph 노드 정의

# 입력 노드
def question_node(state: GraphState) -> GraphState:
    return state

# 분류 노드
def classify_node(state: GraphState) -> GraphState:
    question = state["question"]
    route = router.route(question)
    print(f"[DEBUG] 분류된 경로: {route}") 
    return {**state, "route": route}

# A 시스템 처리
def genie_node(state: GraphState) -> GraphState:
    try:
        print("[DEBUG] genie_node 진입")
        question = state["question"]
        print(f"[DEBUG] 질문: {question}")

        # conversation_id 유지 여부 체크
        if "genie_conversation_id" not in st.session_state:
            print("[DEBUG] 대화 새로 시작")
            result = genie_api.start_conversation(question)
            st.session_state["genie_conversation_id"] = result["conversation_id"]
        else:
            print("[DEBUG] 이전 대화 계속 사용")
            result = genie_api.ask_followup(st.session_state["genie_conversation_id"], question)

        conversation_id = result["conversation_id"]
        message_id = result["message_id"]
        print(f"[DEBUG] conversation_id: {conversation_id}, message_id: {message_id}")

        # attachments polling
        for i in range(15):
            print(f"[DEBUG] polling {i+1}/15 ...")
            time.sleep(2)
            message = genie_api.get_query_info(conversation_id, message_id)
            print("[DEBUG] message 객체 타입:", type(message))
            print("[DEBUG] message 객체 내용:", message)

            attachments = message.get("attachments", [])
            status_val = message.get("status", "")  # ← 여기 수정함
            print("[DEBUG] 현재 상태:", status_val)
            if status_val in ("SUCCEEDED", "COMPLETED") and attachments:
                print("[DEBUG] 쿼리 성공!")
                break
        else:
            return {**state, "response": "❗쿼리 결과를 가져오는 데 실패했습니다."}

        attachment_id = attachments[0]["attachment_id"]
        description = attachments[0]["query"]["description"]

        result_data = genie_api.get_query_result(conversation_id, message_id, attachment_id)

        data_array = result_data.get("statement_response", {}).get("result", {}).get("data_array", [])
        columns_schema = result_data.get("statement_response", {}).get("manifest", {}).get("schema", {}).get("columns", [])

        print("[DEBUG] data_array:", data_array)
        print("[DEBUG] columns_schema:", columns_schema)

        column_names = [col.get("name", f"col{i}") for i, col in enumerate(columns_schema)]

        if data_array and column_names:
            df = pd.DataFrame(data_array, columns=column_names)
            return {**state, "response_df": df, "description": description}
        else:
            return {**state, "response": "데이터가 비어있습니다. 더 구체적인 질문을 해보세요."}

    except Exception as e:
        print("[ERROR] 예외 발생:", str(e))
        print("[ERROR] 예외 타입:", type(e))
        return {**state, "response": f"❗데이터 처리 중 오류가 발생했습니다.\n({str(e)})"}


# B 시스템 처리
def rag_node(state: GraphState) -> GraphState:
    answer, _ = rag_api.ask(state["question"])
    return {**state, "response": answer}

# 최종 응답 노드
def response_node(state: GraphState) -> GraphState:
    return state

# ─────────────────────────────────────────────────────────────
# 4. LangGraph 구성

builder = StateGraph(GraphState)
builder.set_entry_point("question_node")

builder.add_node("question_node", question_node)
builder.add_node("classify_node", classify_node)
builder.add_node("genie_node", genie_node)
builder.add_node("rag_node", rag_node)
builder.add_node("respond_node", response_node)

builder.set_entry_point("question_node")
builder.add_edge("question_node", "classify_node")

builder.add_conditional_edges(
    "classify_node",
    lambda state: state["route"],
    {
        "A": "genie_node",
        "B": "rag_node",
    }
)

builder.add_edge("genie_node", "respond_node")
builder.add_edge("rag_node", "respond_node")
builder.set_finish_point("respond_node")

graph = builder.compile()

# ─────────────────────────────────────────────────────────────
# 5. 실행 예시

if __name__ == "__main__":
    user_input = input("질문을 입력하세요: ")
    output = graph.invoke({"question": user_input})

    if "response_df" in output:
        print("\n[📊 데이터프레임 결과]")
        print(output["response_df"])
    elif "response" in output:
        print("\n[💬 텍스트 응답]")
        print(output["response"])
    else:
        print("\n❗답변이 없습니다.")

def run_chatbot(question: str) -> dict:
    output = graph.invoke({"question": question})

    if "response_df" in output:
        return {"response_df": output["response_df"]}
    elif "response" in output:
        return {"response": output["response"]}
    else:
        return {"response": "❗답변을 생성하지 못했습니다. 다시 시도해 주세요."}


# In[ ]:




