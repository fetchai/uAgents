

# src.uagents.mailbox



#### is_mailbox_agent[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/mailbox.py#L86)
```python
def is_mailbox_agent(endpoints: list[AgentEndpoint],
                     agentverse: AgentverseConfig) -> bool
```

Check if the agent is a mailbox agent.

**Returns**:

- `bool` - True if the agent is a mailbox agent, False otherwise.



#### register_in_agentverse[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/mailbox.py#L98)
```python
async def register_in_agentverse(
        request: AgentverseConnectRequest,
        identity: Identity,
        prefix: AddressPrefix,
        agentverse: AgentverseConfig,
        agent_details: Optional[AgentUpdates] = None) -> RegistrationResponse
```

Registers agent in Agentverse

**Arguments**:

- `request` _AgentverseConnectRequest_ - Request object
- `identity` _Identity_ - Agent identity object
- `prefix` _AddressPrefix_ - Agent address prefix
  can be "agent" (mainnet) or "test-agent" (testnet)
- `agentverse` _AgentverseConfig_ - Agentverse configuration
- `agent_details` _Optional[AgentUpdates]_ - Agent details (name, readme, avatar_url)
  

**Returns**:

- `RegistrationResponse` - Registration response object



#### unregister_in_agentverse[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/mailbox.py#L166)
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



#### update_agent_details[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/mailbox.py#L200)
```python
async def update_agent_details(user_token: str,
                               agent_address: str,
                               agent_details: AgentUpdates,
                               agentverse: Optional[AgentverseConfig] = None)
```

Updates agent details in Agentverse.

**Arguments**:

- `user_token` _str_ - User token
- `agent_address` _str_ - Agent address
- `agent_details` _AgentUpdates_ - Agent details
- `agentverse` _Optional[AgentverseConfig]_ - Agentverse configuration



## MailboxClient Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/mailbox.py#L233)

```python
class MailboxClient()
```

Client for interacting with the Agentverse mailbox server.



#### run[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/mailbox.py#L248)
```python
async def run()
```

Runs the mailbox client.

