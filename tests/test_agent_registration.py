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

    def test_name_service_ownership(self):
        agent = Agent()
        fund_agent_if_low(agent.wallet.address())

        ownership_msg = agent._service_contract._get_ownership_msg(
            agent.name, str(agent.wallet.address())
        )

        transaction = agent._service_contract.execute(ownership_msg, agent.wallet)

        transaction.wait_to_complete()

        is_owner = agent._service_contract.is_owner(
            agent.name, str(agent.wallet.address())
        )

        self.assertEqual(is_owner, True, "Domain ownership failed")

    def test_name_service_failed_ownership(self):
        agent = Agent()

        is_owner = agent._service_contract.is_owner(
            agent.name, str(agent.wallet.address())
        )

        self.assertEqual(is_owner, False, "Agent shouldn't own any domain")

    def test_registration(self):
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

        agent._almanac_contract.execute(
            almanac_msg, agent.wallet, funds=reg_fee
        ).wait_to_complete()

        self.assertEqual(
            agent._almanac_contract.is_registered(agent.address),
            True,
            "Almanac registration failed",
        )

        is_name_available = agent._service_contract.is_name_available(agent.name)
        self.assertEqual(is_name_available, True, "Agent name should be available")

        is_owner = agent._service_contract.is_owner(
            agent.name, str(agent.wallet.address())
        )
        self.assertEqual(is_owner, False)

        ownership_msg = agent._service_contract._get_ownership_msg(
            agent.name, str(agent.wallet.address())
        )
        registration_msg = agent._service_contract._get_registration_msg(
            agent.name, agent.address
        )

        agent._service_contract.execute(ownership_msg, agent.wallet).wait_to_complete()
        agent._service_contract.execute(
            registration_msg, agent.wallet
        ).wait_to_complete()

        is_name_available = agent._service_contract.is_name_available(agent.name)
        self.assertEqual(is_name_available, False, "Agent name shouldn't be available")

        is_owner = agent._service_contract.is_owner(
            agent.name, str(agent.wallet.address())
        )
        self.assertEqual(is_owner, True, "Domain ownership failed")

        query_address = get_agent_address(agent.name)

        self.assertEqual(
            query_address == agent.address, True, "Service contract registration failed"
        )


if __name__ == "__main__":
    unittest.main()
