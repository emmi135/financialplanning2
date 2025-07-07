import requests
import json
import sseclient

BASE_URI = "https://chat.botpress.cloud"
HEADERS = {
    "accept": "application/json",
    "Content-Type": "application/json",
}

class BotpressClient:
    def __init__(self, api_id, user_key):
        self.api_id = api_id
        self.user_key = user_key
        self.base_url = f"{BASE_URI}/{self.api_id}"
        self.headers = {**HEADERS, "x-user-key": self.user_key}

    def _request(self, method, path, json_data=None):
        url = f"{self.base_url}{path}"
        try:
            resp = requests.request(method, url, headers=self.headers, json=json_data)
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as e:
            print(f"HTTP error {e.response.status_code}: {e.response.text}")
            return None

    def create_conversation(self):
        return self._request("POST", "/conversations", json_data={"body": {}})

    def list_conversations(self):
        return self._request("GET", "/conversations")

    def get_conversation(self, conversation_id):
        return self._request("GET", f"/conversations/{conversation_id}")

    def create_message(self, text, conversation_id):
        payload = {
            "payload": {"type": "text", "text": text},
            "conversationId": conversation_id,
        }
        return self._request("POST", "/messages", json_data=payload)

    def list_messages(self, conversation_id):
        return self._request("GET", f"/conversations/{conversation_id}/messages")

    def listen_conversation(self, conversation_id):
        url = f"{self.base_url}/conversations/{conversation_id}/listen"
        client = sseclient.SSEClient(url, headers=self.headers)
        for event in client:
            if event.data == "ping":
                continue
            data = json.loads(event.data)["data"]
            yield {"id": data["id"], "text": data["payload"]["text"]}
