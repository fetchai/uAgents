<a id="src.uagents.experimental.search.__init__"></a>

# src.uagents.experimental.search.`__`init`__`

<a id="src.uagents.experimental.search.__init__.AgentFilters"></a>

## AgentFilters Objects

```python
class AgentFilters(BaseModel)
```

The set of filters that should be applied to the agent search entries

<a id="src.uagents.experimental.search.__init__.AgentSearchCriteria"></a>

## AgentSearchCriteria Objects

```python
class AgentSearchCriteria(BaseModel)
```

The search criteria that can be set for the agent search

<a id="src.uagents.experimental.search.__init__.AgentGeoFilter"></a>

## AgentGeoFilter Objects

```python
class AgentGeoFilter(BaseModel)
```

The geo filter that can be applied to the agent search

<a id="src.uagents.experimental.search.__init__.AgentGeoSearchCriteria"></a>

## AgentGeoSearchCriteria Objects

```python
class AgentGeoSearchCriteria(AgentSearchCriteria)
```

The search criteria that can be set for the agent search

<a id="src.uagents.experimental.search.__init__.geosearch_agents_by_proximity"></a>

#### geosearch`_`agents`_`by`_`proximity

```python
def geosearch_agents_by_proximity(latitude: float,
                                  longitude: float,
                                  radius: float,
                                  limit: int = 30)
```

Return all agents in a circle around the given coordinates that match the given search criteria

<a id="src.uagents.experimental.search.__init__.geosearch_agents_by_protocol"></a>

#### geosearch`_`agents`_`by`_`protocol

```python
def geosearch_agents_by_protocol(latitude: float,
                                 longitude: float,
                                 radius: float,
                                 protocol_digest: str,
                                 limit: int = 30)
```

Return all agents in a circle around the given coordinates that match the given search criteria

<a id="src.uagents.experimental.search.__init__.geosearch_agents_by_text"></a>

#### geosearch`_`agents`_`by`_`text

```python
def geosearch_agents_by_text(latitude: float,
                             longitude: float,
                             radius: float,
                             search_text: str,
                             limit: int = 30)
```

Return all agents in a circle around the given coordinates that match the given search_text

<a id="src.uagents.experimental.search.__init__.search_agents_by_protocol"></a>

#### search`_`agents`_`by`_`protocol

```python
def search_agents_by_protocol(protocol_digest: str, limit: int = 30)
```

Return all agents that match the given search criteria

<a id="src.uagents.experimental.search.__init__.search_agents_by_text"></a>

#### search`_`agents`_`by`_`text

```python
def search_agents_by_text(search_text: str, limit: int = 30)
```

Return all agents that match the given search_text

