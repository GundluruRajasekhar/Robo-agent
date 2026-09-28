"""HTTP API so the agent can be deployed. POST /run {"goal": "..."} with header X-Token."""
import os
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from agent import run_agent

app = FastAPI(title="Robo agent")
APP_TOKEN = os.getenv("APP_TOKEN", "")


class Goal(BaseModel):
    goal: str


@app.get("/")
def health():
    return {"status": "ok", "usage": "POST /run with JSON {\"goal\": \"...\"} and header X-Token"}


@app.post("/run")
def run(body: Goal, x_token: str = Header(default="")):
    if not APP_TOKEN or x_token != APP_TOKEN:  # protects your LLM bill on a public URL
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return run_agent(body.goal)
