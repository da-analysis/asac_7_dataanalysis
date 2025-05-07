# Databricks notebook source
# MAGIC %md
# MAGIC ## 설치파일

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

!pip install --upgrade numpy pandas

# COMMAND ----------

!pip install boto3

# COMMAND ----------

!pip install lxml

# COMMAND ----------

# MAGIC %md
# MAGIC ## S3 서버로 파일 연결

# COMMAND ----------

# s3 경로 확인
import requests

DATABRICKS_HOST = "https://tacademykr-asacdataanalysis.cloud.databricks.com"
TOKEN = "YOUR_DATABRICKS_TOKEN"     # DATABRICKS_TOKEN 입력
VOLUME_NAME = "bronze.crawling_semas.xml"
# /Volumes/bronze/crawling_semas/xml/latest/semas_supportcontents.xml
headers = {
    "Authorization": f"Bearer {TOKEN}"
}

resp = requests.get(
    f"{DATABRICKS_HOST}/api/2.1/unity-catalog/volumes/{VOLUME_NAME}",
    headers=headers
)

volume_info = resp.json()
s3_path = volume_info["storage_location"]
print("S3 위치:", s3_path)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 코드(함수)

# COMMAND ----------

import io
import boto3
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
os.environ["OPENAI_API_KEY"] = "YOUR_OPENAI_API_KEY"   # OPENAI_API_KEY 입력

def load_documents_from_s3_xml(bucket, key):
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=bucket, Key=key)
    xml_bytes = obj['Body'].read()

    results = []
    root = ET.fromstring(xml_bytes)

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
                    soup = BeautifulSoup(content_html or "", "lxml")
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

# 2. 초기 세팅
def intialize_qa_chain_from_s3(bucket,key):
    texts, metadatas = load_documents_from_s3_xml(bucket,key)
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
        print("\n자세한 사항은 https://www.semas.or.kr/ 를 참조하세요.")

# COMMAND ----------

qa_chain = intialize_qa_chain("semas_supportcontents.xml")

ask_question(qa_chain, "폐업 준비 중인데, 재기를 위한 지원책이 있나요?")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 질문

# COMMAND ----------

# 연결 xml S3 경로 설정
# 첫 셀에서 확인한 S3 위치에 모두 들어가 있음 - 카탈로그/스키마/볼륨의 위치 말해주는것

bucket = "asac-7-dataanalysis"
key = (
    "unity-catalog/639069795658224/__unitystorage/"
    "schemas/a9e627a1-04ca-48c3-bc02-bdd59ec47f87/"
    "volumes/5ee21755-3d14-4d4c-b297-f18e4a83a4e6/latest/semas_supportcontents.xml"
)

# COMMAND ----------

qa_chain = intialize_qa_chain_from_s3(bucket, key)
ask_question(qa_chain, "청년 창업지원 내용은 어떤 게 있어?")

# COMMAND ----------

qa_chain = intialize_qa_chain_from_s3(bucket, key)
ask_question(qa_chain, "경영 부진을 해결할 수 있는 지원에는 뭐가 있습니까?")

# COMMAND ----------

qa_chain = intialize_qa_chain_from_s3(bucket, key)
ask_question(qa_chain, "한 가게를 오랫동안 운영했습니다. 지원받을 수 있는게 있을까요?")

# COMMAND ----------

qa_chain = intialize_qa_chain_from_s3(bucket, key)
ask_question(qa_chain, "지역특색을 살린 사업을 하고 싶은데 뭘 할 수 있죠?")

# COMMAND ----------

qa_chain = intialize_qa_chain_from_s3(bucket, key)
ask_question(qa_chain, "로컬크리에이터가 뭐죠?")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 질문(수정 전)

# COMMAND ----------

qa_chain = intialize_qa_chain("semas_supportcontents.xml")

ask_question(qa_chain, "해외 진출을 위한 마케팅을 지원해주는 사업을 알려주세요")

# COMMAND ----------

qa_chain = intialize_qa_chain("semas_supportcontents.xml")

ask_question(qa_chain, "폐업 준비 중인데, 재기를 위한 지원책이 있나요?")

# COMMAND ----------

qa_chain = intialize_qa_chain("semas_supportcontents.xml")

ask_question(qa_chain, "해외 진출을 위한 마케팅을 지원해주는 사업을 알려주세요")

# COMMAND ----------

qa_chain = intialize_qa_chain("semas_supportcontents.xml")

ask_question(qa_chain, "원스톱폐업지원에 마케팅 지원 항목도 있나요?")

# COMMAND ----------

qa_chain = intialize_qa_chain("semas_supportcontents.xml")

ask_question(qa_chain, "운영한지 30년 이상된 가게는 어떤 지원사업을 신청하는 것이 좋을까요?")

# COMMAND ----------

qa_chain = intialize_qa_chain("semas_supportcontents.xml")

ask_question(qa_chain, "폐업을 해야하는 상황인데, 폐업을 지원해주기도 하나요?")

# COMMAND ----------

qa_chain = intialize_qa_chain("semas_supportcontents.xml")

ask_question(qa_chain, "청년 창업지원 내용은 어떤 게 있어?")

# COMMAND ----------



# COMMAND ----------


