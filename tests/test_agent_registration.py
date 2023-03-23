# pylint: disable=protected-access
import unittest

from uagents import Agent
from uagents.setup import fund_agent_if_low


class TestVerify(unittest.TestCase):
    def test_agent_registration(self):
        agent = Agent(name="alice")

        reg_fee = "500000000000000000atestfet"

        fund_agent_if_low(agent.wallet.address())

        sequence = agent.get_registration_sequence()

        signature = agent._identity.sign_registration(
            agent._reg_contract.address, agent.get_registration_sequence()
        )

        msg = {
            "register": {
                "record": {
                    "service": {
                        "protocols": [],
                        "endpoints": [
                            {"url": "http://127.0.0.1:8000/submit", "weight": 1}
                        ],
                    }
                },
                "signature": signature,
                "sequence": sequence,
                "agent_address": agent.address,
            }
        }

        transaction = agent._reg_contract.execute(msg, agent.wallet, funds=reg_fee)
        transaction.wait_to_complete()

        query_msg = {"query_records": {"agent_address": agent.address}}
        response = agent._reg_contract.query(query_msg)

        is_registered = False
        if response["record"] != []:
            is_registered = True

        self.assertEqual(is_registered, True, "Registration failed")


if __name__ == "__main__":
    unittest.main()
