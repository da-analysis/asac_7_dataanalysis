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

[시스템 목록]
A: Databricks Genie API (SQL 분석 관련 질문)
B: 청년/소상공인 정책 관련 질문 (RAG 기반 검색)

[시스템 목록 분류 키워드]
A: #분석
B: #지원정책

질문: {question}

반드시 A 또는 B 하나만 출력하세요. 다른 문장, 설명 없이!
"""
        )
        self.chain = self.prompt | self.llm

    def route(self, question: str) -> str:
        result = self.chain.invoke({"question": question})
        text = result.content.strip().upper()
    
        match = re.search(r"\b(A|B)\b", text)
        if match:
            return match.group(1)
        else:
            raise ValueError(f"Invalid route: {text}")


# In[ ]:




