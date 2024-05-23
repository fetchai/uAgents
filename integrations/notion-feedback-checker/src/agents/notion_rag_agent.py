import os
from langchain.schema.document import Document
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.prompts import ChatPromptTemplate
from ai_engine import UAgentResponse, UAgentResponseType
from notion_client import AsyncClient as AsyncNotionClient
from messages.requests import NotionRequest
from uagents import Agent, Context, Protocol


NOTION_RAG_SEED = os.getenv("NOTION_RAG_SEED", "")
assert NOTION_RAG_SEED, "NOTION_RAG_SEED environment variable is missing from .env"
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
assert NOTION_TOKEN, "NOTION_TOKEN environment variable is missing from .env"
NOTION_DB_ID = os.getenv("NOTION_DB_ID", "")
assert NOTION_DB_ID, "NOTION_DB_ID environment variable is missing from .env"
AGENT_MAILBOX_KEY = os.getenv("AGENT_MAILBOX_KEY", "")
assert AGENT_MAILBOX_KEY, "AGENT_MAILBOX_KEY environment variable is missing from .env"

agent = Agent(
    name="notion_rag_agent",
    seed=NOTION_RAG_SEED,
    port=8001,
    endpoint=["http://127.0.0.1:8001/submit"],
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)

docs_bot_protocol = Protocol("DocsBot")


PROMPT_TEMPLATE = """
Select those titles from the titles below which are most relevant for this title: {feedback_title}:

---

{context}

---

"""


@docs_bot_protocol.on_message(model=NotionRequest, replies={UAgentResponse})
async def check_feedback(ctx: Context, sender: str, msg: NotionRequest):
    ctx.logger.info(f"Received message from {sender}, session: {ctx.session}")
    ctx.logger.info(f"New feedback title: {msg.feedback_title}")

    notion = AsyncNotionClient(auth=NOTION_TOKEN)
    my_page = await notion.databases.query(
        **{
            "database_id": NOTION_DB_ID,
        }
    )
    feedback_titles = []
    for res in my_page["results"]:
        feedback_title = "".join(
            [
                text["text"]["content"]
                for text in res["properties"]["Feedback Title"]["title"]
            ]
        )
        doc = Document(page_content=feedback_title, metadata={"source": "local"})
        feedback_titles.append(doc)
    ctx.logger.info(f"All feedback titles:\n{feedback_titles}")

    db = FAISS.from_documents(feedback_titles, OpenAIEmbeddings())
    retriever = db.as_retriever()

    similar_feedbacks = retriever.get_relevant_documents(msg.feedback_title)
    ctx.logger.info(f"Similar feedbacks from vector index:\n{similar_feedbacks}")

    context_text = "\n\n---\n\n".join([doc.page_content for doc in similar_feedbacks])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(
        context=context_text, feedback_title=msg.feedback_title
    )
    ctx.logger.info(f"Prompt:\n{prompt}")

    model = ChatOpenAI(model="gpt-3.5-turbo-1106")
    response = model.predict(prompt)
    ctx.logger.info(f"Response from GPT-3.5 Turbo model:\n{response}")
    await ctx.send(
        sender, UAgentResponse(message=response, type=UAgentResponseType.FINAL)
    )


agent.include(docs_bot_protocol, publish_manifest=True)


if __name__ == "__main__":
    agent.run()
