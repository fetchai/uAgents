<a id="src.uagents.registration"></a>

# src.uagents.registration

<a id="src.uagents.registration.generate_backoff_time"></a>

#### generate`_`backoff`_`time

```python
def generate_backoff_time(retry: int) -> float
```

Generate a backoff time starting from 0.128 seconds and limited to ~131 seconds

<a id="src.uagents.registration.coerce_metadata_to_str"></a>

#### coerce`_`metadata`_`to`_`str

```python
def coerce_metadata_to_str(
    metadata: Optional[Dict[str, Any]]
) -> Optional[Dict[str, Union[str, Dict[str, str]]]]
```

Step through the metadata and convert any non-string values to strings.

