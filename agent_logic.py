import os
import requests

def run_budget_agent(user_input: str) -> str:
    # Use DeepSeek or any OpenRouter model you prefer
    headers = {
        "Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY')}",
    }
    data = {
        "model": "deepseek/deepseek-chat",
        "messages": [
            {"role": "user", "content": user_input}
        ]
    }
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    return response.json()["choices"][0]["message"]["content"]
