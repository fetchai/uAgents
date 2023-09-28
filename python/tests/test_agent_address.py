import unittest

from uagents import Agent
from uagents.crypto import Identity

test_prefix = "test-agent://"


class TestAgentAdress(unittest.TestCase):
    def test_agent_from_seed(self):
        alice = Agent(name="alice", seed="alice recovery password")
        bob = Agent(name="bob", seed="bob recovery password")

        alice_target_address = Identity.from_seed("alice recovery password", 0).address
        bob_target_address = Identity.from_seed("bob recovery password", 0).address

        self.assertEqual(
            alice.address == test_prefix + alice_target_address,
            True,
            "Alice's address does not match",
        )
        self.assertEqual(
            bob.address == test_prefix + bob_target_address,
            True,
            "Bobs's address does not match",
        )

    def test_agent_generate(self):
        alice = Agent(name="alice")

        self.assertEqual(alice.address[-65:-60] == "agent", True)
        self.assertEqual(len(alice.address) == 65 + len(test_prefix), True)


if __name__ == "__main__":
    unittest.main()
