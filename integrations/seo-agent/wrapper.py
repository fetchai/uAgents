import os
from dotenv import load_dotenv, find_dotenv
from typing import Dict, List

from langchain_core.tools import tool
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI, OpenAI
from langchain.output_parsers import CommaSeparatedListOutputParser
from langchain.prompts import PromptTemplate
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
	# TODO include cleaned-up html to 
	bs_transformer = BeautifulSoupTransformer()
	docs_transformed = bs_transformer.transform_documents(html, tags_to_extract=["body"])

	return docs_transformed[0].page_content

# @tool 
def extractKeywords(text: str):
	"""
	Extracts keywords from the provided text using a language model asynchronously.
	"""
	parser = CommaSeparatedListOutputParser()
	# Define the prompt to guide the LLM for keyword extraction
	prompt_string = f"Given the following text extracted from a web page, identify and list the three most relevant keywords the present them as a Python list. Return the keywords as a comma separated list.:\n\n{text}"
	format_instructions = parser.get_format_instructions()
	prompt = PromptTemplate(
		template="{subject}.\n{format_instructions}",
		input_variables=["subject"],
		partial_variables={"format_instructions": format_instructions},
	)

	# Use the LLM to generate a response based on the prompt
	llm = OpenAI()
	chain = prompt | llm | parser
	response = chain.invoke({"subject": prompt_string})
	# response = llm.generate(prompt, max_tokens=100)
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
	
	subject_page = crawlPage(url)
	subject_keywords = extractKeywords(subject_page)
	# top_pages = getSERP()

	print(subject_keywords)

if __name__ == "__main__":
	startProcess("https://fetch.ai")