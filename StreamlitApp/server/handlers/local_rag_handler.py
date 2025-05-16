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
            category_name = category.get("name", "")
            subcategories = category.findall("Subcategory")

            if subcategories:
                for subcat in subcategories:
                    subcategory_name = subcat.get("name", "")
                    for item in subcat.findall("Item"):
                        title = item.findtext("Title")
                        url = item.findtext("URL")
                        content = item.findtext("Content") or ""
                        soup = BeautifulSoup(content, "lxml")
                        for dl in soup.find_all("dl"):
                            dt, dd = dl.find("dt"), dl.find("dd")
                            if dt and dd:
                                results.append({
                                    "Category": category_name,
                                    "Subcategory": subcategory_name,
                                    "title": title,
                                    "url": url,
                                    "구분": dt.get_text(strip=True),
                                    "내용": dd.get_text(separator="\n", strip=True)
                                })
            else:
                for item in category.findall("Item"):
                    title = item.findtext("Title")
                    url = item.findtext("URL")
                    content = item.findtext("Content") or ""
                    soup = BeautifulSoup(content, "lxml")
                    for dl in soup.find_all("dl"):
                        dt, dd = dl.find("dt"), dl.find("dd")
                        if dt and dd:
                            results.append({
                                "Category": category_name,
                                "Subcategory": None,
                                "title": title,
                                "url": url,
                                "구분": dt.get_text(strip=True),
                                "내용": dd.get_text(separator="\n", strip=True)
                            })

        texts, metadatas = [], []
        for r in results:
            if r["구분"] not in ["문의처", "설문", "만족도"]:
                texts.append(
                    f"카테고리: {r['Category'] or '없음'}\n"
                    f"소분류: {r['Subcategory'] or '없음'}\n"
                    f"사업명: {r['title']}\n"
                    f"구분: {r['구분']}\n"
                    f"내용:\n{r['내용']}"
                )
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
당신은 소상공인 지원정책에 대한 전문 답변자입니다.

다음 문서는 여러 지원사업들에 대한 정보입니다.
각 문서는 다음과 같은 구조로 이루어져 있습니다:
- 사업명: 반드시 이 필드에 나타나는 값만 실제 사업명으로 간주하세요.
- 구분: 항목 유형 (예: 지원내용, 신청자격 등)
- 내용: 해당 항목의 실제 설명입니다.

- '내용' 중 일부 표현(예: "폐업 지원")을 사업명으로 오인하지 마세요.
- 반드시 '사업명' 필드의 값만 제목으로 사용하세요.
- 해당하는 사업의 '사업명'을 강조한 후, 상세내용을 가능한한 상세하게 설명하세요.
- 만족도 설문, 문의처 등은 제외하고 정책 내용 위주로 설명하세요.
- "장사가 안된다", "힘들다", "매출이 없다" 등의 표현은 '경영 부진'으로 해석하세요.

문서:
{summaries}

질문:
{question}

답변:
"""
        )

        llm = ChatOpenAI(model_name="gpt-4.1-mini", temperature=0)
        retriever = MultiQueryRetriever.from_llm(retriever=vectorstore.as_retriever(), llm=llm)

        return RetrievalQAWithSourcesChain.from_chain_type(
            retriever=retriever,
            chain_type="stuff",
            chain_type_kwargs={"prompt": prompt_template},
            llm=llm
        )

    def ask(self, question: str):
        response = self.qa_chain.invoke({"question": question})
        answer = response["answer"].strip()

        suffix = (
            "\n\n---\n\n"
            "ℹ️ 더 자세한 내용은 각 지원사업의 공식 홈페이지 링크를 참고해주세요.  \n"
            "🔗 [소상공인 지원사업 안내](https://www.semas.or.kr/web/main/index.kmdc)"
        )
        return answer + suffix, response.get("sources")
