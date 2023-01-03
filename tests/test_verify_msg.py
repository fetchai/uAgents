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

        signature = alice._identity._sk.sign_digest(encoded_msg).hex()

        # Message signature can be verified using alice address
        result = Identity.verify_digest(alice.address, encoded_msg, signature)

        self.assertEqual(result, True, "Verification failed")

    def test_verify_dart_digest(self):

        # Generate public key
        address = "agent1qf5gfqm48k9acegez3sg82ney2aa6l5fvpwh3n3z0ajh0nam3ssgwnn5me7"

        # Signature
        signature = "3e8a94a928f65f5bfdc29d7389e92e2a76d0aef341b968440736d5e983bf5c75c3a877bb7b7c2401b50d40094b9b26fa22cb842fe0ff0d3c2fe787c079671652"

        # Message
        dart_digest = "a29af8b704077d394a9756dc04f0bb5f1424fc391b3de91144d683c5893ca234"
        bytes_dart_digest = bytes.fromhex(dart_digest)

        result = Identity.verify_digest(address, bytes_dart_digest, signature)

        self.assertEqual(result, True, "Verification failed")


if __name__ == "__main__":
    unittest.main()
