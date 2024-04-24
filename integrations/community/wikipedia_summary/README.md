# langchain-wikipedia x uAgents

Welcome to the langchain-wikipedia integration! This repository contains an agent that uses LangChain's Wikipedia integration to fetch summaries. The agent is designed to run locally but can communicate and be managed via Agentverse, making it accessible for interaction through DeltaV.

## Prerequisites

-   **Python 3.11.7 or less than or equal to 3.12**: Ensure Python is installed on your machine. Download it from Python.org.
-   **Agentverse Account**: Create an account on [Agentverse](https://agentverse.ai/) to deploy and manage your agent.

## Installation

1. **Clone this repository** to get started with the agent, and navigate to the directory.
    
2. **Install Required Libraries**: Use pip to install the necessary Python packages:
    
    `pip install uagents langchain_community uagents-ai-engine`
    

## Agent Setup

Inside the repository, you'll find the `wikipedia_agent.py` script. This script defines an agent capable of fetching Wikipedia summaries based on user queries.

1.  **Running the Agent**: Execute the script to start your agent:
        
        `py wikipedia_agent.py` 
        
    -   Upon starting, the agent's address will be printed in your console, and it may throw some error. Ignore the errors, and copy the address for now. This address will be used to configure your agent in Agentverse.
    
2. **Deployment on Agentverse**

-   *Create a Mailbox*: Log in to Agentverse and navigate to the Mailroom to create a mailbox for your agent. You need to use the address you generated in step one to create the mailbox.
-   *Copy Mailbox Key*: Copy the mailbox key for step 3.

3. **Configure the Agent**: Edit `wikipedia_agent.py`, replacing placeholder values with actual data:
    
    -   `SEED_PHRASE`: Your secret seed phrase for agent creation - you can leave it as-is if you want.
    -   `AGENT_MAILBOX_KEY`: The mailbox key obtained from Agentverse.
  
4. **Re-run the script**: Rerun the script with:   

 `py wikipedia_agent.py` 

- This will initialize the agent so that it can receive messages, and other agents know where to communicate with them.


## Interaction via DeltaV

Once your agent is configured locally, head over to Agentverse to create a service group - and then a service.

### Create a Service for Your Agent

1.  **Service Group Creation**:
    
    -   Go to "Services" in Agentverse.
    - Switch the tab to 'Service Groups' on the top, and click on 'New Service Group'
    -   Create a new private service group (e.g., "Wikipedia Services") and save it.
    
2.  **Add New Service**:
    
    -   Navigate back to the other tab ('Services').
    - Click on '+ New Service' and fill in the information. 
	    - Give it a very descriptive objective - this field is extremely helpful for Agent discovery on DeltaV.
	    - For 'Service group', select the one you created in the previous step.
	    - For 'Agent', select the mailbox agent you created before. 
	    - Add a field for "Query" that users will input to fetch the Wikipedia summary.

Now you can head over to [DeltaV](https://deltav.agentverse.ai/) to start interacting with it. When you are testing, remember to select 'Advanced Options', and click on the service group you created for this project.

You can now send Wikipedia queries through DeltaV's interface, and the agent will fetch and return summaries.

## Support

For support or more information about Agentverse and DeltaV integration, refer to the official [documentation](https://fetch.ai/docs).