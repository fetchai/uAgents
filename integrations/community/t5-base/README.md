# T5-BASE Model Integration

## **About T5-BASE**

The T5 model is a Text-to-Text Transfer Transformer model that was developed by Google Research. It's a large-scale transformer-based language model that's designed to handle a wide range of NLP tasks, including translation, summarization, and question answering.

## Requirements

- Python (v3.10+ recommended)
- Poetry (A Python packaging and dependency management tool)

## Setup

1. For the demo to work, you need to get HuggingFaceAPI Token:

    1. Visit [HuggingFace](https://huggingface.co/).
    2. Sign up or log in.
    3. Navigate to `Profile -> Settings -> Access Tokens`.
    4. Copy an existing token or create a new one.

2. **Install Dependencies**

    ```bash
    poetry install
    ```

3.  **Running The Agent Script**

    open terminal goto "t5-base/src", run below command to load environment variables and run the agent.

    ```bash
    export HUGGING_FACE_ACCESS_TOKEN="{Your HuggingFaceAPI Token}"
    poetry run python agent.py
    ```

    Check the log for "adding t5-base agent to bureau" line and copy the {agent address}.

4.  **Running The User Script**

    open terminal and goto "t5-base/src",run below command to load environment variables and run the client.

    ```bash
    export T5_BASE_AGENT_ADDRESS="{ agent address from last step }"
    poetry run python client.py
    ```

After running the command, a request is sent to the agent every 30 sec till its successful.

Modify **INPUT_TEXT** in **t5_base_user.py** to translate different sentence.
