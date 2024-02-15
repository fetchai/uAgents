from uagents import Agent, Context, Protocol
from messages.requests import RagRequest
from ai_engine import UAgentResponse


QUESTION = "How to install uagents using pip"
URL = "https://fetch.ai/docs/guides/agents/installing-uagent"
DEEP_READ = (
    "no"  # it means nested pages at the URL won't be parsed, just the actual URL
)

RAG_AGENT_ADDRESS = "agent1q0yu4450vryngsxv6un8t5x8hwrprkznay2f49a5y4384jn0tgxj62jf3h8"

user = Agent(
    name="langchain_rag_user",
    port=8000,
    endpoint=["http://127.0.0.1:8000/submit"],
)

rag_user = Protocol("LangChain RAG user")


@rag_user.on_interval(60, messages=RagRequest)
async def ask_question(ctx: Context):
    ctx.logger.info(
        f"Asking RAG agent to answer {QUESTION} based on document located at {URL}, readin nested pages too: {DEEP_READ}"
    )
    await ctx.send(
        RAG_AGENT_ADDRESS, RagRequest(question=QUESTION, url=URL, deep_read=DEEP_READ)
    )


@rag_user.on_message(model=UAgentResponse)
async def handle_data(ctx: Context, sender: str, data: UAgentResponse):
    ctx.logger.info(f"Got response from RAG agent: {data.message}")


user.include(rag_user)

if __name__ == "__main__":
    rag_user.run()
