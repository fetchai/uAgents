import unittest

from uagents import Agent

agents = [
    Agent(),
    Agent(mailbox="agent_mailbox_key@some_url"),
    Agent(mailbox={"agent_mailbox_key": "agent_mailbox_key", "base_url": "some_url"}),
    Agent(mailbox="agent_mailbox_key"),
    Agent(agentverse="agent_mailbox_key@some_url"),
    Agent(agentverse="agent_mailbox_key"),
    Agent(agentverse="http://some_url"),
    Agent(agentverse="wss://some_url"),
    Agent(agentverse="ws://some_url"),
    Agent(agentverse={"agent_mailbox_key": "agent_mailbox_key", "protocol": "wss"}),
    Agent(agentverse="https://staging.agentverse.ai"),
    Agent(agentverse={"base_url": "staging.agentverse.ai"}),
]

expected_configs = [
    {
        "base_url": "agentverse.ai",
        "protocol": "https",
        "http_prefix": "https",
    },
    {
        "base_url": "some_url",
        "protocol": "https",
        "http_prefix": "https",
    },
    {
        "base_url": "some_url",
        "protocol": "https",
        "http_prefix": "https",
    },
    {
        "base_url": "agentverse.ai",
        "protocol": "https",
        "http_prefix": "https",
    },
    {
        "base_url": "some_url",
        "protocol": "https",
        "http_prefix": "https",
    },
    {
        "base_url": "agentverse.ai",
        "protocol": "https",
        "http_prefix": "https",
    },
    {
        "base_url": "some_url",
        "protocol": "http",
        "http_prefix": "http",
    },
    {
        "base_url": "some_url",
        "protocol": "wss",
        "http_prefix": "https",
    },
    {
        "base_url": "some_url",
        "protocol": "ws",
        "http_prefix": "http",
    },
    {
        "base_url": "agentverse.ai",
        "protocol": "wss",
        "http_prefix": "https",
    },
    {
        "base_url": "staging.agentverse.ai",
        "protocol": "https",
        "http_prefix": "https",
    },
    {
        "base_url": "staging.agentverse.ai",
        "protocol": "https",
        "http_prefix": "https",
    },
]


class TestConfig(unittest.TestCase):
    def test_parse_agentverse_config(self):
        for agent, expected_config in zip(agents, expected_configs):  # noqa
            self.assertEqual(agent.agentverse.model_dump(), expected_config)
