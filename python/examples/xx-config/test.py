from uagents import Agent
from uagents.agent import AgentConfig, Bureau
from uagents.config import load_config, load_configs

PATH = "/Users/florian/git/uAgents/python/examples/xx-config/my_config.yaml"

conf1 = load_config(PATH)  # type: dict
agent = Agent(**conf1)

conf2 = AgentConfig.from_file(PATH)  # type: AgentConfig
agent2 = conf2.create_agent()
# agent2 = Agent(**conf2.__dict__) # same as above

confs = load_configs(PATH)  # multiple configs in one file

bureau = Bureau()
for conf in confs:
    bureau.add(Agent(**conf))

bureau.run()

print("done")
