# Rainforest API Integration

## Overview
Rainforest API integration enhances the capabilities of an AI agent by leveraging Rainforest Product Data API. This integration allows the AI agent to perform advanced searches, providing users with relevant data based on their search queries.  


## Rainforest API
**Rainforest** is a real-time, high-scale API to request Amazon product data, customer reviews, seller offers, search results, category listing results and bestselling products.

## Usage
To use the Rainforest API integration, create an instance of the `SearchAmazonRequest` model with a specific query and send it to the agent. The agent will utilize the Rainforest Product Search API to perform the search and respond with formatted results.

# Getting Rainforest API Key

To access the Rainforest API, you need an API key. Follow these steps to obtain your API key:

1. Visit the Rainforest website at [https://www.rainforestapi.com/](https://www.rainforestapi.com/).
2. Sign up or log in to your account.
3. Navigate to the API section.
4. Create a new API key.
5. Copy the generated API key.
6. Replace the placeholder in the script with your actual API key.

Ensure that you keep your API key secure and do not share it publicly. It is a sensitive credential that grants access to Rainforest services.

# Agent Secrets on Agentverse

1. Go to the Agentverse platform.
2. Navigate to the Agent Secrets section.
3. Create an agent and copy the code in it
4. Add a new secret with the key `API_KEY` and the value as your API KEY.

# Steps to Enroll an Agent as a Service on Agentverse

You can integrate into DeltaV your Agents created on your local computer, IoT devices, in the VMs, or agents created on Agentverse. The steps are the same.

Once your agents are run, the agent protocol manifests are uploaded to the Almanac contract in the form of protocol digests. After uploading the manifests, we take the agent addresses and enroll the agents as a service under the "Services" tab in Agentverse.

## Agent Validation on Agentverse Explorer
*Note: You can validate the procedure by searching for your agent's address on Agent Explorer, checking if the protocols have been uploaded successfully. If not, you need to wait for some time (1-2 minutes) until the protocols are uploaded successfully.*

## Create a Service Group

1. Start by creating a new service group on Agentverse.
2. Set up the service group as PRIVATE (you will only be able to see your own agents).
   - If you set up your service group as Public, anyone will be able to see your agents.

**Service group has been created.**

## Create a Service

1. To register the agents as a service, input a concise title and description for the agent service.
2. Choose the service group for the agent service that you've created previously.
3. Fill in the agent address in the Agent field.
4. Set the task type to Task.

Now, your agents are enrolled as a service in Agentverse. You can manage and monitor them under the "Services" tab. Ensure that you follow the agent validation steps on Agent Explorer to confirm successful enrollment.