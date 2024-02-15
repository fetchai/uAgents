# Langchain RAG integration

Langchain RAG integration example offers a guide to setting up and using RAG (retrieval augmented generation) technology in a uagent. This example shows how to create a RAG application that can answer question based on a document.

- Python (v3.10+ recommended)
- Poetry (A Python packaging and dependency management tool)

## Setup

1. For the demo to work, you need to get some API keys:

    - Visit the [Cohere website](https://dashboard.cohere.com/).
    - Sign up or log in.
    - Navigate to `API Keys`.
    - Copy an existing key or create a new one.

    - Visit the [OpenAI website](https://openai.com/).
    - Sign up or log in.
    - Navigate to the API section to obtain your API key.

    Note that if you’ve run out of OpenAI credits, you will not be able to get results for this example.

2. In the `langchain-rag/src` directory, create a `.env` file and set your API keys:

    ```
    export COHERE_API_KEY="{GET THE API KEY}"
    export OPENAI_API_KEY="{GET THE API KEY}"
    export LANGCHAIN_RAG_SEED="{GET THE API KEY}"
    ```

3. In the `langchain-rag` directory install all dependencies

    ```bash
    poetry install
    ```

3. To load the environment variables from `.env:

    ```bash
    cd src
    source .env
    ```

## Running The Main Script

To run the project, use the command:

```
poetry run python main.py
```


After running the command, a request is sent to the agent in every minute. The results can be seen in the console. Look for the following output in the logs:

```
Adding RAG agent to Bureau: {agent_address}
```

Copy the {agent_address} value and replace RAG_AGENT_ADDRESS with this value in src/langchain_rag_user.py.

In the src/langchain_rag_user.py file, there are variables QUESTION, URL, DEEP_READ. Change the value of these variables to customize the question you want to get answered. Default values are:

```
QUESTION = "How to install uagents using pip"
URL = "https://fetch.ai/docs/guides/agents/installing-uagent"
DEEP_READ = "no"  # it means nested pages at the URL won't be parsed, just the actual URL
```

Now you can enjoy answering questions with Langchan RAG agent!