import unittest

from uagents import Agent
from uagents.crypto import Identity
from uagents.resolver import extract_agent_address


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

    def test_extract_valid_address(self):
        valid_addresses = [
            "agent1qfl32tdwlyjatc7f9tjng6sm9y7yzapy6awx4h9rrwenputzmnv5g6skess",
            "some-prefix://agent1qfl32tdwlyjatc7f9tjng6sm9y7yzapy6awx4h9rrwenputzmnv5g6skess",
            "other-prefix://agent1qfl32tdwlyjatc7f9tjng6sm9y7yzapy6awx4h9rrwenputzmnv5g6skess",
            "some-prefix://agent_name/agent1qfl32tdwlyjatc7f9tjng6sm9y7yzapy6awx4h9rrwenputzmnv5g6skess",
            "some-prefix://some_agent_name/agent1qfl32tdwlyjatc7f9tjng6sm9y7yzapy6awx4h9rrwenputzmnv5g6skess",
        ]

        for val in valid_addresses:
            self.assertEqual(
                extract_agent_address(val)
                == "agent1qfl32tdwlyjatc7f9tjng6sm9y7yzapy6awx4h9rrwenputzmnv5g6skess",
                True,
            )

    def test_extract_invalid_address(self):
        invalid_addresses = [
            "other1qfl32tdwlyjatc7f9tjng6sm9y7yzapy6awx4h9rrwenputzmnv5g6skess",
            "some-prefix:agent1qfl32tdwlyjatc7f9tjng6sm9y7yzapy6awx4h9rrwenputzmnv5g6skess",
            "other-prefix://agent1qfl32tdwlyjatc7f9tjng6sm9y7yzapy6awx4h9rrwenputzmnv5g6skes",
            "some-prefix://agent1qfl32tdwlyjatc7f9tjng6sm9y7yzapy6awx4h9rrwenputzmnv5g6skess/agent_name",
            "some-prefix::agent1qfl32tdwlyjatc7f9tjng6sm9y7yzapy6awx4h9rrwenputzmnv5g6skess",
        ]

        for val in invalid_addresses:
            self.assertEqual(extract_agent_address(val) == None, True)


if __name__ == "__main__":
    unittest.main()
