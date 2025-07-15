# fastapi_backend.py
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from agent_logic import run_budget_agent

app = FastAPI()

class Query(BaseModel):
    query: str

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/agent_api")
def handle_voice_input(query: Query):
    user_input = query.query
    reply = run_budget_agent(user_input)
    return {"reply": reply}
