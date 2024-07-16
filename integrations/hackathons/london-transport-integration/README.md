# uAgent London Transport Examples 

This repository contains examples of london transport journey planner integrations using three agents: `tfl_agent` and `user_agent`.

1. `user_agent` : This agent takes from and to location request as details from user, and responds with all possible routes with detailed plan.

2. `tfl_agent`: This agent takes from and to location from user, fetches the post code using [UK PostCode API](https://rapidapi.com/search/uk%2Bpostcodes) and sends request to tfl request link with journey endpoint. https://api.tfl.gov.uk/Journey/JourneyResults/from_loc/to/to_loc. This sends all possible routes to the user agent.

## Getting Started 🚀

To use these agents, follow the steps below:

### Step 1: Obtain API Keys 🔑

Before running the agents, you need to obtain the required API keys:

#### UK_POSTCODE_API

1. Visit the RapidAPI website: https://rapidapi.com/search/uk%2Bpostcodes
2. If you don't have an account, create one by signing up.
3. Once you are logged in, click on test endpoint and register for API on free-tier.
4. Once done you will see X-RapidAPI-Key in header parameter.

### Step 2: Set API Keys and address in agent scripts

1. Fill in the API Keys in the `tfl_agent` scripts.
2. Replace the london_transport agent address in user agent's script.

### Step 3: Run Project

To run the project and its agents:

```bash
cd src
python main.py
```

Now you have the agents up and running to perform london transport journey planner integrations using the provided APIs. Happy integrating! 🎉
