This example consists of the following agents:

* charger_search_agent: An agent offering a search protocol to run detailed queries regarding EV charging stations that go beyond the capability of the search api.
* searching_agent: A user agent showcasing how to execute a search with the search agent.
* hit_agent: An agent satisfying the general parameters and the specific attributes
* miss_agent: An agent satisfying the general parameters but not the specific attributes

How to run the example:

1. Start the search_agent, hit_agent and miss_agent
2. Put the search_agents's address as `SEARCH_AGENT = ...` in searching_agent
2. (?) Wait a couple of minutes to let the information propagate through agentverse etc.
3. Run the searching agent
4. It should only get the hit_agent's address as a result