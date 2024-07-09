# Notion Feedback Checker RAG integration

Notion Feedback Checker RAG integration example offers a guide to setting up and using RAG (retrieval augmented generation) technology in a uagent. This example shows how to create a RAG application that can search for duplicate feedback in a Notion DB.

- Python (v3.10+ recommended)
- Poetry (A Python packaging and dependency management tool)

## Setup

1. For the demo to work, you need to get some API keys:

    - Visit the [OpenAI website](https://openai.com/).
    - Sign up or log in.
    - Navigate to the API section to obtain your API key (this will be the OPENAI_API_KEY environment variable - see below).
    Note that if you’ve run out of OpenAI credits, you will not be able to get results for this example.

    - Visit the [Notion Integrations page](https://www.notion.so/my-integrations).
    - Create a new integration for the workspace where you would like to fetch data from.
    - The generated secret will be the NOTION_TOKEN environment variable - see below.

2. In the `notion-feedback-checker/src` directory, create a `.env` file and set your API keys and the agent seeds:

    ```
    export OPENAI_API_KEY="{GET THE API KEY - see above}"
    export NOTION_RAG_SEED="{random string that determines your Notion RAG agent's address}"
    export NOTION_USER_SEED="{random string that determines your user agent's address}"
    export NOTION_TOKEN="{GET THE TOKEN - see above}"
    export NOTION_DB_ID="{ID of you Feedback DB}"
    export AGENT_MAILBOX_KEY="{Mailbox key that you have to generate at https://agentverse.ai/mailroom using your Notion RAG agent's address}"
    ```

3. In the `notion-feedback-checker` directory install all dependencies

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


After running the command, a request is sent to the Notion RAG agent in every minute. The results can be seen in the console. Look for the following output in the logs:

```
Adding Notion RAG agent to Bureau: {agent_address}
```

Copy the {agent_address} value and replace NOTION_RAG_AGENT_ADDRESS with this value in src/notion_rag_user.py.

In the src/notion_rag_user.py file, there is a variable FEEDBACK_TITLE. Change the value of this variable to customize the feedback title the presence of which you would like to check in Notion feedback DB. Default value is:

```
FEEDBACK_TITLE = "Test feedback"
```

If you would like to talk to your Notion RAG agent from [DeltaV](https://deltav.agentverse.ai/) you need to register it as a Service. You can read through an example on how to achieve it here:
https://fetch.ai/docs/guides/agentverse/registering-agent-coin-toss#register-your-coin-toss-agent

Now you can enjoy checking already existing feedbacks in Notion with Notion RAG agent!