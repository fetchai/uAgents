from uagents import Agent

from protocols import host_proto

agent = Agent(name="menu-host-staging", mailbox=True, agentverse="https://staging.agentverse.ai")
agent.include(host_proto)

if __name__ == "__main__":
    agent.run()
