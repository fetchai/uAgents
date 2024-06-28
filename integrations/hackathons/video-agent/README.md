# Youtube Video Summarization and Question Answering Agent

This project is a Youtube video summarization and question answering agent. It uses natural language processing techniques to generate summaries of Youtube videos and answer questions based on the video content.

## Installation

1. Clone uagents repo and navigate to this folder

2. Use `poetry install` to install the dependencies

3. Obtain the [OpenAI](https://openai.com/) and [Anthropoc](https://anthropic.com/) key. Follow the instructions provided by the respective service to get your API key.

```bash
export OPENAI_API_KEY=YOUR_KEY
export ANTHROPIC_API_KEY=YOUR_KEY
```

4. Run the following command in your terminal:
  ```bash
  python -m spacy download en_core_web_lg
  ```


## Usage

0. Generate a random seed phrase and edit agent.py and set the SEED to your secret!
1. Run the agent using the following command:
```
poetry run agent
```

2. Copy out your agent address, and go to agentverse.ai, log in and create a Mailroom mailbox for this agent, copy out the key and set it as the following environment variable:
```bash
export AGENT_MAILBOX_KEY=YOUR_KEY
```

3. Run your agent using `poetry run agent`

4. Go to agentverse.ai and register your agent as a service! Afterwards you can go to https://deltav.agentverse.ai and play with your agent!

