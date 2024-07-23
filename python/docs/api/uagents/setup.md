<a id="src.uagents.setup"></a>

# src.uagents.setup

Agent's Setup.

<a id="src.uagents.setup.fund_agent_if_low"></a>

#### fund`_`agent`_`if`_`low

```python
def fund_agent_if_low(wallet_address: str,
                      min_balance: int = REGISTRATION_FEE)
```

Checks the agent's wallet balance and adds testnet funds if it's below min_balance.

**Arguments**:

- `wallet_address` _str_ - The wallet address of the agent.
- `min_balance` _int_ - The minimum balance required.
  

**Returns**:

  None

<a id="src.uagents.setup.register_agent_with_mailbox"></a>

#### register`_`agent`_`with`_`mailbox

```python
def register_agent_with_mailbox(agent: Agent, email: str)
```

Registers the agent on a mailbox server using the provided email.

**Arguments**:

- `agent` _Agent_ - The agent object to be registered.
- `email` _str_ - The email address associated with the agent.
  

**Returns**:

  None

