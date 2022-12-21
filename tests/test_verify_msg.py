import hashlib
import unittest

from nexus import Agent
from nexus.crypto import Identity


def encode(message: str) -> bytes:
    hasher = hashlib.sha256()
    hasher.update(message.encode())
    return hasher.digest()


class TestVerify(unittest.TestCase):        
    def test_sign_and_verify_message(self):
        alice = Agent(name="alice", seed="alice recovery password")

        alice_msg = "hello there bob"
        encoded_msg = encode(alice_msg)

        signature = list(alice._identity._sk.sign_digest(encoded_msg))

        # Message signature can be verified using alice address
        result = Identity.verify_digest(alice.address, encoded_msg, signature)

        self.assertEqual(result, True, "Verification failed")

    def test_verify_dart_digest(self):

        # Generate public key
        address = "agent1qf5gfqm48k9acegez3sg82ney2aa6l5fvpwh3n3z0ajh0nam3ssgwnn5me7"

        # Signature
        signature = [61, 145, 82, 16, 168, 165, 33, 152, 210, 139, 178, 105, 237, 134, 230, 77, 6, 210, 150, 252, 47, 188, 2, 149, 93, 12, 116, 140, 120, 63, 5, 207, 8, 203, 61, 35, 211, 253, 4, 162, 183, 76, 14, 247, 199, 109, 191, 95, 126, 220, 184, 137, 20, 248, 77, 24, 87, 50, 82, 215, 95, 252, 80, 196]

        # Message
        dart_digest = "a29af8b704077d394a9756dc04f0bb5f1424fc391b3de91144d683c5893ca234"
        bytes_dart_digest = bytes.fromhex(dart_digest)

        result = Identity.verify_digest(address, bytes_dart_digest, signature)

        self.assertEqual(result, True, "Verification failed")


if __name__ == "__main__":
    unittest.main()
