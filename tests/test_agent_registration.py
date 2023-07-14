# pylint: disable=protected-access
import unittest

from uagents import Agent
from uagents.setup import fund_agent_if_low
from uagents.resolver import get_agent_address
from uagents.config import (
    REGISTRATION_FEE,
    REGISTRATION_DENOM,
)


class TestRegistration(unittest.TestCase):
    def test_alamanc_registration(self):
        agent = Agent()

        reg_fee = f"{REGISTRATION_FEE}{REGISTRATION_DENOM}"

        fund_agent_if_low(agent.wallet.address())

        sequence = agent._almanac_contract.get_sequence(agent.address)

        signature = agent._identity.sign_registration(
            agent._almanac_contract.address, sequence
        )

        almanac_msg = agent._almanac_contract.get_registration_msg(
            {}, [], signature, agent.address
        )

        transaction = agent._almanac_contract.execute(
            almanac_msg, agent.wallet, funds=reg_fee
        )
        transaction.wait_to_complete()

        self.assertEqual(
            agent._almanac_contract.is_registered(agent.address),
            True,
            "Almanac registration failed",
        )

    def test_alamanc_failed_registration(self):
        agent = Agent()

        self.assertEqual(
            agent._almanac_contract.is_registered(agent.address),
            False,
            "Shouldn't be registered on alamanac",
        )

    def test_name_service_failed_ownership(self):
        agent = Agent()

        domain = "agent"

        is_owner = agent._service_contract.is_owner(
            agent.name, domain, str(agent.wallet.address())
        )

        self.assertEqual(is_owner, False, "Agent shouldn't own any domain")

    def test_registration(self):
        agent = Agent()

        domain = "agent"

        reg_fee = f"{REGISTRATION_FEE}{REGISTRATION_DENOM}"

        fund_agent_if_low(agent.wallet.address())

        sequence = agent._almanac_contract.get_sequence(agent.address)

        signature = agent._identity.sign_registration(
            agent._almanac_contract.address, sequence
        )

        almanac_msg = agent._almanac_contract.get_registration_msg(
            {}, [], signature, agent.address
        )

        agent._almanac_contract.execute(
            almanac_msg, agent.wallet, funds=reg_fee
        ).wait_to_complete()

        self.assertEqual(
            agent._almanac_contract.is_registered(agent.address),
            True,
            "Almanac registration failed",
        )

        is_name_available = agent._service_contract.is_name_available(
            agent.name, domain
        )
        self.assertEqual(is_name_available, True, "Agent name should be available")

        is_owner = agent._service_contract.is_owner(
            agent.name, domain, str(agent.wallet.address())
        )
        self.assertEqual(is_owner, False)

        registration_msg = agent._service_contract._get_registration_msg(
            agent.name, agent.address, domain
        )

        agent._service_contract.execute(
            registration_msg, agent.wallet
        ).wait_to_complete()

        is_name_available = agent._service_contract.is_name_available(
            agent.name, domain
        )
        self.assertEqual(is_name_available, False, "Agent name shouldn't be available")

        is_owner = agent._service_contract.is_owner(
            agent.name, domain, str(agent.wallet.address())
        )
        self.assertEqual(is_owner, True, "Domain ownership failed")

        query_address = get_agent_address(agent.name + "." + domain)

        self.assertEqual(
            query_address == agent.address, True, "Service contract registration failed"
        )


if __name__ == "__main__":
    unittest.main()
