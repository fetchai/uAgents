# Public Repository Fetching Agent

This uAgent queries all public repositories of a given GitHub username, ordered from most to least recently contributed to.

## Overview:

This is a DeltaV compatible agent connected to the agentverse. The agent has one field, `username`, which is the username of the GitHub account to query public repositories from.

## Prerequisites

- Python version > 3.10
- Agentverse account

## Steps to Use the Integration

### Set Up Agent on Agentverse

1. Create an account and login to [Agentverse](https://agentverse.ai).
2. Click the `New Agent` button, and select the `Blank Agent` template.
3. Copy the content from `get_public_repositories.py` into the `agent.py` file on the agentverse code editor.
4. Click `Start` to run the agent.

### Register the Agent as a Function

1. While the agent is running on the Agentverse, select on the `Deploy` tab and click the `New Function` button to create a new DeltaV function.
2. Enter a name and description for the function, as well as a description for the field(s) listed.
3. (Optional) Test the newly formed function on DeltaV by turning on advanced settings, and select `My Functions` from the function group dropdown.
4. Deploy the function to DeltaV by clicking `Publish`.

### Access the Agent on DeltaV

1. Login to [DeltaV](https://deltav.agentverse.ai/home) using your Google account or Fetch Wallet.
2. Enter a query related to fetching the repositories of a specific user.
3. Choose the function and provide the requested field.
