# pylint: disable=protected-access
import unittest

from uagents import Agent
from uagents.setup import fund_agent_if_low
from uagents.resolver import get_agent_address
from uagents.network import get_name_service_contract


class TestRegistration(unittest.IsolatedAsyncioTestCase):
    async def test_almanac_registration(self):
        agent = Agent(endpoint=["http://localhost:8000/submit"])

        fund_agent_if_low(agent.wallet.address())

        await agent.register()

        self.assertEqual(
            agent._almanac_contract.is_registered(agent.address),
            True,
            "Almanac registration failed",
        )

    def test_almanac_failed_registration(self):
        agent = Agent()

        self.assertEqual(
            agent._almanac_contract.is_registered(agent.address),
            False,
            "Shouldn't be registered on almanac",
        )

    def test_name_service_failed_ownership(self):
        agent = Agent()

        domain = "agent"

        name_service_contract = get_name_service_contract(test=True)

        is_owner = name_service_contract.is_owner(
            agent.name, domain, str(agent.wallet.address())
        )

        self.assertEqual(is_owner, False, "Agent shouldn't own any domain")

    async def test_name_service_registration(self):
        agent = Agent(endpoint=["http://localhost:8000/submit"])

        domain = "agent"

        fund_agent_if_low(agent.wallet.address())

        await agent.register()

        self.assertEqual(
            agent._almanac_contract.is_registered(agent.address),
            True,
            "Almanac registration failed",
        )

        name_service_contract = get_name_service_contract(test=True)

        is_name_available = name_service_contract.is_name_available(agent.name, domain)
        self.assertEqual(is_name_available, True, "Agent name should be available")

        is_owner = name_service_contract.is_owner(
            agent.name, domain, str(agent.wallet.address())
        )
        self.assertEqual(is_owner, False)

        await name_service_contract.register(
            agent._ledger, agent.wallet, agent.address, agent.name, domain=domain
        )

        is_name_available = name_service_contract.is_name_available(agent.name, domain)
        self.assertEqual(is_name_available, False, "Agent name shouldn't be available")

        is_owner = name_service_contract.is_owner(
            agent.name, domain, str(agent.wallet.address())
        )
        self.assertEqual(is_owner, True, "Domain ownership failed")

        query_address = get_agent_address(agent.name + "." + domain, True)

        self.assertEqual(
            query_address == agent.address, True, "Service contract registration failed"
        )


if __name__ == "__main__":
    unittest.main()
