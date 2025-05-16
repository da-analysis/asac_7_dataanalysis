import os
import requests
from dotenv import load_dotenv

load_dotenv()

class GenieSALESHandler:
    def __init__(self, workspace, token, space_id):
        self.workspace = workspace
        self.token = token
        self.space_id = space_id
        self.headers = {'Authorization': f'Bearer {self.token}'}

    def _run_api(self, url, method='GET', data_json=None):
        response = requests.request(method=method, url=url, headers=self.headers, json=data_json)
        if response.status_code != 200:
            raise Exception(f"Request failed: {response.status_code}, {response.text}")
        return response.json()

    def start_conversation(self, question):
        url = f"https://{self.workspace}/api/2.0/genie/spaces/{self.space_id}/start-conversation"
        return self._run_api(url, method='POST', data_json={"content": question})

    def ask_followup(self, conversation_id, question):
        url = f"https://{self.workspace}/api/2.0/genie/spaces/{self.space_id}/conversations/{conversation_id}/messages"
        return self._run_api(url, method='POST', data_json={"content": question})

    def get_query_info(self, conversation_id, message_id):
        url = f"https://{self.workspace}/api/2.0/genie/spaces/{self.space_id}/conversations/{conversation_id}/messages/{message_id}"
        return self._run_api(url)

    def get_query_result(self, conversation_id, message_id, attachment_id):
        url = f"https://{self.workspace}/api/2.0/genie/spaces/{self.space_id}/conversations/{conversation_id}/messages/{message_id}/query-result/{attachment_id}"
        return self._run_api(url)


def genie_chat_sales(question: str, genie_api: GenieSALESHandler):
    try:
        if "genie_sales_conversation_id" not in st.session_state:
            result = genie_api.start_conversation(question)
            st.session_state["genie_sales_conversation_id"] = result["conversation_id"]
        else:
            result = genie_api.ask_followup(st.session_state["genie_sales_conversation_id"], question)

        conversation_id = result["conversation_id"]
        message_id = result["message_id"]

        for _ in range(15):
            time.sleep(2)
            message = genie_api.get_query_info(conversation_id, message_id)
            attachments = message.get("attachments", [])
            state = message.get("status", "")
            if state in ("SUCCEEDED", "COMPLETED") and attachments:
                break
        else:
            return "❗쿼리 결과를 가져오는 데 실패했습니다."

        attachment = attachments[0]
        attachment_id = attachment["attachment_id"]
        description = attachment["query"].get("description", "(설명 없음)")

        result = genie_api.get_query_result(conversation_id, message_id, attachment_id)
        data_array = result.get("statement_response", {}).get("result", {}).get("data_array", [])
        columns_schema = result.get("statement_response", {}).get("manifest", {}).get("schema", {}).get("columns", [])
        column_names = [col.get("name", f"col{i}") for i, col in enumerate(columns_schema)]

        if data_array and column_names:
            df = pd.DataFrame(data_array, columns=column_names)
            return {"description": description, "dataframe": df}
        else:
            return "❗데이터가 없습니다."

    except Exception as e:
        return f"❗오류 발생: {str(e)}"
