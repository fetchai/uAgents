This example consists of the following agents:

* charger_search_agents: An agent offering a search protocol to run detailed queries regarding EV charging stations that go beyond the capability of the search api. There is both a sync and an async implementation of the agent to compare implementational differences for the same solution.
* searching_agent: A user agent showcasing how to execute a search with the search agent.
* hit_agent: An agent satisfying the general parameters and the specific attributes
* miss_agent: An agent satisfying the general parameters but not the specific attributes

How to run the example:

1. Start the charger_search_agent, hit_agent and miss_agent
2. Put the search_agents's address as `SEARCH_AGENT = ...` in searching_agent
2. (?) Wait a couple of minutes to let the information propagate through agentverse etc.
3. Run the searching agent
4. It should only get the hit_agent's address as a result

```
title General Search Agent Flow

participant "User Agent" as U
participant "Search Agent" as S
participant "Search Engine" as E
participant "Hit Agent" as RP
participant "Miss Agent" as RN

note over RP, RN: Assuming all agents representing \nthe desired information / entities \nare supporting the same protocol

U->S: search for agents with filters
note over S: check cache here or only after search engine?
S->E: query general agent group
S<-E: list of agents
loop list of agents
S->RP: query attributes
S->RN: query attributes
end
S<-RP: return attributes 
S<-RN: return empty list
loop responses
S->S: add to cache
alt attribute match
S->S: add to result list
end
end
U<-S: result list
U->RP: consume
```