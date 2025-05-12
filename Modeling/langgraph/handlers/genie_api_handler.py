#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests
import time

class GenieAPIHandler:
    def __init__(self, workspace, token, space_id):
        self.workspace = workspace
        self.token = token
        self.space_id = space_id
        self.headers = {'Authorization': f'Bearer {self.token}'}

    def _run_api(self, method, url, data_json=None):
        response = requests.request(method=method, headers=self.headers, url=url, json=data_json)
        if response.status_code != 200:
            raise Exception(f'Request failed: {response.status_code}, {response.text}')
        return response.json()

    def ask(self, question: str) -> dict:
        # 1. 대화 시작 (POST)
        url = f'https://{self.workspace}/api/2.0/genie/spaces/{self.space_id}/start-conversation'
        start_payload = {"content": question}
        result = self._run_api('POST', url, start_payload)
    
        conversation_id = result['conversation_id']
        message_id = result['message_id']

        time.sleep(12)
        
        # 2. SQL 메시지 조회 (GET → 절대 body 없음)
        url = f'https://{self.workspace}/api/2.0/genie/spaces/{self.space_id}/conversations/{conversation_id}/messages/{message_id}'
        result = self._run_api('GET', url)
    
        if "attachments" not in result or not result["attachments"]:
            raise ValueError(
                f"[Genie API] SQL 생성 실패. attachments 누락. 질문: '{question}'"
            )
    
        attachment = result["attachments"][0]
        attachment_id = attachment["attachment_id"]
        query_description = attachment["query"]["description"]
    
        # 3. 쿼리 결과 조회 (GET → 역시 body 없음)
        url = f'https://{self.workspace}/api/2.0/genie/spaces/{self.space_id}/conversations/{conversation_id}/messages/{message_id}/query-result/{attachment_id}'
        result = self._run_api('GET', url)
    
        return {
            "query_description": query_description,
            "data": result
        }



# In[ ]:




