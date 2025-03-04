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

```
title General Search Agent Flow

participant "User Agent" as U
participant "Search Agent" as S
participant "Search Engine" as E
participant "Positive Result Agent" as RP
participant "Negative Result Agent" as RN

note over RP, RN: Assuming all agents representing \n
the desired information / entities \nare supporting the same protocol

U->S: search for agents with filters
note over S: check cache here or only after search engine?
S->E: query general agent group
S<-E: list of agents
group broadcast
S->RP: query attributes
S->RN: query attributes
end
alt agent not fitting
S<-RN: return attributes or false?
else
S<-RP: return attributes or true?
S->S: add to cache
S->S: add to result list
end
U<-S: result list
U->RP: consume
```