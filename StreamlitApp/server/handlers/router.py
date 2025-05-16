#!/usr/bin/env python
# coding: utf-8

# In[1]:


import re
from langchain_core.runnables import RunnableSequence
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

class LLMRouter:
    def __init__(self):
        self.llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
        self.prompt = PromptTemplate(
            input_variables=["question"],
            template="""
당신은 사용자의 질문에 따라 시스템 목록 분류 키워드와 질문 내용을 기반으로 아래 시스템 중 하나를 선택해야 합니다.
시스템 분류 목록 키워드를 최우선으로 선별 기준으로 채택하고, 질문에 시스템 목록 분류 키워드가 없다면 질문의 내용을 기반으로 선택해주세요.
질문이 너무 일반적이거나 (예: "안녕하세요", "도움이 필요해요") 또는 시스템 분류와 명백히 관련 없는 경우 (예: 계정 문제, 비밀번호, 로그인 등)는 무조건 "X"로 답변하세요.
이전 년도와 분기의 정확한 매출이나 구매건수에 대한 질문은 A,
운영하고 있는 일반적인 상가들에 대한 정보와 서울의 실시간 상권, 인구데이터는 B,
다양한 상황에 맞춰 지원받을 수 있는 정책에 대한 질문은 C 입니다.

[시스템 목록]
A: Databricks Genie API (SQL 매출 분석 관련 질문)
B: Databricks Genie API (SQL 개,폐업한 상가들에 대한 질문 & 서울 실시간 데이터 & 인구밀도, 혼잡도, 유동인구, 주거인구)
C: 소상공인 지원 정책 관련 질문 (RAG 기반 검색)

[시스템 목록 분류 키워드]
A: 매출분석
B: 업종분석, 실시간분석(시간분석)
C: 지원정책

질문: {question}

반드시 A, B, C 중 하나의 알파벳만 단독으로 출력하세요.  
다른 문장, 설명, 인사말 없이 **한 글자만** 출력하세요.  
적절한 분류가 불가능하거나 질문이 무관하다면 "X"를 출력하세요.
"""
        )
        self.chain = self.prompt | self.llm

    def route(self, question: str) -> str:
        result = self.chain.invoke({"question": question})
        text = result.content.strip().upper()

        # A, B, C 중 하나만 추출
        if text in {"A", "B", "C"}:
            return text
        else:
            return "X"


# In[ ]:




