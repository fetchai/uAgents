from protocol.protocol import proto
from uagents import Agent, Bureau

AGENT_INFO = {
    "alice": {"seed": "replace_with_alice_seed", "min_price": 45},
    "bob": {"seed": "replace_with_bob_seed", "min_price": 55},
    "charles": {"seed": "replace_with_charles_seed", "min_price": 60},
    "diana": {"seed": "replace_with_diana_seed", "min_price": 75},
    "ean": {"seed": "replace_with_ean_seed", "min_price": 85},
    "fabian": {"seed": "replace_with_fabian_seed", "min_price": 65},
}


agents = []
for name, info in AGENT_INFO.items():
    agent = Agent(name=name, seed=info["seed"])
    print(f"{agent.name} address: {agent.address}")
    agent.storage.set("min_price", info["min_price"])
    agent.include(proto)
    agents.append(agent)

bureau = Bureau(port=8001, endpoint="http://localhost:8001/submit")
for agent in agents:
    bureau.add(agent)

if __name__ == "__main__":
    bureau.run()
