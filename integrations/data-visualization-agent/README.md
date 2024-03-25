
# Overview
To create a visually appealing repository showcasing examples of amplitude events data represented on a graph using the Data Visualization Agent (uagents_agent)

## Getting Started 🚀
To use these Data Visualization agent, follow the steps below:

### Step 1: Obtain API Keys 🔑
Before running the agents, you need to obtain the required API keys:

#### Amplitude events API Key
1. Visit the amplitude events website: [amplitude events](https://www.docs.developers.amplitude.com/analytics/apis/dashboard-rest-api/#example-request_8)
2. Login using amplitude credentials.
3. Click on Get API Key and store this key at safe place.
4. For more information on how to use amplitude events refer [Amplitude events Quickstart](https://www.docs.developers.amplitude.com/data/sdks/sdk-quickstart/)

### Step 2: Installation
Install μAgents for Python 3.8 to 3.12:
Install Matplotlib 
Install Requests
Install dotenv 

### Step 3: Set up .env file
To run the demo, you need API keys from:
* AmplitudeAPI
 
Once you have all three keys, create a .env file in the project_name directory.
```bash

API_KEY="GET THE API KEY"
SECRET_KEY="GET THE SECRET KEY"

### Note: 
I've attempted to create my first agent, but currently, the lang chain is not implemented. I'll continue exploring how things work and plan to contribute more in the upcoming hackathon.