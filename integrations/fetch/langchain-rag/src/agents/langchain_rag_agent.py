import traceback
from uagents import Agent, Context, Protocol
import validators
from messages.requests import RagRequest
import os
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_community.document_loaders import UnstructuredURLLoader
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CohereRerank
from ai_engine import UAgentResponse, UAgentResponseType
import nltk

nltk.download("punkt")
nltk.download("averaged_perceptron_tagger")


LANGCHAIN_RAG_SEED = os.getenv("LANGCHAIN_RAG_SEED", "")
assert (
    LANGCHAIN_RAG_SEED
), "LANGCHAIN_RAG_SEED environment variable is missing from .env"

agent = Agent(
    name="langchain_rag_agent",
    seed=LANGCHAIN_RAG_SEED,
    port=8001,
    endpoint=["http://127.0.0.1:8001/submit"],
)

docs_bot_protocol = Protocol("DocsBot")


PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""


def create_retriever(
    ctx: Context, url: str, deep_read: bool
) -> ContextualCompressionRetriever:
    def scrape(site: str):
        if not validators.url(site):
            ctx.logger.info(f"Url {site} is not valid")
            return

        r = requests.get(site)
        soup = BeautifulSoup(r.text, "html.parser")

        parsed_url = urlparse(url)
        base_domain = parsed_url.scheme + "://" + parsed_url.netloc

        link_array = soup.find_all("a")
        for link in link_array:
            href: str = link.get("href", "")
            if len(href) == 0:
                continue
            current_site = f"{base_domain}{href}" if href.startswith("/") else href
            if (
                ".php" in current_site
                or "#" in current_site
                or not current_site.startswith(url)
                or current_site in urls
            ):
                continue
            urls.append(current_site)
            scrape(current_site)

    urls = [url]
    if deep_read:
        scrape(url)
        ctx.logger.info(f"After deep scraping - urls to parse: {urls}")

    try:
        loader = UnstructuredURLLoader(urls=urls)
        docs = loader.load_and_split()
        db = FAISS.from_documents(docs, OpenAIEmbeddings())
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=CohereRerank(), base_retriever=db.as_retriever()
        )
        return compression_retriever
    except Exception as exc:
        ctx.logger.error(f"Error happened: {exc}")
        traceback.format_exception(exc)


@docs_bot_protocol.on_message(model=RagRequest, replies={UAgentResponse})
async def answer_question(ctx: Context, sender: str, msg: RagRequest):
    ctx.logger.info(f"Received message from {sender}, session: {ctx.session}")
    ctx.logger.info(
        f"input url: {msg.url}, question: {msg.question}, is deep scraping: {msg.deep_read}"
    )

    parsed_url = urlparse(msg.url)
    if not parsed_url.scheme or not parsed_url.netloc:
        ctx.logger.error("invalid input url")
        await ctx.send(
            sender,
            UAgentResponse(
                message="Input url is not valid",
                type=UAgentResponseType.FINAL,
            ),
        )
        return
    base_domain = parsed_url.scheme + "://" + parsed_url.netloc
    ctx.logger.info(f"Base domain: {base_domain}")

    retriever = create_retriever(ctx, url=msg.url, deep_read=msg.deep_read == "yes")

    compressed_docs = retriever.get_relevant_documents(msg.question)
    context_text = "\n\n---\n\n".join([doc.page_content for doc in compressed_docs])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=msg.question)

    model = ChatOpenAI(model="gpt-3.5-turbo-1106")
    response = model.predict(prompt)
    ctx.logger.info(f"Response: {response}")
    await ctx.send(
        sender, UAgentResponse(message=response, type=UAgentResponseType.FINAL)
    )


agent.include(docs_bot_protocol, publish_manifest=True)


if __name__ == "__main__":
    agent.run()
