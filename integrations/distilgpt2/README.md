# DistilGPT2 Integrations Examples

DistilGPT2 integrations examples offer an easy-to-follow guide to setting up and using DistilGPT2 models. Ensure you have the following software installed:

- Python (v3.10+ recommended)
- Poetry (A Python packaging and dependency management tool)

## Setup

1. For the demo to work, you need to get HuggingFaceAPI Token:

    1. Visit [HuggingFace](https://huggingface.co/).
    2. Sign up or log in.
    3. Navigate to `Profile -> Settings -> Access Tokens`.
    4. Copy an existing token or create a new one.

2. In the `distilgpt2-integrations/src` directory, create a `.env` file and set your HuggingFaceAPI Token:

    ```
    export HUGGING_FACE_ACCESS_TOKEN="{Your HuggingFaceAPI Token}"
    ```

3. To load the environment variables from `.env` and install the dependencies:

    ```bash
    cd src
    source .env
    poetry install
    ```

## Running The Main Script

To run the project, use the command:

```
poetry run python main.py
```


After running the command, a request is sent to the agent every 10 minutes. The results can be seen in the console. Look for the following output in the logs:

```
Adding agent to Bureau: {agent_address}
```

Copy the {agent_address} value and replace AI_MODEL_AGENT_ADDRESS with this value in distilgpt2_user.py.

In the src/distilgpt2_user.py file, there's a variable COMPLETE_THIS. Change its value to customize the text you want auto-completed. Default value is:

```
COMPLETE_THIS = "My name is Clara and I am"
```

Now you can enjoy creating unique sentences with DistilGPT2!