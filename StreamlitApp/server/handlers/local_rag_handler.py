import os
import boto3
import fitz  # PyMuPDF
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from tiktoken import get_encoding
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

class LocalRAGHandler:
    def __init__(self, bucket: str, key: str, pdf_prefix: str = None, faiss_dir="faiss_index"):
        self.bucket = bucket
        self.key = key
        self.pdf_prefix = os.getenv("BUCKET_PREFIX_PDF")
        self.faiss_dir = faiss_dir
        self.qa_chain = self._initialize_chain()

    def _load_documents(self):
        s3 = boto3.client('s3')
        obj = s3.get_object(Bucket=self.bucket, Key=self.key)
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

    def _load_pdfs(self):
        if not self.pdf_prefix:
            return [], []

        s3 = boto3.client("s3")
        paginator = s3.get_paginator("list_objects_v2")
        operation_parameters = {"Bucket": self.bucket, "Prefix": self.pdf_prefix}

        pdf_texts, metadatas = [], []

        for page in paginator.paginate(**operation_parameters):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if key.endswith(".pdf"):
                    pdf_obj = s3.get_object(Bucket=self.bucket, Key=key)
                    pdf_bytes = pdf_obj["Body"].read()

                    doc = fitz.open("pdf", pdf_bytes)
                    full_text = ""
                    for page in doc:
                        full_text += page.get_text()
                    doc.close()

                    pdf_texts.append(full_text)
                    metadatas.append({
                        "title": os.path.basename(key),
                        "source": f"https://{self.bucket}.s3.amazonaws.com/{key}"
                    })

        return pdf_texts, metadatas



    def split_documents_by_token_limit(self, documents, token_limit=250000):
        tokenizer = get_encoding("cl100k_base")
        batches = []
        current_batch = []
        current_tokens = 0

        for doc in documents:
            tokens = len(tokenizer.encode(doc.page_content))
            if current_tokens + tokens > token_limit:
                batches.append(current_batch)
                current_batch = [doc]
                current_tokens = tokens
            else:
                current_batch.append(doc)
                current_tokens += tokens

        if current_batch:
            batches.append(current_batch)

        return batches

    def _initialize_chain(self):
        embedding = OpenAIEmbeddings(model="text-embedding-ada-002")

        if os.path.exists(self.faiss_dir):
            vectorstore = FAISS.load_local(self.faiss_dir, embeddings=embedding, allow_dangerous_deserialization=True)
        else:
            texts_xml, metas_xml = self._load_documents()
            texts_pdf, metas_pdf = self._load_pdfs()

            texts = texts_xml + texts_pdf
            metadatas = metas_xml + metas_pdf

            splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            documents = splitter.create_documents(texts, metadatas=metadatas)
            batches = self.split_documents_by_token_limit(documents, token_limit=250000)
            vectorstore = None
            for batch_docs in batches:
                if vectorstore is None:
                    vectorstore = FAISS.from_documents(batch_docs, embedding)
                else:
                    vectorstore.add_documents(batch_docs)

            vectorstore.save_local(self.faiss_dir)

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
- 해당 사업에 대한 url을 같이 표기해주세요.
- 지원사업과 관련된 소상공인 우수사례가 있다면 같이 출력해주세요.
- 우수 사례에 대한 질문을 했을 경우에도 관련된 지원사업을 축약하여 같이 출력해주세요. 단, 이 경우 우수사례를 먼저 출력한 뒤에 관련된 사업을 설명해주세요.
- 우수 사례를 표기할 때는 반드시 출처를 표기해주셔야 합니다. 

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

        return answer, response.get("sources")
