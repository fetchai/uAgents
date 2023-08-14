import unittest

from uagents import Agent
from uagents.crypto import Identity


class TestAgentAdress(unittest.TestCase):
    def test_agent_from_seed(self):
        alice = Agent(name="alice", seed="alice recovery password")
        bob = Agent(name="bob", seed="bob recovery password")

        alice_target_address = Identity.from_seed("alice recovery password", 0).address
        bob_target_address = Identity.from_seed("bob recovery password", 0).address

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
