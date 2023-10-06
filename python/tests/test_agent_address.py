import unittest

from uagents import Agent
from uagents.crypto import Identity
from uagents.resolver import parse_identifier, is_valid_address, is_valid_prefix


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
            "test-agent://agent1qfl32tdwlyjatc7f9tjng6sm9y7yzapy6awx4h9rrwenputzmnv5g6skess",
            "agent://agent1qfl32tdwlyjatc7f9tjng6sm9y7yzapy6awx4h9rrwenputzmnv5g6skess",
            "test-agent://name/agent1qfl32tdwlyjatc7f9tjng6sm9y7yzapy6awx4h9rrwenputzmnv5g6skess",
            "name/agent1qfl32tdwlyjatc7f9tjng6sm9y7yzapy6awx4h9rrwenputzmnv5g6skess",
        ]

        for val in valid_addresses:
            prefix, name, address = parse_identifier(val)
            self.assertEqual(
                is_valid_address(address),
                True,
            )
            self.assertIn(name, {"name", ""})
            self.assertEqual(
                is_valid_prefix(prefix),
                True,
            )

    def test_extract_valid_name(self):
        valid_names = [
            "name.domain",
            "test-agent://name.domain",
            "agent://name.domain",
            "agent://name.domain/agent1qfl32tdwlyjatc7f9tjng6sm9y7yzapy6awx4h9rrwenputzmnv5g6skess",
            "name.domain/agent1qfl32tdwlyjatc7f9tjng6sm9y7yzapy6awx4h9rrwenputzmnv5g6skess",
        ]
        for val in valid_names:
            prefix, name, address = parse_identifier(val)
            self.assertEqual(name, "name.domain")
            self.assertIn(
                address,
                {
                    "agent1qfl32tdwlyjatc7f9tjng6sm9y7yzapy6awx4h9rrwenputzmnv5g6skess",
                    "",
                },
            )
            self.assertEqual(is_valid_prefix(prefix), True)

    def test_extract_invalid_address(self):
        invalid_addresses = [
            "p://other1qfl32tdwlyjatc7f9tjng6sm9y7yzapy6awx4h9rrwenputzmnv5g6skess",
            "prefix://myagent1qfl32tdwlyjatc7f9tjng6sm9y7yzapy6awx4h9rrwenputzmnv5g6skes",
            "other-prefix://address1qfl32tdwlyjatc7f9tjng6sm9y7yzapy6awx4h9rrwenputzmnv5g6skes",
            "prefix://name/alice1qfl32tdwlyjatc7f9t6sm9y7yzapy6awx4h9rrwenputzmnv5g6skess/name",
            "some-prefix://bobqfl32tdwlyjatc7f9tjng6sm9y7yzapy6awx4h9rrwenputzmnv5g6skess",
        ]

        for val in invalid_addresses:
            prefix, _, address = parse_identifier(val)
            self.assertEqual(is_valid_address(address), False)
            self.assertEqual(is_valid_prefix(prefix), False)


if __name__ == "__main__":
    unittest.main()
