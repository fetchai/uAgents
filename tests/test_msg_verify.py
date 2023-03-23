import asyncio
import hashlib
import unittest

from uagents import Agent
from uagents.crypto import Identity


def encode(message: str) -> bytes:
    hasher = hashlib.sha256()
    hasher.update(message.encode())
    return hasher.digest()


class TestVerify(unittest.TestCase):
    def test_sign_and_verify_message(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        alice = Agent(name="alice", seed="alice recovery password")

        alice_msg = "hello there bob"
        encoded_msg = encode(alice_msg)

        signature = alice.sign_digest(encoded_msg)

        # Message signature can be verified using alice address
        result = Identity.verify_digest(alice.address, encoded_msg, signature)

        self.assertEqual(result, True, "Verification failed")

    def test_verify_dart_digest(self):
        # Generate public key
        address = "agent1qf5gfqm48k9acegez3sg82ney2aa6l5fvpwh3n3z0ajh0nam3ssgwnn5me7"

        # Signature
        signature = "sig1qyvn5fjzrhjzqcmj2gfg4us6xj00gvscs4u9uqxy6wpvp9agxjf723eh5l6w878p67lycgd3fz77zr3h0q6mrheg48e35zsvv0rm2tsuvyn3l"  # pylint: disable=line-too-long

        # Message
        dart_digest = "a29af8b704077d394a9756dc04f0bb5f1424fc391b3de91144d683c5893ca234"
        bytes_dart_digest = bytes.fromhex(dart_digest)

        result = Identity.verify_digest(address, bytes_dart_digest, signature)

        self.assertEqual(result, True, "Verification failed")


if __name__ == "__main__":
    unittest.main()
