#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import boto3
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.prompts import PromptTemplate
import os

class LocalRAGHandler:
    def __init__(self, bucket: str, key: str):
        self.qa_chain = self._initialize_chain(bucket, key)

    def _load_documents(self, bucket, key):
        s3 = boto3.client('s3')
        obj = s3.get_object(Bucket=bucket, Key=key)
        xml_bytes = obj['Body'].read()
        root = ET.fromstring(xml_bytes)

        results = []
        for category in root.findall("Category"):
            for sub in category.findall(".//Item"):
                title = sub.findtext("Title")
                url = sub.findtext("URL")
                content = sub.findtext("Content") or ""
                soup = BeautifulSoup(content, "lxml")
                for dl in soup.find_all("dl"):
                    dt, dd = dl.find("dt"), dl.find("dd")
                    if dt and dd:
                        results.append({
                            "title": title,
                            "url": url,
                            "구분": dt.get_text(strip=True),
                            "내용": dd.get_text(separator="\n", strip=True)
                        })

        texts, metadatas = [], []
        for r in results:
            if r["구분"] not in ["문의처", "설문", "만족도"]:
                texts.append(f"{r['구분']}: {r['내용']}")
                metadatas.append({"title": r["title"], "source": r["url"]})

        return texts, metadatas

    def _initialize_chain(self, bucket, key):
        texts, metadatas = self._load_documents(bucket, key)
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
        retriever = MultiQueryRetriever.from_llm(retriever=vectorstore.as_retriever(), llm=llm)

        return RetrievalQAWithSourcesChain.from_chain_type(
            retriever=retriever,
            chain_type="stuff",
            chain_type_kwargs={"prompt": prompt_template},
            llm=llm
        )

    def ask(self, question: str):
        response = self.qa_chain.invoke({"question": question})
        return response["answer"], response.get("sources")

