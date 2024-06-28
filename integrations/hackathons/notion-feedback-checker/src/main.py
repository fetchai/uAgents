from uagents import Bureau
from agents.notion_rag_agent import agent
from agents.notion_rag_user import notion_rag_user as user


if __name__ == "__main__":
    bureau = Bureau(endpoint="http://127.0.0.1:8000/submit", port=8000)
    print(f"Adding Notion RAG agent to Bureau: {agent.address}")
    bureau.add(agent)
    print(f"Adding user agent to Bureau: {user.address}")
    bureau.add(user)
    bureau.run()
