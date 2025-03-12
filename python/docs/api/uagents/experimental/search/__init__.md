

# src.uagents.experimental.search.__init__



## AgentFilters Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/search/__init__.py#L85)

```python
class AgentFilters(BaseModel)
```

The set of filters that should be applied to the agent search entries



## AgentSearchCriteria Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/search/__init__.py#L102)

```python
class AgentSearchCriteria(BaseModel)
```

The search criteria that can be set for the agent search



## AgentGeoFilter Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/search/__init__.py#L125)

```python
class AgentGeoFilter(BaseModel)
```

The geo filter that can be applied to the agent search



## AgentGeoSearchCriteria Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/search/__init__.py#L138)

```python
class AgentGeoSearchCriteria(AgentSearchCriteria)
```

The search criteria that can be set for the agent search



#### geosearch_agents_by_proximity[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/search/__init__.py#L176)
```python
def geosearch_agents_by_proximity(latitude: float,
                                  longitude: float,
                                  radius: float,
                                  limit: int = 30) -> list[Agent]
```

Return all agents in a circle around the given coordinates that match the given search criteria



#### geosearch_agents_by_protocol[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/search/__init__.py#L194)
```python
def geosearch_agents_by_protocol(latitude: float,
                                 longitude: float,
                                 radius: float,
                                 protocol_digest: str,
                                 limit: int = 30) -> list[Agent]
```

Return all agents in a circle around the given coordinates that match the given search criteria



#### geosearch_agents_by_text[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/search/__init__.py#L219)
```python
def geosearch_agents_by_text(latitude: float,
                             longitude: float,
                             radius: float,
                             search_text: str,
                             limit: int = 30) -> list[Agent]
```

Return all agents in a circle around the given coordinates that match the given search_text



#### search_agents_by_protocol[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/search/__init__.py#L235)
```python
def search_agents_by_protocol(protocol_digest: str,
                              limit: int = 30) -> list[Agent]
```

Return all agents that match the given search criteria



#### search_agents_by_text[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/search/__init__.py#L251)
```python
def search_agents_by_text(search_text: str, limit: int = 30) -> list[Agent]
```

Return all agents that match the given search_text

