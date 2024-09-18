import os
import sys

from langchain_core.documents import Document
from dotenv import load_dotenv, find_dotenv
from typing import List

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
    if "items" in result:
        for item in result["items"]:
            top_webpages.append(item["link"])
    return top_webpages


# @tool
def crawlPage(url: str) -> Document:
    """Returns the content of a website"""
    loader = AsyncChromiumLoader([url])
    html = loader.load()

    # return html
    bs_transformer = BeautifulSoupTransformer()
    docs_transformed = bs_transformer.transform_documents(
        html, tags_to_extract=["body"]
    )

    return docs_transformed[0]


# @tool
def extractKeywords(text: str, url: str):
    """
    Extracts keywords from the provided text using a language model asynchronously.
    """
    parser = CommaSeparatedListOutputParser()
    # Define the prompt to guide the LLM for keyword extraction
    prompt_string = f"Given the following text extracted from {url}, identify and list the three most relevant keywords the present them as a Python list. Exclude brandname, the page title or parts from the url from the keywords. Return the keywords as a comma separated list.:\n\n{text}"
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

    return response


def compare_websites_for_keywords(
    superior_page: Document, inferior_page: Document, keywords: List[str]
) -> str:
    """
    Compares 2 websites based on keywords and return a assessment why one is better ranked than the other
    """

    prompt = f"""
	You are a SEO expert agent advising website owners how to improve their content. 
	For this you will compare a superior ranked website 'SUPERIOR' ({superior_page.metadata['source']}) 
	with the website to be evaluated 'ORIGINAL' ({inferior_page.metadata['source']})
	and summarize why the superior website ranks better for the given 'KEYWORDS'.
	Refer to SUPERIOR and ORIGINAL by their urls or page titles.
	You can include 1 or 2 concrete examples of what superior is doing better, or inferior is not doing good.\n
	# SUPERIOR\n{superior_page.page_content[:8000]}\n 
	# ORIGINAL\n{inferior_page.page_content[:8000]}\n 
	# KEYWORDS\n{keywords}\n
	"""
    llm = ChatOpenAI(model="gpt-3.5-turbo")
    # Use the LLM to generate the comparison
    comparison_result = llm.invoke(prompt)
    print(comparison_result)
    return comparison_result.content


# tools = [getSERP, crawlPage, extractKeywords]


def startProcess(url: str):
    # prompt = hub.pull("hwchase17/openai-tools-agent")
    # model = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0)
    # agent = create_openai_tools_agent(model, tools, prompt)
    # agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    print(f"crawling page: {url}")
    subject_page = crawlPage(url)
    print(f"content length: {len(subject_page.page_content)}")
    subject_keywords = extractKeywords(subject_page.page_content, url)
    print(f"found keywords: {subject_keywords}")
    top_pages = getSERP(subject_keywords)
    top_1 = crawlPage(top_pages[0])
    result = compare_websites_for_keywords(top_1, subject_page, subject_keywords)

    # print(result)
    return result


if __name__ == "__main__":
    startProcess(sys.argv[1])
