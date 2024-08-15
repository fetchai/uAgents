# Web Summarizer Agent

The Web Summarizer Agent uses Fetch.ai's uagent technology to automatically summarize website content. It uses a combination of WebBaseLoader for fetching website content, LangChain for summarization processes, and ChatOpenAI (GPT-3.5) for processing and generating summaries.


## Usage

To start using the Web Summarizer Agent, follow these steps:

1. **Environment Setup**:
   - run `poetry install` to install the dependencies
   - Obtain your `OPENAI_API_KEY` from [OpenAI](https://openai.com/). Follow the instructions provided by the respective service to get your API key.

2. **Agent Initialization**:
   - Initialize the Web Summarizer Agent with a unique seed phrase and mailbox key.
   - Start the agent `python3 agent.py`

3. **Agent Initialization**:
   - Initialize the Web Summarizer Agent with a unique seed phrase and mailbox key.
   - Start the agent `python3 agent.py`
   - Create a new [service](https://agentverse.ai/services)
   - Login to [deltaV](https://deltav.agentverse.ai/) and select your service group
   - Provide description on deltaV, example: I want to get a summary of this website link: https://agentverse.ai/