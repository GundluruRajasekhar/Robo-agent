# Robo: a Python agent (LLM + tools)

Loop: goal -> LLM decides -> tool call -> observation -> repeat -> answer.

## Run locally
```
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...        # Windows: set ANTHROPIC_API_KEY=...
python agent.py "Write a file hello.txt saying hi, then read it back"
```

## Run as an API
```
export APP_TOKEN=some-long-secret
uvicorn server:app --reload
curl -X POST localhost:8000/run -H "X-Token: some-long-secret" -H "Content-Type: application/json" -d '{"goal":"What is 17*23?"}'
```

## Deploy (Render, free tier)
1. Push this folder to a GitHub repo.
2. On render.com: New > Blueprint > pick the repo (uses render.yaml).
3. Set ANTHROPIC_API_KEY and APP_TOKEN when prompted.
4. Your link will look like https://robo-agent.onrender.com (interactive docs at /docs).

## Add abilities
Add a function + schema to `tools.py` (email, calendar, database, search...). The agent uses it automatically.
