

# src.uagents.mailbox



#### is_mailbox_agent[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/mailbox.py#L68)
```python
def is_mailbox_agent(endpoints: list[AgentEndpoint],
                     agentverse: AgentverseConfig) -> bool
```

Check if the agent is a mailbox agent.

**Returns**:

- `bool` - True if the agent is a mailbox agent, False otherwise.



#### register_in_agentverse[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/mailbox.py#L92)
```python
async def register_in_agentverse(
        request: AgentverseConnectRequest, identity: Identity,
        prefix: AddressPrefix, agentverse: AgentverseConfig,
        agent_details: RegistrationRequest) -> RegistrationResponse
```

Registers agent in Agentverse

**Arguments**:

- `request` _AgentverseConnectRequest_ - Request object
- `identity` _Identity_ - Agent identity object
- `prefix` _AddressPrefix_ - Agent address prefix
  can be "agent" (mainnet) or "test-agent" (testnet)
- `agentverse` _AgentverseConfig_ - Agentverse configuration
- `agent_details` _RegistrationRequest | None_ - Agent details to register
  

**Returns**:

- `RegistrationResponse` - Registration response object



#### unregister_in_agentverse[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/mailbox.py#L155)
```python
async def unregister_in_agentverse(
        request: AgentverseDisconnectRequest, agent_address: str,
        agentverse: AgentverseConfig) -> UnregistrationResponse
```

Unregisters agent in Agentverse

**Arguments**:

- `request` _AgentverseDisconnectRequest_ - Request object
- `agent_address` _str_ - The agent's address
- `agentverse` _AgentverseConfig_ - Agentverse configuration
  

**Returns**:

- `UnregistrationResponse` - Unregistration response object



## MailboxClient Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/mailbox.py#L186)

```python
class MailboxClient()
```

Client for interacting with the Agentverse mailbox server.



#### run[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/mailbox.py#L202)
```python
async def run()
```

Runs the mailbox client.

