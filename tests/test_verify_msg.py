import hashlib
import unittest

from nexus.agent import Agent
from nexus.crypto import Identity


def encode(message: str) -> bytes:
    hasher = hashlib.sha256()
    hasher.update(message.encode())
    return hasher.digest()


class TestVerify(unittest.TestCase):
    def test_verify_message(self):
        alice = Agent(name="alice", seed="alice recovery password")

        alice_msg = "hello there bob"
        encoded_msg = encode(alice_msg)

        signature = alice.sign_digest(encoded_msg)

        # Message signature can be verified using alice address
        result = Identity.verify_digest(alice.address, encoded_msg, signature)

        self.assertEqual(result, True, "Verification failed")


if __name__ == "__main__":
    unittest.main()
