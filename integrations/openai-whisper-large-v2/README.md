# openai whisper model integration

Whisper is a pre-trained model for automatic speech recognition (ASR) and speech translation. Trained on 680k hours of labelled data, Whisper models demonstrate a strong ability to generalise to many datasets and domains without the need for fine-tuning.

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

    open terminal and goto "./openai-whisper-large-v2/src" and
    run below command to load environment variables and run the agent.

    ```bash
    export HUGGING_FACE_ACCESS_TOKEN="{Your HuggingFaceAPI Token}"
    poetry run python agent.py
    ```

    Check the log for "Adding Agent to Bureau" line and copy the {agent address}.

4.  **Running The User Script**

    open terminal and goto "./openai-whisper-large-v2/src" and
    run below command to load environment variables and run the client.

    ```bash
    export WHISPER_AGENT_ADDRESS="{ agent address from last step }"
    poetry run python user.py
    ```

After running the command, a request is sent to the agent every 30 sec till its successful.
    
You can change the RECORDING_FILE variable to transcript your own audio file.