<a id="src.uagents.experimental.mobility.protocols.base_protocol"></a>

# src.uagents.experimental.mobility.protocols.base`_`protocol

<a id="src.uagents.experimental.mobility.protocols.base_protocol.Location"></a>

## Location Objects

```python
class Location(Model)
```

<a id="src.uagents.experimental.mobility.protocols.base_protocol.Location.radius"></a>

#### radius

This is used for compatibility with uagents message model

<a id="src.uagents.experimental.mobility.protocols.base_protocol.CheckIn"></a>

## CheckIn Objects

```python
class CheckIn(Model)
```

Signal message to send to an agent once entering its area of service

<a id="src.uagents.experimental.mobility.protocols.base_protocol.CheckInResponse"></a>

## CheckInResponse Objects

```python
class CheckInResponse(Model)
```

Information to return after receiving a check-in message

<a id="src.uagents.experimental.mobility.protocols.base_protocol.CheckOut"></a>

## CheckOut Objects

```python
class CheckOut(Model)
```

Signal message to optionally send when leaving the service area of an agent

<a id="src.uagents.experimental.mobility.protocols.base_protocol.CheckOutResponse"></a>

## CheckOutResponse Objects

```python
class CheckOutResponse(Model)
```

Checkout response to optionally include a summary regarding the "stay" in the service area

<a id="src.uagents.experimental.mobility.protocols.base_protocol.StatusUpdate"></a>

## StatusUpdate Objects

```python
class StatusUpdate(Model)
```

Message to signal an update to all checked in mobility agents

<a id="src.uagents.experimental.mobility.protocols.base_protocol.StatusUpdateResponse"></a>

## StatusUpdateResponse Objects

```python
class StatusUpdateResponse(Model)
```

Optional response to return on a StatusUpdate

