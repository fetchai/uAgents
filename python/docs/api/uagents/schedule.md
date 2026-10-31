

# src.uagents.schedule

Cron-style schedules



## Cron Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/schedule.py#L11)

```python
class Cron()
```

A cron schedule evaluated in the given timezone (UTC by default).



#### delays[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/schedule.py#L30)
```python
def delays() -> Iterator[float]
```

Yield the number of seconds to wait until each successive scheduled time,
skipping any times that have already passed.

