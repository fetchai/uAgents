import os
from typing import List

from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_transformers import BeautifulSoupTransformer

os.environ["DATAFORSEO_LOGIN"] = "nikolay.dimitrov@fetch.ai"
os.environ["DATAFORSEO_PASSWORD"] = "e1e9ead557069e89"

def startProcess(url: str):
    result = crawlPage(url)

    print(result)

def getSERP(keywords: List[str]):
    pass

def crawlPage(url: str):
    loader = AsyncChromiumLoader([url])
    html = loader.load()

    bs_transformer = BeautifulSoupTransformer()
    docs_transformed = bs_transformer.transform_documents(html, tags_to_extract=["span"])

    return docs_transformed[0].page_content[0:500]

if __name__ == "__main__":
    startProcess("https://fetch.ai")