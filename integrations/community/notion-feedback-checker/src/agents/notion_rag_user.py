import os
from uagents import Agent, Context, Protocol
from messages.requests import NotionRequest
from ai_engine import UAgentResponse
from agents.notion_rag_agent import agent as rag_agent


FEEDBACK_TITLE = "Test feedback"

NOTION_RAG_AGENT_ADDRESS = rag_agent.address

NOTION_USER_SEED = os.getenv("NOTION_RAG_SEED", "")
assert NOTION_USER_SEED, "NOTION_USER_SEED environment variable is missing from .env"

notion_rag_user = Agent(
    name=NOTION_USER_SEED,
    port=8000,
    endpoint=["http://127.0.0.1:8000/submit"],
)

notion_rag_user_protocol = Protocol("LangChain RAG user")


@notion_rag_user_protocol.on_interval(60, messages=NotionRequest)
async def ask_question(ctx: Context):
    ctx.logger.info(
        f"Asking Notion RAG agent to check if a feedback with title similar to {FEEDBACK_TITLE} has already been saved in Notion Feedbacks"
    )
    await ctx.send(
        NOTION_RAG_AGENT_ADDRESS, NotionRequest(feedback_title=FEEDBACK_TITLE)
    )


@notion_rag_user_protocol.on_message(model=UAgentResponse)
async def handle_data(ctx: Context, sender: str, data: UAgentResponse):
    ctx.logger.info(f"Got response from Notion RAG agent: {data.message}")


notion_rag_user.include(notion_rag_user_protocol)

if __name__ == "__main__":
    notion_rag_user.run()
