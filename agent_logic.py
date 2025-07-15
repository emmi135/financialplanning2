# agent_logic.py
import requests

def run_budget_agent(user_input: str) -> str:
    # Your actual LLM logic here
    # This version uses OpenRouter (DeepSeek) — adjust as needed
    headers = {
        "Authorization": "Bearer YOUR_OPENROUTER_API_KEY",
    }
    data = {
        "model": "deepseek/deepseek-chat",
        "messages": [
            {"role": "user", "content": user_input}
        ]
    }
    res = requests.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers)
    reply = res.json()["choices"][0]["message"]["content"]
    return reply
