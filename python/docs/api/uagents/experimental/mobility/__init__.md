

# src.uagents.experimental.mobility.__init__



## MobilityAgent Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/mobility/__init__.py#L26)

```python
class MobilityAgent(Agent)
```



#### proximity_agents[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/mobility/__init__.py#L54)
```python
@property
def proximity_agents() -> list[SearchResultAgent]
```

List of agents that this agent has checked in with.
(i.e. agents that are in proximity / within the radius of this agent)



#### checkedin_agents[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/mobility/__init__.py#L62)
```python
@property
def checkedin_agents() -> dict[str, dict[str, Any]]
```

List of agents that have checked in with this agent.
(i.e. agents which radius this agent is within)



#### update_geolocation[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/mobility/__init__.py#L88)
```python
async def update_geolocation(location: Location) -> None
```

Call this method with new location data to update the agent's location

