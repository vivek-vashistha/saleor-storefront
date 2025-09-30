# app.py (minimal runner)
from deepagents_commerce.agent import agent

thread_cfg = {"configurable": {"thread_id": "u123"}}  # per-user thread

dialog = [
  {"role": "user", "content": "I'm looking for a regime which can help me in maintaining overall physical and mental health"},
  {"role": "assistant", "content": ""},  # agent will fill this in
]

# Stream for tool/useful progress messages if you like:
for event in agent.stream({"messages": dialog}, config=thread_cfg):
    print(event)

# Or single-shot:
result = agent.invoke({"messages": dialog}, config=thread_cfg)
payload = result.get("response")  # emit_recommendations payload when emitted
files = result.get("files", {})   # any files the agent chose to create
