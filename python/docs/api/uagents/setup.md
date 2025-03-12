

# src.uagents.setup

Agent's Setup.



#### fund_agent_if_low[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/setup.py#L16)
```python
def fund_agent_if_low(wallet_address: str,
                      min_balance: int = TESTNET_REGISTRATION_FEE) -> None
```

Checks the agent's wallet balance and adds testnet funds if it's below min_balance.

**Arguments**:

- `wallet_address` _str_ - The wallet address of the agent.
- `min_balance` _int_ - The minimum balance required. Defaults to TESTNET_REGISTRATION_FEE.

