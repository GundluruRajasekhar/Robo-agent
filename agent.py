"""Agent loop: think -> call tool -> observe -> repeat until done or step limit."""
import os
from anthropic import Anthropic
from tools import TOOLS, run_tool

client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment
MODEL = os.getenv("AGENT_MODEL", "claude-sonnet-5")
MAX_STEPS = int(os.getenv("MAX_STEPS", "8"))

SYSTEM = (
    "You are Robo, a general-purpose task agent. Break the user's goal into steps, "
    "use tools when they help, and check every tool result. If a tool returns an error, "
    "change your approach instead of repeating it. Say plainly when a task is beyond your tools. "
    "Finish with a short answer that says what you did."
)


def run_agent(goal: str) -> dict:
    messages = [{"role": "user", "content": goal}]
    trace = []
    tool_schemas = [t["schema"] for t in TOOLS.values()]
    for step in range(1, MAX_STEPS + 1):
        resp = client.messages.create(
            model=MODEL, max_tokens=1500, system=SYSTEM, tools=tool_schemas, messages=messages
        )
        messages.append({"role": "assistant", "content": resp.content})
        thought = "".join(b.text for b in resp.content if b.type == "text")
        if resp.stop_reason != "tool_use":
            return {"answer": thought, "steps": trace}
        results = []
        for b in resp.content:
            if b.type == "tool_use":
                out = run_tool(b.name, b.input)
                trace.append({"step": step, "thought": thought, "tool": b.name,
                              "input": b.input, "observation": out[:500]})
                results.append({"type": "tool_result", "tool_use_id": b.id, "content": out})
        messages.append({"role": "user", "content": results})
    return {"answer": "Stopped: step limit reached.", "steps": trace}


if __name__ == "__main__":
    import json, sys
    print(json.dumps(run_agent(" ".join(sys.argv[1:]) or "What is 17 * 23?"), indent=2))
