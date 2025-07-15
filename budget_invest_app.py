import streamlit as st
import openai  # or use requests for DeepSeek via OpenRouter
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI()

class Query(BaseModel):
    query: str

@app.post("/agent_api")
def handle_voice(query: Query):
    prompt = query.query
    # Call your logic here (e.g., LLM, budget planner logic, etc.)
    response = my_streamlit_agent_response(prompt)
    return {"reply": response}

def my_streamlit_agent_response(user_input):
    # This can be connected to Gemini, OpenRouter, etc.
    return f"You said: {user_input}. (Here would be the agent's full reply.)"

# CORS setup if you're calling from browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8501)
