# AI Web Scraper and Summarizer

This project implements a web scraper and summarizer API integrated with a question answering system. It utilizes Flask for creating the API endpoints and integrates with langchain for web scraping, summarization, and for question answering tasks it utilizes the Hugging Face model.

## Functionality

The project consists of the following main components:

1. **Web Scraper and Summarizer**: A functionality to scrape content from a given URL and summarize it using langchain and langchain-openai libraries. This is exposed through the `/get-summarization` endpoint.

2. **Question Answering System**: An endpoint `/ques-ans` to answer questions related to the summarized content. It utilizes the Hugging Face model `deepset/roberta-base-squad2` for question answering.

3. **Agent Protocol Adapter**: An adapter (`AgentProtocolAdapter`) to facilitate communication with external agents via protocols. This is used for sending and receiving messages related to summarization and question answering.

# Getting OpenAI API Key

To access the OpenAI API, you need an API key. Follow these steps to obtain your API key:

1. Visit the OpenAI website at [https://platform.openai.com/](https://platform.openai.com/).
2. Sign up or log in to your account.
3. Navigate to the View API Keys under Profile section.
4. Create a new secret key.
5. Copy the generated API key.
6. Replace the placeholder in the script with your actual API key.

Ensure that you keep your API key secure and do not share it publicly. It is a sensitive credential that grants access to Rainforest services.

# Hugging Face Token

1. Visit the Hugging Face website: [https://huggingface.co/](https://huggingface.co/)
2. Sign in to your Hugging Face account or create a new one.
3. Navigate to your profile settings.
4. Find or generate your API token. If you don't have one, there is usually an option to create a new token.
5. Copy the generated token; this will be your Hugging Face Token.

# Agent Secrets on Agentverse

1. Go to the Agentverse platform.
2. Navigate to the Agent Secrets section.
3. Create an agent and copy the code in it
4. Add a new secrets with the keys for `HOSTED_BASE_URL` and `HUGGING_FACE_TOKEN` and the values


## Usage

1. **Installation**: First, install the required dependencies using the provided `requirements.txt` file:

   ```bash
   pip install -r requirements.txt
2. **Run**: Run the application:

    ```bash
   python server.py

