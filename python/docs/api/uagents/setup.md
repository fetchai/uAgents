

# src.uagents.setup

Agent's Setup.



#### fund_agent_if_low[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/setup.py#L14)
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



#### register_agent_with_mailbox[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/setup.py#L39)
```python
def register_agent_with_mailbox(agent: Agent, email: str)
```

Registers the agent on a mailbox server using the provided email.

**Arguments**:

- `agent` _Agent_ - The agent object to be registered.
- `email` _str_ - The email address associated with the agent.
  

**Returns**:

  None

