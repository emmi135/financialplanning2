import requests
import json
import sseclient

BASE_URI = "https://chat.botpress.cloud"
HEADERS = {"accept": "application/json", "Content-Type": "application/json"}

class BotpressClient:
    def __init__(self, api_id, user_key):
        self.api_id = api_id
        self.user_key = user_key
        self.base_url = f"{BASE_URI}/{self.api_id}"
        self.headers = {**HEADERS, "x-user-key": self.user_key}

    def _request(self, method, path, json_data=None):
        url = f"{self.base_url}/{path}"
        response = requests.request(method, url, headers=self.headers, json=json_data)
        return response.json()

    def create_conversation(self):
        return self._request("POST", "conversations")

    def create_message(self, text, conversation_id):
        return self._request("POST", f"conversations/{conversation_id}/messages", {"type": "text", "text": text})

    def list_messages(self, conversation_id):
        return self._request("GET", f"conversations/{conversation_id}/messages")

    def listen_conversation(self, conversation_id):
        url = f"{self.base_url}/conversations/{conversation_id}/events"
        headers = self.headers
        response = requests.get(url, headers=headers, stream=True)
        client = sseclient.SSEClient(response)
        for event in client.events():
            if event.data:
                payload = json.loads(event.data)
                if "payload" in payload and "text" in payload["payload"]:
                    yield payload["payload"]["text"]