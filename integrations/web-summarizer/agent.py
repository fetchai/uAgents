from langchain.chains.summarize import load_summarize_chain
from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import ChatOpenAI
from uagents import Agent, Context, Protocol, Model
from pydantic import Field
from ai_engine import UAgentResponse, UAgentResponseType


class WebsiteLink(Model):
    link: str = Field(description="Give the link you want to retrieve information from")


SEED_PHRASE = "website agent seed phrase"
AGENT_MAILBOX_KEY = "YOUR_MAILBOX_KEY"

OPENAI_API_KEY = "YOUR_OPEN_API_KEY"

summaryAgent = Agent(
    name="SummaryAgent",
    seed=SEED_PHRASE,
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)

summary_protocol = Protocol("Website Link Summarizer")

print(summaryAgent.address)


@summary_protocol.on_message(model=WebsiteLink, replies={UAgentResponse})
async def summarize_news(ctx: Context, sender: str, msg: WebsiteLink):

    loader = WebBaseLoader(msg.link)
    docs = loader.load()
    llm = ChatOpenAI(
        temperature=0, model_name="gpt-3.5-turbo-1106", api_key=OPENAI_API_KEY
    )
    chain = load_summarize_chain(llm, chain_type="stuff")

    result = chain.invoke(docs)

    await ctx.send(
        sender,
        UAgentResponse(message=(result["output_text"]), type=UAgentResponseType.FINAL),
    )


summaryAgent.include(summary_protocol, publish_manifest=True)
summaryAgent.run()
