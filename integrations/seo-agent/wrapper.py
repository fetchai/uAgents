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
import requests


load_dotenv(find_dotenv())
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AGENT_MAILBOX_KEY = os.getenv("MAILBOX_API_KEY")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_CSE_ID = os.getenv("GOOGLE_SEARCH_CSE_ID")

# @tool
def getSERP(keywords: List[str], count: int = 4) -> List[str]:
	"""Retrieves the first 'count' entries of a SERP for the given keywords"""

	# Construct the API URL
	query = " ".join(keywords)
	url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_SEARCH_API_KEY}&cx={GOOGLE_SEARCH_CSE_ID}&num={count}"

	# Make the GET request to the Google Custom Search API
	response = requests.get(url)
	result = response.json()
	
	# Extract the top webpages from the result
	top_webpages = []
	if 'items' in result:
		for item in result['items']:
			top_webpages.append(item['link'])
	return top_webpages

# @tool
def crawlPage(url: str) -> str:
	"""Returns the content of a website"""
	loader = AsyncChromiumLoader([url])
	html = loader.load()

	# return html
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

def compare_websites_for_keywords(superior_page: str, inferior_page: str, keywords: List[str]) -> str:
	"""
	Compares 2 websites based on keywords and return a assesment why one is better ranked than the other
	"""
   
	prompt = [f"""
	You are a SEO expert agent advising website owners how to improve their content. 
	For this you will compare a superior ranked website 'SUPERIOR' with the website to be evaluated 'ORIGINAL'
	and summarize why the superior website ranks better for the given 'KEYWORDS'.\n\n
	SUPERIOR:\n\n{superior_page}\n\n ---
	ORIGINAL:\n\n{inferior_page}\n\n ---
	KEYWORDS:\n\n{keywords}\n\n
	"""]
	llm = OpenAI()
	# Use the LLM to generate the comparison
	comparison_result = llm.generate(prompt)  # Adjust max_tokens as needed
	return comparison_result

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
	top_pages = getSERP(subject_keywords)
	top_1 = crawlPage(top_pages[0])
	result = compare_websites_for_keywords(subject_page, top_1, subject_keywords)

	print(result)

if __name__ == "__main__":
	startProcess("https://fetch.ai")