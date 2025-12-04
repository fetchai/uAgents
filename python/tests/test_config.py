import unittest

from uagents_core.config import AgentverseConfig
from uagents_core.types import AgentEndpoint

from uagents import Agent

MAILBOX_ENDPOINT = AgentverseConfig().mailbox_endpoint
PROXY_ENDPOINT = AgentverseConfig().proxy_endpoint


agents = [
    Agent(),
    Agent(mailbox="agent_mailbox_key"),  # type: ignore  (backwards compatibility)
    Agent(agentverse="http://some_url", endpoint="http://some_url"),
    Agent(agentverse="https://staging.agentverse.ai"),
    Agent(agentverse={"base_url": "staging.agentverse.ai"}),
    Agent(mailbox=True),
    Agent(mailbox=True, endpoint="http://some_url"),
    Agent(proxy=True),
    Agent(proxy=True, endpoint="http://some_url"),
    Agent(mailbox=True, proxy=True),
]

expected_endpoints = [
    [],
    [AgentEndpoint(url=MAILBOX_ENDPOINT, weight=1)],
    [AgentEndpoint(url="http://some_url", weight=1)],
    [],
    [],
    [AgentEndpoint(url=MAILBOX_ENDPOINT, weight=1)],
    [AgentEndpoint(url="http://some_url", weight=1)],
    [AgentEndpoint(url=PROXY_ENDPOINT, weight=1)],
    [AgentEndpoint(url="http://some_url", weight=1)],
    [AgentEndpoint(url=MAILBOX_ENDPOINT, weight=1)],
]

expected_configs = [
    {
        "base_url": "agentverse.ai",
        "http_prefix": "https",
    },
    {
        "base_url": "agentverse.ai",
        "http_prefix": "https",
    },
    {
        "base_url": "some_url",
        "http_prefix": "http",
    },
    {
        "base_url": "staging.agentverse.ai",
        "http_prefix": "https",
    },
    {
        "base_url": "staging.agentverse.ai",
        "http_prefix": "https",
    },
    {
        "base_url": "agentverse.ai",
        "http_prefix": "https",
    },
    {
        "base_url": "agentverse.ai",
        "http_prefix": "https",
    },
    {
        "base_url": "agentverse.ai",
        "http_prefix": "https",
    },
    {
        "base_url": "agentverse.ai",
        "http_prefix": "https",
    },
    {
        "base_url": "agentverse.ai",
        "http_prefix": "https",
    },
]


class TestConfig(unittest.TestCase):
    def test_parse_agentverse_config(self):
        for agent, expected_config, endpoints, index in zip(  # noqa
            agents,
            expected_configs,
            expected_endpoints,
            range(len(agents)),
        ):
            self.assertEqual(
                agent.agentverse.model_dump(),
                expected_config,
                f"Failed on agent {index}",
            )
            self.assertEqual(agent._endpoints, endpoints, f"Failed on agent {index}")
