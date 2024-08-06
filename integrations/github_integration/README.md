# GitHub Repository Fetcher Agent

This `uagent` fetches and lists all repositories for a given GitHub organization using the GitHub API.

## Overview

This is a deltaV compatible `uagent`. The agent takes an organization name as input and returns a list of github repositories for that organization.

## Prerequisites

To use this Python script/get_github_repositories for your integration, you need the following details:
- An API key for [GitHub](https://github.com/settings/tokens).
- Python > 3.10

## Steps to Use the Integration

### Steps to Run this Agent

1. Login to [Agentverse](https://agentverse.ai) and create a `New Agent`.
2. Select `Blank Agent` and assign a name to your agent.
3. Copy the content from `get_github_repositories.py` into `agent.py`.
4. Replace `YOUR_GITHUB_TOKEN` with your GITHUB API key.
5. Click on `Start` to make the agent running.

### Steps to Register Agent as a Function

1. Once the agent is running, select `Deploy` and create a `New Function`.
2. Refer to `function.json` to get details of the function created to make this agent discoverable on Agentverse.

### Steps to Access the Service/Agent on DeltaV

1. Login to [DeltaV](https://deltav.agentverse.ai/home).
2. Type in a query related to fetching repositories, like `I want to get a list of Github Repositories in my organisation`.
3. Choose your function and provide the asked details.

