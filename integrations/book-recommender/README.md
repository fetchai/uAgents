# uAgent Book Recommender

This repository contains example of Book Recommendation using one agent `agent.py`

## Introduction
The personalized book system allows users to create custom books by selecting parameter such as genre.The system then generates a personalized book based on the user's preferences (genre) by providing the book title and authors name.


## Getting Started 🚀
To use these agents, follow the steps below:

### Step 1: Obtain API 🔑
Before running the agents, you need to obtain the required API

#### OpenLibrary API
1. Visit the OpenLibrary website: [https://openlibrary.org/developers/api](https://openlibrary.org/developers/api "OpenLibrary Website")
2. You dont have to create any account it is directly accessible
3. Once you visit the website you will see a `BOOK SEARCH` on the main page
4. Click on it and you will get your API endpoint there

### Step 2: 
Paste the API on the `base_url` of `agent.py`

### Step 3: Run Project
To run the Project
```
python agent.py
```
This can be used for running the agent to perform book recommendation task using the provided API on the local system.

### Step 4: Run the project on agent verse
1. To run this project on agentverse, create an agent and add the `agent.py` code.

2. Create a Service by specifying the Title, Description and other details.
   ![image](https://github.com/Pixathon-Saavyas/Neurons/assets/5381124/645fcc16-a3e0-4304-925c-a2ad5f10d6c1)
   
4. Run the service on DeltaV   


## Sample Output on DeltaV:
![brs](https://github.com/Pixathon-Saavyas/Neurons/assets/5381124/8dc7f50c-ec96-4895-b263-d85940341f19)

