# Google Gemini Generative AI Integration 🤑

This repository contains examples of Google Gemini chat conversation integrations using two agents: `Gemini_agent` and `user_agent`.

1. `user_agent` : This agent takes request from user (message) and queries google gemini agent. 

2. `Gemini_agent`: This agent takes query from user, and asks google gemini generative AI for response. [Google Gemini ](https://makersuite.google.com/app/prompts/new_freeform). Once it gets response from generative AI. It sends back to user.

## Getting Started 🚀

To use these agents, follow the steps below:

### Step 1: Obtain API Keys 🔑

Before running the agents, you need to obtain the required API keys:

#### Google Gemini API Key

1. Visit the Google AI Studio website: [Google AI Studio](https://makersuite.google.com/app/prompts/new_freeform)
2. Login using google credentials.
3. Click on Get API Key and store this key at safe place.
4. For more information on how to use Gemini API refer [Gemini API Quickstart](https://ai.google.dev/tutorials/python_quickstart#chat_conversations)

### Step 2: Set API Keys and address in agent scripts

1. Fill in the API Keys in the `gemini_agent` scripts.
2. Check for all gemini_agent address and replace it into the google agent.

### Step 3: Run Project

To run the project and its agents:

```bash
cd src
python main.py
```

Now you have the agents up and running to perform gemini integrations using the provided APIs. Happy integrating! 🎉