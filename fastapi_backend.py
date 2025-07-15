from fastapi import FastAPI
from pydantic import BaseModel
from agent_logic import run_budget_agent
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

class Query(BaseModel):
    query: str

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

@app.post("/agent_api")
def handle_query(q: Query):
    return {"reply": run_budget_agent(q.query)}
