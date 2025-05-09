# Generated from Jupyter notebook

from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal
from handlers.genie_api_handler import GenieAPIHandler
from handlers.local_rag_handler import LocalRAGHandler
from handlers.router import LLMRouter

import os, sys
sys.path.insert(0, "../handlers")

# OpenAI API Key 설정
from dotenv import load_dotenv

load_dotenv()

# API 키를 환경변수로 변경
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DATABRICKS_TOKEN = os.getenv('DATABRICKS_TOKEN')

# ─────────────────────────────────────────────────────────────
# 1. 시스템 클래스 인스턴스 정의
genie_api = GenieAPIHandler(
    workspace=os.getenv('DATABRICKS_WORKSPACE'),
    token=os.getenv('DATABRICKS_TOKEN'),
    space_id=os.getenv('DATABRICKS_SPACE_ID')
)

rag_api = LocalRAGHandler(
    bucket=os.getenv('RAG_BUCKET'),
    key=os.getenv('RAG_KEY')
)

router = LLMRouter()

# ─────────────────────────────────────────────────────────────
# 2. 상태 타입 정의
class GraphState(TypedDict):
    question: str
    route: Literal["A", "B"]
    response: str

# ─────────────────────────────────────────────────────────────
# 3. LangGraph 노드 정의

# 입력 노드
def question_node(state: GraphState) -> GraphState:
    return state

# 분류 노드
def classify_node(state: GraphState) -> GraphState:
    question = state["question"]
    route = router.route(question)
    return {**state, "route": route}

# A 시스템 처리
def genie_node(state: GraphState) -> GraphState:
    result = genie_api.ask(state["question"])
    description = result.get("query_description", "(쿼리 설명 없음)")
    data = result.get("data", {})

    # Genie의 실제 결과 위치 반영
    data_array = (
        data.get("statement_response", {})
            .get("result", {})
            .get("data_array", [])
    )

    columns_schema = (
        data.get("statement_response", {})
            .get("manifest", {})
            .get("schema", {})
            .get("columns", [])
    )
    column_names = [col.get("name", f"col{i}") for i, col in enumerate(columns_schema)]

    # 결과 포맷
    if data_array and column_names:
        header = " | ".join(column_names)
        divider = "-" * len(header)
        table = "\n".join([" | ".join(map(str, row)) for row in data_array])
        formatted_result = f"{header}\n{divider}\n{table}"
    else:
        formatted_result = "(쿼리 결과 없음)"

    # 전체 응답 구성
    # full_response = f"[쿼리 설명]\n{description}\n\n[쿼리 결과]\n{formatted_result}"
    return {**state, "response": formatted_result}


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
    print("\n ㄴ답변:", output["response"])

