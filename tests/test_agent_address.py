import unittest

from nexus import Agent


class TestAgentAdress(unittest.TestCase):
    def test_agent_from_seed(self):
        alice = Agent(name="alice", seed="alice recovery password")
        bob = Agent(name="bob", seed="bob recovery password")

        alice_target_address = (
            "agent1qg985el6kquqw3zdnq7tvpsz2n0srxa8e8eyp0nwpagp6yyg2ayus294dux"
        )
        bob_target_address = (
            "agent1qgqdlpds2w7rs032jgylcka8m5d663nvt6p5dmmffpmanljldchssyjhn9r"
        )

        self.assertEqual(
            alice.address == alice_target_address,
            True,
            "Alice's address does not match",
        )
        self.assertEqual(
            bob.address == bob_target_address, True, "Bobs's address does not match"
        )

    def test_agent_generate(self):
        alice = Agent(name="alice")

        self.assertEqual(alice.address[:5] == "agent", True)
        self.assertEqual(len(alice.address) == 65, True)


if __name__ == "__main__":
    unittest.main()
