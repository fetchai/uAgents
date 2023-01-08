import unittest
import hashlib

from nexus import Agent
from nexus.setup import fund_agent_if_low
from nexus.network import get_ledger, get_reg_contract


class TestVerify(unittest.TestCase):
    def test_agent_registration(self):

        agent = Agent(
            name="alice",
            port=8000,
            seed="alice secret phrase",
            endpoint="http://127.0.0.1:8000/submit",
        )

        reg_fee = "500000000000000000atestfet"

        fund_agent_if_low(agent.wallet.address())

        sequence = agent.get_registration_sequence()

        almanac_contract = get_reg_contract()

        # pylint: disable=no-member
        signature = agent._identity.sign_registration(
            almanac_contract.address, agent.get_registration_sequence()
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

        almanac_contract.execute(msg, agent.wallet, funds=reg_fee).wait_to_complete()

        is_registered = agent.registration_status()
        self.assertEqual(is_registered, True, "Registration failed")


if __name__ == "__main__":
    unittest.main()
