# uAgent Business Finder Integrations Examples 🤑

This repository contains examples of business finder integrations using three agents: `business_finder_agent`, `business_details_agent` and `user_agent`.

1. `user_agent` : This agent takes request as details from user (city and category), type of business they want to look for. 

2. `business_finder_agent`: This agent takes city and category from user, fetch city's location coordinates using [GeoCoding API](https://rapidapi.com/apininjas/api/geocoding-by-api-ninjas/) and passing it to [Local Business Finder](https://rapidapi.com/alreadycoded/api/local-business-listing-finder/) to fetch list of ten businesses names.

3. `business_details_agent`: This agent gets list of business names from business finder agent and takes input from user, which business they want details about. It retrieves the details of business using API's used in `business_finder_agent` and sends it to `business_finder_agent` which in turn sends it to user.

## Getting Started 🚀

To use these agents, follow the steps below:

### Step 1: Obtain API Keys 🔑

Before running the agents, you need to obtain the required API keys:

#### GeoCoding_API

1. Visit the RapidAPI website: https://rapidapi.com/apininjas/api/geocoding-by-api-ninjas/
2. If you don't have an account, create one by signing up.
3. Once you are logged in, click on test endpoint and register for API on free-tier.
4. Once done you will see X-RapidAPI-Key in header parameter.

#### LocalBusinessListingFinder_API 🛍️

1. Visit the RapidAPI website: https://rapidapi.com/alreadycoded/api/local-business-listing-finder/
2. If you don't have an account, create one by signing up.
3. Once you are logged in, click on test endpoint and register for API on free-tier.
4. Once done you will see X-RapidAPI-Key in header parameter.

### Step 2: Set API Keys and address in agent scripts

1. Fill in the API Keys in the `business_finder_agent` and `business_details_agent` scripts.
2. Check for all three agent's addresses and replace them at relevant places in the script.

### Step 3: Run Project

To run the project and its agents:

```bash
cd src
python main.py
```

Now you have the agents up and running to perform mobility integrations using the provided APIs. Happy integrating! 🎉