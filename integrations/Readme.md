# Podcast Search Agent

This code implements a Fetch.ai AI Agent named "Podcast Search Agent" designed to search for podcasts using the ListenNotes API.

## Requirements
- Python 3.6 or higher
- `ai_engine` library
- `http` module from `ai_engine.utils`

## Usage
1. Import necessary libraries including `Agent`, `Context`, `Protocol`, `Model`, `UAgentResponse`, `UAgentResponseType`, and `http`.
2. Define a model `PodcastSearchRequest` to represent the search query for podcasts.
3. Implement a function `test_listennotes_api_request` to make a request to the ListenNotes API for podcast search.
4. Create a test class `TestListenNotesAPI` to test the podcast search API request.
5. Instantiate an agent named "Podcast Search Agent".
6. Define a protocol named "Podcast Search Protocol".
7. Implement a message handler function `search_podcasts` to handle incoming podcast search requests.
8. Include the protocol in the agent and run the agent.

## Steps
1. The code defines a model `PodcastSearchRequest` with a default query parameter set to "star wars".
2. It implements the `test_listennotes_api_request` function to make an asynchronous HTTP GET request to the ListenNotes API with the provided query parameters.
3. A test class `TestListenNotesAPI` is defined to ensure the functionality of the API request.
4. An agent named "Podcast Search Agent" is created.
5. A protocol named "Podcast Search Protocol" is defined.
6. A message handler function `search_podcasts` is implemented to handle incoming podcast search requests by calling the `test_listennotes_api_request` function and sending the response back.
7. The protocol is included in the agent, and the agent is run.

## API Key
Ensure to replace the placeholder API key with your actual ListenNotes API key. Link for that is https://www.listennotes.com/api

## Dependencies
- `ai_engine`: This library provides the infrastructure for creating AI agents.
- `http` module: This module provides utilities for making HTTP requests.

## Note
This code demonstrates a basic implementation of a podcast search agent using the Fetch.ai AI Agent technology. Modify and extend it according to your specific requirements.
