<a id="src.uagents.mailbox"></a>

# src.uagents.mailbox

<a id="src.uagents.mailbox.is_mailbox_agent"></a>

#### is`_`mailbox`_`agent

```python
def is_mailbox_agent(endpoints: list[AgentEndpoint],
                     agentverse: AgentverseConfig) -> bool
```

Check if the agent is a mailbox agent.

**Returns**:

- `bool` - True if the agent is a mailbox agent, False otherwise.

<a id="src.uagents.mailbox.register_in_agentverse"></a>

#### register`_`in`_`agentverse

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

- `RegistrationResponse` - Registration

<a id="src.uagents.mailbox.update_agent_details"></a>

#### update`_`agent`_`details

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

<a id="src.uagents.mailbox.MailboxClient"></a>

## MailboxClient Objects

```python
class MailboxClient()
```

Client for interacting with the Agentverse mailbox server.

<a id="src.uagents.mailbox.MailboxClient.run"></a>

#### run

```python
async def run()
```

Runs the mailbox client.

