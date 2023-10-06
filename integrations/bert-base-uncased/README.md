# BERT-BASE Model Integration

## **About BERT-BASE**

BERT base model (uncased) Pretrained model on English language using a masked language modeling (MLM) objective. It was introduced in this paper and first released in this repository. This model is uncased: it does not make a difference between english and English.

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

    open terminal goto "bert-base-uncased/src",
    run below command to load environment variables and run the agent.

    ```bash
    export HUGGING_FACE_ACCESS_TOKEN="{Your HuggingFaceAPI Token}"
    poetry run python agent.py
    ```

    Check the log for "adding bert-base agent to bureau" line and copy the {agent address}.

4.  **Running The User Script**

    open new terminal and goto "bert-base-uncased/src",
    run below command to load environment variables and run the client.

    ```bash
    export BERT_BASE_AGENT_ADDRESS="{ agent address from last step }"
    poetry run python client.py
    ```

After running the command, a request is sent to the agent every 30 sec till its successful.

Modify **INPUT_TEXT** in **bert_base_user.py** to predict a different sentences.