from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal
from handlers.genie_sales_handler import GenieSALESHandler
from handlers.genie_license_handler import GenieLICENSEHandler
from handlers.local_rag_handler import LocalRAGHandler
from handlers.router import LLMRouter
from handlers.fallback_handler import fallback_example_node
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
genie_sales_api = GenieSALESHandler(
    workspace=os.environ["DATABRICKS_WORKSPACE"],
    token=os.environ["DATABRICKS_TOKEN_SALE"],
    space_id=os.environ["DATABRICKS_SPACE_ID_SALE"]
)

genie_license_api = GenieLICENSEHandler(
    workspace=os.environ["DATABRICKS_WORKSPACE"],
    token=os.environ["DATABRICKS_TOKEN_LICENSE"],
    space_id=os.environ["DATABRICKS_SPACE_ID_LICENSE"]
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
    route: Literal["A", "B", "C", "X"]
    response: str
    response_df: pd.DataFrame
    description: str 
# ─────────────────────────────────────────────────────────────
# 3. LangGraph 노드 정의

# 입력 노드
def question_node(state: GraphState) -> GraphState:
    return state

# 분류 노드
def classify_node(state: GraphState) -> GraphState:
    question = state["question"]
    route = router.route(question)
    print(f"[DEBUG] 분류된 경로 원본: {route!r}")  # 문자열 그대로 출력
    normalized_route = route.strip().upper()
    print(f"[DEBUG] 정규화된 경로: {normalized_route}")
    
    if normalized_route == "B":
        st.session_state.pop("genie_conversation_id", None)
        print("[DEBUG] Genie 세션 초기화 완료")
    
    return {**state, "route": normalized_route}

# A 시스템 처리
def genie_sales_node(state: GraphState) -> GraphState:
    try:
        question = state["question"]

        # conversation_id 유지 여부 체크
        if "genie_sales_conversation_id" not in st.session_state:
            print("[DEBUG] [SALES] 대화 새로 시작")
            result = genie_sales_api.start_conversation(question)
            st.session_state["genie_sales_conversation_id"] = result["conversation_id"]
        else:
            print("[DEBUG] [SALES] 이전 대화 계속 사용")
            result = genie_sales_api.ask_followup(st.session_state["genie_sales_conversation_id"], question)

        conversation_id = result["conversation_id"]
        message_id = result["message_id"]
        print(f"[DEBUG] [SALES] conversation_id: {conversation_id}, message_id: {message_id}")

        # attachments polling
        for i in range(15):
            print(f"[DEBUG] [SALES] polling {i+1}/15 ...")
            time.sleep(2)
            message = genie_sales_api.get_query_info(conversation_id, message_id)
            attachments = message.get("attachments", [])
            status_val = message.get("status", "")
            print("[DEBUG] [SALES] 현재 상태:", status_val)
            if status_val in ("SUCCEEDED", "COMPLETED") and attachments:
                print("[DEBUG] [SALES] 쿼리 성공!")
                break
        else:
            return {**state, "response": "❗쿼리 결과를 가져오는 데 실패했습니다."}

        attachment = attachments[0]
        query_block = attachment.get("query")
        text_block = attachment.get("text", {}).get("content")

        if not query_block:
            return {**state, "response": text_block or "답변은 생성됐지만 실행 가능한 쿼리는 없었습니다."}

        attachment_id = attachment["attachment_id"]
        description = query_block.get("description", None)

        result_data = genie_sales_api.get_query_result(conversation_id, message_id, attachment_id)
        data_array = result_data.get("statement_response", {}).get("result", {}).get("data_array", [])
        columns_schema = result_data.get("statement_response", {}).get("manifest", {}).get("schema", {}).get("columns", [])
        column_names = [col.get("name", f"col{i}") for i, col in enumerate(columns_schema)]

        if data_array and column_names:
            df = pd.DataFrame(data_array, columns=column_names)
            return {**state, "response_df": df, "description": description}
        else:
            return {**state, "response": "데이터가 비어있습니다.", "description": description}

    except Exception as e:
        print("[ERROR] [SALES] 예외 발생:", str(e))
        return {**state, "response": f"❗데이터 처리 중 오류가 발생했습니다.\n({str(e)})"}

# B 시스템 처리
def genie_license_node(state: GraphState) -> GraphState:
    try:
        question = state["question"]

        if "genie_license_conversation_id" not in st.session_state:
            print("[DEBUG] [LICENSE] 대화 새로 시작")
            result = genie_license_api.start_conversation(question)
            st.session_state["genie_license_conversation_id"] = result["conversation_id"]
        else:
            print("[DEBUG] [LICENSE] 이전 대화 계속 사용")
            result = genie_license_api.ask_followup(st.session_state["genie_license_conversation_id"], question)

        conversation_id = result["conversation_id"]
        message_id = result["message_id"]
        print(f"[DEBUG] [LICENSE] conversation_id: {conversation_id}, message_id: {message_id}")

        for i in range(15):
            print(f"[DEBUG] [LICENSE] polling {i+1}/15 ...")
            time.sleep(2)
            message = genie_license_api.get_query_info(conversation_id, message_id)
            attachments = message.get("attachments", [])
            status_val = message.get("status", "")
            print("[DEBUG] [LICENSE] 현재 상태:", status_val)
            if status_val in ("SUCCEEDED", "COMPLETED") and attachments:
                print("[DEBUG] [LICENSE] 쿼리 성공!")
                break
        else:
            return {**state, "response": "❗쿼리 결과를 가져오는 데 실패했습니다."}

        attachment = attachments[0]
        query_block = attachment.get("query")
        description = query_block.get("description", None)
        attachment_id = attachment["attachment_id"]

        result_data = genie_license_api.get_query_result(conversation_id, message_id, attachment_id)
        data_array = result_data.get("statement_response", {}).get("result", {}).get("data_array", [])
        columns_schema = result_data.get("statement_response", {}).get("manifest", {}).get("schema", {}).get("columns", [])
        column_names = [col.get("name", f"col{i}") for i, col in enumerate(columns_schema)]

        if data_array and column_names:
            df = pd.DataFrame(data_array, columns=column_names)
            return {**state, "response_df": df, "description": description}
        else:
            return {**state, "response": "데이터가 비어있습니다.", "description": description}
    except Exception as e:
        print("[ERROR] [LICENSE] 예외 발생:", str(e))
        return {**state, "response": f"❗LICENSE 처리 중 오류 발생: {str(e)}"}


# C 시스템 처리
def rag_node(state: GraphState) -> GraphState:
    answer, meta = rag_api.ask(state["question"])
    print("[DEBUG][RAG] answer:", answer)
    print("[DEBUG][RAG] meta:", meta)
    return {**state, "response": answer}

# fallback 처리 노드 (분류 실패 시 예시 안내)
def fallback_node(state: GraphState) -> GraphState:
    return {
        **state,
        "response": fallback_example_node(state["question"])["response"]
    }

# 최종 응답 노드
def response_node(state: GraphState) -> GraphState:
    return {
        "response_df": state.get("response_df"),
        "response": state.get("response"),
        "description": state.get("description")
    }

# ─────────────────────────────────────────────────────────────
# 4. LangGraph 구성

builder = StateGraph(GraphState)
builder.set_entry_point("question_node")

builder.add_node("question_node", question_node)
builder.add_node("classify_node", classify_node)
builder.add_node("genie_sales_node", genie_sales_node)
builder.add_node("genie_license_node", genie_license_node)
builder.add_node("rag_node", rag_node)
builder.add_node("respond_node", response_node)
builder.add_node("fallback_node", fallback_node)
builder.add_edge("question_node", "classify_node")

builder.add_conditional_edges(
    "classify_node",
    lambda state: state["route"].strip().upper(),
    {
        "A": "genie_sales_node",
        "B": "genie_license_node",
        "C": "rag_node",
        "X": "fallback_node",
    }
)

builder.add_edge("genie_sales_node", "respond_node")
builder.add_edge("genie_license_node", "respond_node")
builder.add_edge("rag_node", "respond_node")
builder.add_edge("fallback_node", "respond_node")
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
    print("[DEBUG] 최종 output:", output)

    return {
        "response": output.get("response"),
        "response_df": output.get("response_df"),
        "description": output.get("description"),
        "route": output.get("route")
    }



# In[ ]:




