

# src.uagents.experimental.mobility.protocols.base_protocol



## CheckIn Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/experimental/mobility/protocols/base_protocol.py#L29)

```python
class CheckIn(Model)
```

Signal message to send to an agent once entering its area of service



## CheckInResponse Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/experimental/mobility/protocols/base_protocol.py#L38)

```python
class CheckInResponse(Model)
```

Information to return after receiving a check-in message



## CheckOut Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/experimental/mobility/protocols/base_protocol.py#L51)

```python
class CheckOut(Model)
```

Signal message to optionally send when leaving the service area of an agent



## CheckOutResponse Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/experimental/mobility/protocols/base_protocol.py#L55)

```python
class CheckOutResponse(Model)
```

Checkout response to optionally include a summary regarding the "stay" in the service area



## StatusUpdate Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/experimental/mobility/protocols/base_protocol.py#L63)

```python
class StatusUpdate(Model)
```

Message to signal an update to all checked in mobility agents



## StatusUpdateResponse Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/experimental/mobility/protocols/base_protocol.py#L72)

```python
class StatusUpdateResponse(Model)
```

Optional response to return on a StatusUpdate

