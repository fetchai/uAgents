# Exchange protocol

## Overview

The **μAgents Exchange Protocol** defines a simple standard by which the agents communicate.

In this protocol, agents can send ***messages*** enclosed in ***envelopes***, which are then encoded and sent via HTTP to the ***endpoints*** of other agents.

We break down each of these concepts in more detail below.

## Messages

Messages consist of key-value pairs following the standard JSON format.

Here are a few examples:
```json
{"message": "hello"}
```
```json
{"name": "alice", "age": 26, "languages": ["English", "Japanese", "Arabic"]}
```
```json
{"item": "pretzel", "bid": {"amount": 120, "denomination": "GBP"}}
```

Once created, messages are then enclosed in envelopes containing some important metadata.

## Envelopes

Envelopes have the following form and are quite similar to blockchain transactions:

```python
@dataclass
class Envelope:
    sender: str:            # bech32-encoded public address
    target: str:            # bech32-encoded public address
    session: str            # UUID
    schema_digest: str      # digest of message schema used for routing
    protocol_digest: str    # digest of protocol containing message 
    payload: bytes          # JSON type: base64 str
    expires: int            # Unix timestamp in seconds
    nonce: int              # unique message nonce
    signature: str          # bech32-encoded signature
```

### Semantics

The **sender** field exposes the address of the sender of the message.

The **target** field exposes the address of the recipient of the message.

The **schema_digest** contains the unique schema digest string for the message.

The **protocol_digest** contains the unique digest for protocol containing the message if available.

The **payload** field exposes the payload of the protocol. Its JSON representation should be a base64 encoded string.

The **expires** field contains the Unix timestamp in seconds at which the message is no longer valid.

The **nonce** is a sequential number used to ensure each message is unique.

The **signature** field contains the signature that is used to authenticate that the message has been sent from the **sender** agent.

Envelopes are then JSON encoded and sent to endpoints of other agents or services.

## Endpoints

The protocol supports only one standardised endpoint:

```HTTP 1.1 POST /submit```

and expects data which is broadly JSON compatible. The protocol currently supports MIME content type `application/json`.

