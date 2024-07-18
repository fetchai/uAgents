# Language Translation Agent

This uagents is based on `GPT model 3.5 Turbo` and helps to translate a given message from one language to another.

## Overview:

This is deltaV compatible uagents connected to agentverse using `mailbox`. The agent takes three different inputs from user which includes language_from, language_to and sentence to be tranlated.

## Prerequisites

To use this python script/ uagents for your integration you need below details:

    - An API key for [openAI](https://platform.openai.com/api-keys).
    - A `mailbox` address for your agent.
    - python > 3.10

## Steps to use the integration:

Below are the steps to use this integration:

### Steps to run this agent:

    - Open `terminal` and save script as `translator-agent.py`.
    - Run the script once to get your `agent's address` and terminate the script.
    - Use this agent's address to create a mailbox on [Agentverse](https://agentverse.ai/mailroom).
    - Replace your open_ai API key with actual API key.
    - Rerun the app to make the agent running.

### Steps to register agent as service.

    - Refer `service.json` to get details of service created to make this agent discoverable on agentverse.
    - Use this agent's address to create a service on [Agentverse](https://agentverse.ai/services).

### Steps to access the service/agent on DeltaV.

    - Login to [DeltaV](https://deltav.agentverse.ai/home).
    - Type in 'query' related like `I want to translate a sentence from English to Spanish.`
    - Choose your service and provide asked details.

