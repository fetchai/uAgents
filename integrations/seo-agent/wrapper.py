import os
from typing import List

from langchain_core.tools import tool
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_transformers import BeautifulSoupTransformer


@tool
def getSERP(keywords: List[str], count: int = 4) -> List[str]:
    """Retrieves the first 'count' entries of a SERP for the given keywords"""
    result = []
    return result

@tool
def crawlPage(url: str) -> str:
    """Returns the content of a website"""
    loader = AsyncChromiumLoader([url])
    html = loader.load()

    return html
    # bs_transformer = BeautifulSoupTransformer()
    # docs_transformed = bs_transformer.transform_documents(html, tags_to_extract=["span"])

    # return docs_transformed[0].page_content[0:500]

@tool
def extractKeywords(text: str) -> List[str]:
    """Returns keywords of a given text (e.g., a website)"""
    result = []
    return result

tools = [getSERP, crawlPage, extractKeywords]

def startProcess(url: str):
    # Get the prompt to use - you can modify this!
    prompt = hub.pull("hwchase17/openai-tools-agent")
    model = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0)

    # Construct the OpenAI Tools agent
    agent = create_openai_tools_agent(model, tools, prompt)
    # Create an agent executor by passing in the agent and tools
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    result = crawlPage(url)

    print(result)

if __name__ == "__main__":
    startProcess("https://fetch.ai")