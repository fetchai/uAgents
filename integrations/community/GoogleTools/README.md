# Google Tools Integration

This integration assists user to use Google tool of their choice and query to the tool according to their will.

## Overview:

This is deltaV compatible agents connected to agentverse using `mailbox`. The agent takes google tool agent is hosted on Agentverse and rest of agents are hosted locally. `Google Tool` agent ask user to choose from Finance, Jobs, Lens, Patent or Shcolar.

## Prerequisites

To use this python script/ uagents for your integration you need below details:

    - An API key for [SerpAPI](https://serpapi.com/).
    - Agentverse Credentials
    - A `mailbox` address for your agent.
    - python > 3.10

## Steps to use the integration:

Below are the steps to use this integration:

### Steps to run this agent:

    - Open [Agentverse](https://agentverse.ai/) and create a agent named `google Tools agent`. Add the script from `google_tools.py`. 
    - Open `terminal` and save scripts in the file system as shown.
    - Update the `Serp API keys in all tools file`.
    - Use this agent's address to create a mailbox on [Agentverse](https://agentverse.ai/mailroom) for all the tools agents.
    - Run all scripts and create a service for each one of them.
    - Google tools service is the `task` and rest all services are `subtasks`.

### Steps to register agent as service.

    - Refer `googletools.json` to get details of service created to make master agent discoverable on agentverse.
    - Refer `sample_tool.json` to get details of service created for tools agent.
    - Use this agent's address to create a service on [Agentverse](https://agentverse.ai/services).

### Steps to access the service/agent on DeltaV.

    - Login to [DeltaV](https://deltav.agentverse.ai/home).
    - Type in 'query' related like `I want to choose google tools of my choice.`
    - Choose your service and provide asked details.
    - Select tool of choice and query it.