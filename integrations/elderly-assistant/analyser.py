import os
import getpass
import tempfile
import zipfile

from dotenv import load_dotenv, find_dotenv
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import DirectoryLoader
from summariser import SafetySummariser
import requests


class SafetyAnalyser:
    def __init__(self, directory_url):
        load_dotenv(find_dotenv())
        self.api_key = os.environ.get("OPENAI_API_KEY") or getpass.getpass(
            "OpenAI API Key:"
        )

        with tempfile.TemporaryDirectory() as named_tempdir:
            self.directory = named_tempdir
            self.download_directory(directory_url)

            self.embeddings = OpenAIEmbeddings(api_key=self.api_key)
            self.db = Chroma(embedding_function=self.embeddings)

            self.index_directory()

            self.chat_model = ChatOpenAI(api_key=self.api_key)

            self.prompt = """
                You are an AI tasked with ensuring the safety of a vulnerable user.\n
                Your sole task is to determine whether the user is safe, based on a list of previous incidents.\n
                Here is a database of previous incidents: {DB} \n\n
                An incident has just occurred "{INCIDENT}", given this information, is the user safe?
                Provide a one word answer, safe or unsafe.
            """

    def download_directory(self, directory_url):
        """download from url pointing to zip file, extract contents to self.directory"""
        response = requests.get(directory_url)
        # follow any redirects to just download the file
        response.raise_for_status()

        with open(f"{self.directory}/temp.zip", "wb") as f:
            f.write(response.content)

        with zipfile.ZipFile(f"{self.directory}/temp.zip", "r") as zip_ref:
            zip_ref.extractall(self.directory)

    def index_directory(self):
        # we can trick the directory loader to load files from the tempdir in ram by
        text_loader = DirectoryLoader(self.directory, glob="**/*.txt")
        raw_documents = text_loader.load()

        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        documents = text_splitter.split_documents(raw_documents)
        self.db.from_documents(documents, self.embeddings)

    def retrieve_similarity(self, incident):
        docs = self.db.similarity_search(incident)

        retrieved_data = "\n\n".join(doc.page_content for doc in docs)

        return retrieved_data

    def getChain(self):
        prompt_template = PromptTemplate(
            input_variables=["DB", "INCIDENT"], template=self.prompt
        )
        return LLMChain(prompt=prompt_template, llm=self.chat_model)

    def assess_danger(self, summary):
        similarity_data = self.retrieve_similarity(summary)
        chain = self.getChain()
        input_data = {"DB": similarity_data, "INCIDENT": summary}
        return chain.run(input_data)


class SafetySystem:
    def __init__(self, summariser: SafetySummariser, analyser: SafetyAnalyser):
        self.analyser = analyser
        self.summariser = summariser

    def react_to_incident(self, incident):
        summary = self.summariser.summarise(incident)
        assessment = self.analyser.assess_danger(summary.Summary)
        return summary, assessment
