# uAgent Movie Database Integration

This repository contains example of movie database integration using three entities: agent1, agent2, and user

1. user: Takes movie search from the user.

2. agent1: Takes movie ID from the user and provides with movie title and release year.

3. agent2: Takes movie ID from the user and provides with movie rating and n number of votes.

# Getting started


## Step 1: Obtain API keys

- Before running the agents, you need to obtain required API keys:




## Movie Database API

1. Visit the RapidAPI website:https://rapidapi.com/SAdrian/api/moviesdatabase/
2. If you don't have a account, create one by signing up.
3. Once you are logged in, click on test endpoint and register for API on free-tier.
4. Once done you will see X-RapidAPI-Key in header parameter.

## Step 2: Set API Keys and address in agent scripts

1. Fill in the API keys in the agent1 and agent2 scripts.
2. Fill in the API keys in the user scripts.




## Step 3: Run Project

To deploy this project run

```bash
  cd src
  python main.py
```

Now you have the agents up and running to perform movie database integrations using the provided APIs.