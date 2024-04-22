# Finbert Integration

FinBERT is a pre-trained NLP model to analyze sentiment of financial text. It is built by further training the BERT language model in the finance domain, using a large financial corpus and thereby fine-tuning it for financial sentiment classification.

Ensure you have the following software installed:

- Python (v3.10+ recommended)
- Poetry (A Python packaging and dependency management tool)

## Setup

1. For the demo to work, you need to get HuggingFaceAPI Token:

    1. Visit [HuggingFace](https://huggingface.co/).
    2. Sign up or log in.
    3. Navigate to `Profile -> Settings -> Access Tokens`.
    4. Copy an existing token or create a new one.

2. In the `finbert/src` directory, create a `.env` file and set your HuggingFaceAPI Token:

    ```
    export HUGGING_FACE_ACCESS_TOKEN="{Your HuggingFaceAPI Token}"
    ```

3. To load the environment variables from `.env` and install the dependencies:

    ```bash
    cd src
    source .env
    poetry install
    ```

## Running The Script

To run the project, use the command:

```
poetry run python main.py
```

In the console look for the following output:

```
Adding agent to Bureau: {agent_address}

```

Copy the {agent_address} address and replace **AI_MODEL_AGENT_ADDRESS** value in agents/finbert_user.py.


You can change the input text to what you like, just open the src/finbert_user.py file, and change the value of **INPUT_TEXT** variable in agents/finbert_user.py.

The finbert model will give softmax outputs for three labels: positive, negative or neutral.