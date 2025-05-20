#!/usr/bin/env python
# coding: utf-8

# In[1]:
import re
from langchain_core.runnables import RunnableSequence
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

class LLMRouter:
    def __init__(self):
        self.llm = ChatOpenAI(model_name="gpt-4.1-mini", temperature=0)
        self.prompt = PromptTemplate(
            input_variables=["question"],
            template="""
당신은 이전 대화 내용과 현재 질문을 참고하여, 다음 네 가지 시스템 중 하나를 분류하는 분류기 역할을 수행합니다.

※ 분류는 아래의 우선순위 및 규칙에 따라 A, B, C, D, X 중 하나의 **한 글자만** 출력해야 하며, 그 외의 문장이나 설명은 포함하지 마십시오.

---

[분류 우선순위 및 규칙]

1. 특정 업종명, 메뉴명, 사업장 이름이 등장하면 → 무조건 B
    → 다른 키워드가 포함되더라도 B로 분류
   - 예: “홍대에 있는 떡볶이집 어때요?”, “탕후루 가게 창업할까요?”

2. A: 다음 조건 중 하나라도 만족하면 A로 분류합니다.
- '전통시장', '발달상권', '골목상권', '관광특구' 중 하나와 '매출' 키워드가 함께 등장하는 경우
- 매출, 객단가, 구매건수 등을 기준으로 한 분석 요청 (예: 랭킹, 평균, 변화 추이 등)
- 연도나 분기를 특정하며 매출 정보를 요청하는 경우

3. B: 개업, 폐업, 업종 정보, 인허가, 시간대별 인구, 서울 실시간 유동인구, 인구밀도 관련 질문

4. C: 개업률, 생존율, 창업위험도, 평균영업기간, 프랜차이즈 관련 질문
- 창업과 관련된 질문에서 "위험"에 관련된 것은 창업위험도를 의미합니다.

5. D: 소상공인 지원정책, 신청방법, 지원금, 신청조건, 신청기간, 사례(또는 우수사례) 관련 질문
- "장사가 안된다", "힘들다", "매출이 없다" 등의 표현은 '경영 부진'으로 해석하세요.

6. X: 다음 중 하나에 해당하는 질문은 무조건 X로 분류
   - 너무 일반적인 경우: “안녕하세요”, “도움이 필요해요”, "어떤 질문을 해야 하나요"
   - 시스템과 명백히 무관한 경우: 계정 문제, 로그인 오류, 비밀번호 등

---

[출력 형식]

- 반드시 A, B, C, D, X 중 하나의 **알파벳만 단독 출력**하십시오.
- 다른 문장, 설명, 인사말 등은 절대 포함하지 마십시오.

---

질문: {question}
"""
        )
        self.chain = self.prompt | self.llm

    def route(self, question: str, context: str = "") -> str:
        full_question = f"{context}\n{question}".strip()
        result = self.chain.invoke({"question": full_question})
        text = result.content.strip().upper()

        if text in {"A", "B", "C", "D"}:
            return text
        else:
            return "X"


# In[ ]:




