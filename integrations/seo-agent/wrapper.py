import os
from dotenv import load_dotenv, find_dotenv
from typing import Dict, List

from langchain_core.tools import tool
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI, OpenAI
from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_transformers import BeautifulSoupTransformer

load_dotenv(find_dotenv())
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AGENT_MAILBOX_KEY = os.getenv("MAILBOX_API_KEY")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")

@tool
def getSERP(keywords: List[str], count: int = 4) -> List[str]:
	"""Retrieves the first 'count' entries of a SERP for the given keywords"""
	# use google serper
	result = []
	return result

@tool
def crawlPage(url: str) -> str:
	"""Returns the content of a website"""
	loader = AsyncChromiumLoader([url])
	html = loader.load()

	# return html
	bs_transformer = BeautifulSoupTransformer()
	docs_transformed = bs_transformer.transform_documents(html, tags_to_extract=["body"])

	return docs_transformed[0].page_content[0:500]

# @tool 
def extractKeywords(text: str):
	"""
	Extracts keywords from the provided text using a language model asynchronously.
	"""
	# Define the prompt to guide the LLM for keyword extraction
	prompt = [f"Given the following text extracted from a web page, identify and list the most relevant keywords that summarize the core topics and themes. Focus on extracting key phrases, important terms, and entities that capture the essence of the text.:\n\n{text}"]

	# Use the LLM to generate a response based on the prompt
	llm = OpenAI()
	response = llm.generate(prompt, max_tokens=100)
	# Assuming the response is a string of keywords, possibly comma-separated or as a simple list
	# You might need to adjust parsing based on the actual format of your LLM's response
	return response

tools = [getSERP, crawlPage, extractKeywords]

def startProcess(url: str):
	# Get the prompt to use - you can modify this!
	# prompt = hub.pull("hwchase17/openai-tools-agent")
	# # prompt.ins

	# model = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0)

	# # Construct the OpenAI Tools agent
	# agent = create_openai_tools_agent(model, tools, prompt)
	# # Create an agent executor by passing in the agent and tools
	# agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
	
	result = crawlPage(url)
	result = extractKeywords(result)

	print(result)

if __name__ == "__main__":
	startProcess("https://fetch.ai")