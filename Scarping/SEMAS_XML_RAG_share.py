# Databricks notebook source
# MAGIC %md
# MAGIC # 설치패키지

# COMMAND ----------

!pip install -U langchain-community

# COMMAND ----------

!pip install -U langchain-openai

# COMMAND ----------

!pip install openai

# COMMAND ----------

!pip install chromadb

# COMMAND ----------

!pip install tiktoken

# COMMAND ----------

# MAGIC %md
# MAGIC # RAG Function

# COMMAND ----------

import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.prompts import PromptTemplate
import os
import logging

logging.basicConfig()
logging.getLogger("langchain.retrievers.multi_query").setLevel(logging.INFO)

# OpenAI API Key 설정
os.environ["OPENAI_API_KEY"] = "OPENAI_KEY_HERE"  # OPENAI_KEY_HERE 대신 본인 키 입력

# 1. XML 파싱 및 구조적 정보 추출 변환 함수
def load_documents_from_xml(file_path):
    results = []
    tree = ET.parse(file_path)
    root = tree.getroot()

    for category in root.findall("Category"):
        category_name = category.get("name", "")
        subcategories = category.findall("Subcategory")

        if subcategories:
            for subcat in subcategories:
                subcategory_name = subcat.get("name", "")
                for item in subcat.findall("Item"):
                    title = item.findtext("Title")
                    url = item.findtext("URL")
                    content_html = item.findtext("Content")
                    soup = BeautifulSoup(content_html or "", "html.parser")
                    for dl in soup.find_all("dl"):
                        dt = dl.find("dt")
                        dd = dl.find("dd")
                        if dt and dd:
                            results.append({
                                "Category": category_name,
                                "Subcategory": subcategory_name,
                                "Title": title,
                                "URL": url,
                                "구분": dt.get_text(strip=True),
                                "내용": dd.get_text(separator="\n", strip=True)
                            })
        else:
            for item in category.findall("Item"):
                title = item.findtext("Title")
                url = item.findtext("URL")
                content_html = item.findtext("Content")
                soup = BeautifulSoup(content_html or "", "html.parser")
                for dl in soup.find_all("dl"):
                    dt = dl.find("dt")
                    dd = dl.find("dd")
                    if dt and dd:
                        results.append({
                            "Category": category_name,
                            "Subcategory": None,
                            "Title": title,
                            "URL": url,
                            "구분": dt.get_text(strip=True),
                            "내용": dd.get_text(separator="\n", strip=True)
                        })

    # 청킹 시 metadata 포함
    texts = []
    metadatas = []

    for r in results:
        if r["구분"] not in ["문의처", "설문", "만족도"]:
            texts.append(
                f"카테고리: {r['Category']}\n소분류: {r['Subcategory']}\n제목: {r['Title']}\n구분: {r['구분']}\n내용: {r['내용']}"
            )
            metadatas.append({"title": r["Title"], "source": r["URL"]})

    return texts, metadatas

# 2. RAG 초기 세팅
def intialize_qa_chain(file_path):
    texts, metadatas = load_documents_from_xml(file_path)
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    documents = splitter.create_documents(texts, metadatas=metadatas)

    embedding = OpenAIEmbeddings(model="text-embedding-ada-002")
    vectorstore = Chroma.from_documents(documents, embedding, collection_name="semas-structured")

    prompt_template = PromptTemplate(
        input_variables=["summaries", "question"],
        template="""
    소상공인들의 성공적인 창업 및 경영을 위한 답변이 필요합니다.
    질문과 관련된 모든 정책을 나열하고 다음 문서 내용을 기반으로 질문에 답하세요.
    '내용'에 해당하는 답변을 해야할 때는 반드시 해당 지원사업의 'Title'의 이름을 명시해야합니다.
    ※ 만족도 설문, 문의처 등은 제외하고 정책 내용 위주로 설명하세요.
    ※ 해당하는 사업의 'Title'을 강조한 후, 상세내용을 가능한한 상세하게 설명하세요.
    
    문서:
    {summaries}
    
    질문:
    {question}
    
    답변:
    """
    )

    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
    retriever = MultiQueryRetriever.from_llm(retriever = vectorstore.as_retriever(), llm = llm)

    return RetrievalQAWithSourcesChain.from_chain_type(
        retriever=retriever,
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt_template},
        llm = llm
    )

def ask_question(qa_chain, question: str):
    response = qa_chain.invoke({"question": question})
    print(response["answer"])

    # 관련된 URL 추출
    if response["sources"]:
        print(f"\n자세한 사항은 {response['sources'].split(',')[0]} 를 참조하세요.")
    else:
        print("\n자세한 사항은 https://www.semas.or.kr/ 를 참조하세요.")!pip install --upgrade numpy pandas

# COMMAND ----------

# 질문 시 아래 코드 두 줄만 복사해서 사용

qa_chain = intialize_qa_chain("semas_supportcontents.xml")  # 연결할 XML 파일 경로로 설정

ask_question(qa_chain, "폐업 준비 중인데, 재기를 위한 지원책이 있나요?")

# COMMAND ----------


