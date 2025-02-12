

# src.uagents.registration



#### coerce_metadata_to_str[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/registration.py#L84)
```python
def coerce_metadata_to_str(
    metadata: Optional[Dict[str, Any]]
) -> Optional[Dict[str, Union[str, Dict[str, str]]]]
```

Step through the metadata and convert any non-string values to strings.



#### extract_geo_metadata[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/registration.py#L103)
```python
def extract_geo_metadata(
        metadata: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]
```

Extract geo-location metadata from the metadata dictionary.



## LedgerBasedRegistrationPolicy Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/registration.py#L272)

```python
class LedgerBasedRegistrationPolicy(AgentRegistrationPolicy)
```



#### check_contract_version[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/registration.py#L329)
```python
def check_contract_version()
```

Check the version of the deployed Almanac contract and log a warning
if it is different from the supported version.



#### register[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/registration.py#L343)
```python
async def register(agent_identifier: str,
                   identity: Identity,
                   protocols: List[str],
                   endpoints: List[AgentEndpoint],
                   metadata: Optional[Dict[str, Any]] = None)
```

Register the agent on the Almanac contract if registration is about to expire or
the registration data has changed.

