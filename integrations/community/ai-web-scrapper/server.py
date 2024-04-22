import json
from flask import Flask, request, jsonify
from uagents import Model
from flask_cors import CORS
from pydantic import Field
from utils import AgentProtocolAdapter, AgentAdapterError
import os
from langchain.chains.summarize import load_summarize_chain
from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import ChatOpenAI

HOSTED_BASE_URL = ""
OPEN_API_KEY = ""

class Document:
    def __init__(self, page_content):
        self.page_content = page_content

    def to_dict(self):
        return {"page_content": self.page_content}

def scrape_and_summarize(url, openai_api_key=None):
    # Step 1: Initialize WebBaseLoader with the given URL
    loader = WebBaseLoader(url)
    
    # Step 2: Load the document
    docs = loader.load()
    
    # Step 3: Load summarization chain
    if openai_api_key is None:
        # Attempt to get the API key from environment variable
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key is None:
            raise ValueError("OpenAI API key not found. Please set the environment variable OPENAI_API_KEY.")
    
    llm = ChatOpenAI(openai_api_key=openai_api_key, temperature=0, model_name="gpt-3.5-turbo-1106")
    chain = load_summarize_chain(llm, chain_type="stuff")
    
    # Step 4: Run the summarization chain on the loaded document
    summarized_content = chain.invoke(docs)
    summarized = summarized_content["input_documents"][0].to_json()
    
    # Step 5: Define the needed dependencies
    dependencies = {
        "langchain": ">=1.0.0",
        "langchain_community": ">=1.0.0",
        "langchain_openai": ">=1.0.0"
    }
    
    # Step 6: Return the summarized content and dependencies
    return summarized, dependencies

class Summarizer(Model):
    """
    Describes the input payload.
    """
    url: str = Field(description="This field describes the url which will provided by the user")
    question: str = Field(description="This field describes the question which will also provided by the user")
agent_adapter = AgentProtocolAdapter(endpoint=f'{HOSTED_BASE_URL}/callback')

app = Flask(__name__)
CORS(app)



@app.route("/get-summarization", methods=["POST"])
async def get_summarization():
    try:
        json_data = request.json
        if "url" not in json_data:
            raise ValueError("URL not provided in request")
        summarized_content, _ = scrape_and_summarize(json_data["url"], os.getenv("OPENAI_API_KEY"))
        content = summarized_content.get("page_content")
        if not content:
            raise ValueError("Failed to retrieve summarized content")
        return jsonify({"content": content, "message": "Data Scraped Successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/ques-ans", methods=["POST"])
async def answer_question():
    try:
        json_data = request.json
        if "url" not in json_data or "question" not in json_data:
            raise ValueError("URL or question not provided in request")
        res = await agent_adapter.send_message("agent1q0l9wzgf4m453508wlyzlzhx72gvm0r3zpnmvx03q02a2evll38njsvq525", Summarizer(url=json_data["url"], question=json_data["question"]))
        json_response = json.loads(res)
        return jsonify(json_response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/callback', methods=['POST'])
def agent_callback():
    """
    This endpoint is called by external agents when it receives a message.
    """
    print(request.get_json())
    try:
        agent_adapter.process_response(request.get_json())
    except AgentAdapterError as e:
        return {}

    return {}

if __name__ == "__main__":
    app.run(debug=True, port=8000)