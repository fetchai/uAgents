<a id="src.uagents.experimental.mobility.__init__"></a>

# src.uagents.experimental.mobility.`__`init`__`

<a id="src.uagents.experimental.mobility.__init__.MobilityAgent"></a>

## MobilityAgent Objects

```python
class MobilityAgent(Agent)
```

<a id="src.uagents.experimental.mobility.__init__.MobilityAgent.proximity_agents"></a>

#### proximity`_`agents

```python
@property
def proximity_agents() -> list[SearchResultAgent]
```

List of agents that this agent has checked in with.
(i.e. agents that are in proximity / within the radius of this agent)

<a id="src.uagents.experimental.mobility.__init__.MobilityAgent.checkedin_agents"></a>

#### checkedin`_`agents

```python
@property
def checkedin_agents() -> dict[str, dict[str, Any]]
```

List of agents that have checked in with this agent.
(i.e. agents which radius this agent is within)

<a id="src.uagents.experimental.mobility.__init__.MobilityAgent.update_geolocation"></a>

#### update`_`geolocation

```python
async def update_geolocation(location: Location)
```

Call this method with new location data to update the agent's location

