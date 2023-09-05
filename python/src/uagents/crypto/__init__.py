import hashlib
import struct
from secrets import token_bytes
from typing import Tuple, Union
import json
import base64

import bech32
import ecdsa
from ecdsa.util import sigencode_string_canonize

from uagents.config import USER_PREFIX


def _decode_bech32(value: str) -> Tuple[str, bytes]:
    prefix, data_base5 = bech32.bech32_decode(value)
    data = bytes(bech32.convertbits(data_base5, 5, 8, False))
    return prefix, data


def _encode_bech32(prefix: str, value: bytes) -> str:
    value_base5 = bech32.convertbits(value, 8, 5)
    return bech32.bech32_encode(prefix, value_base5)


def generate_user_address() -> str:
    return _encode_bech32(USER_PREFIX, token_bytes(32))


def is_user_address(address: str) -> bool:
    return address[0 : len(USER_PREFIX)] == USER_PREFIX


def _key_derivation_hash(prefix: str, index: int) -> bytes:
    hasher = hashlib.sha256()
    hasher.update(prefix.encode())
    assert 0 <= index < 256
    hasher.update(bytes([index]))
    return hasher.digest()


def _seed_hash(seed: str) -> bytes:
    hasher = hashlib.sha256()
    hasher.update(seed.encode())
    return hasher.digest()


def derive_key_from_seed(seed, prefix, index) -> bytes:
    hasher = hashlib.sha256()
    hasher.update(_key_derivation_hash(prefix, index))
    hasher.update(_seed_hash(seed))
    return hasher.digest()


def encode_length_prefixed(value: Union[str, int, bytes]) -> bytes:
    if isinstance(value, str):
        encoded = value.encode()
    elif isinstance(value, int):
        encoded = struct.pack(">Q", value)
    elif isinstance(value, bytes):
        encoded = value
    else:
        assert False

    length = len(encoded)
    prefix = struct.pack(">Q", length)

    return prefix + encoded


class Identity:
    """
    An identity is a cryptographic keypair that can be used to sign messages.
    """

    def __init__(self, signing_key: ecdsa.SigningKey):
        """
        Create a new identity from a signing key.
        """
        self._sk = signing_key

        # build the address
        pub_key_bytes = self._sk.get_verifying_key().to_string(encoding="compressed")
        self._address = _encode_bech32("agent", pub_key_bytes)
        self._pub_key = pub_key_bytes.hex()

    @staticmethod
    def from_seed(seed: str, index: int) -> "Identity":
        """
        Create a new identity from a seed and index.
        """
        key = derive_key_from_seed(seed, "agent", index)
        signing_key = ecdsa.SigningKey.from_string(
            key, curve=ecdsa.SECP256k1, hashfunc=hashlib.sha256
        )
        return Identity(signing_key)

    @staticmethod
    def generate() -> "Identity":
        """
        Generate a random new identity.
        """
        signing_key = ecdsa.SigningKey.generate(
            curve=ecdsa.SECP256k1, hashfunc=hashlib.sha256
        )
        return Identity(signing_key)

    @staticmethod
    def from_string(private_key_hex: str) -> "Identity":
        """
        Create a new identity from a private key.
        """
        bytes_key = bytes.fromhex(private_key_hex)
        signing_key = ecdsa.SigningKey.from_string(
            bytes_key, curve=ecdsa.SECP256k1, hashfunc=hashlib.sha256
        )

        return Identity(signing_key)

    @property
    def private_key(self) -> str:
        """
        Property to access the private key of the identity.
        """
        return self._sk.to_string().hex()

    @property
    def address(self) -> str:
        """
        Property to access the address of the identity.
        """
        return self._address

    @property
    def pub_key(self) -> str:
        return self._pub_key

    def sign(self, data: bytes) -> str:
        """
        Sign the provided data.
        """
        return _encode_bech32("sig", self._sk.sign(data))

    def sign_b64(self, data: bytes) -> str:
        raw_signature = bytes(self._sk.sign(data, sigencode=sigencode_string_canonize))
        return base64.b64encode(raw_signature).decode()

    def sign_digest(self, digest: bytes) -> str:
        """
        Sign the provided digest.
        """
        return _encode_bech32("sig", self._sk.sign_digest(digest))

    def sign_registration(self, contract_address: str, sequence: int) -> str:
        """
        Sign the registration data for the Almanac contract.
        """
        hasher = hashlib.sha256()
        hasher.update(encode_length_prefixed(contract_address))
        hasher.update(encode_length_prefixed(self.address))
        hasher.update(encode_length_prefixed(sequence))
        return self.sign_digest(hasher.digest())

    def sign_arbitrary(self, data: bytes) -> Tuple[str, str]:
        # create the sign doc
        sign_doc = {
            "chain_id": "",
            "account_number": "0",
            "sequence": "0",
            "fee": {
                "gas": "0",
                "amount": [],
            },
            "msgs": [
                {
                    "type": "sign/MsgSignData",
                    "value": {
                        "signer": self.address,
                        "data": base64.b64encode(data).decode(),
                    },
                },
            ],
            "memo": "",
        }

        raw_sign_doc = json.dumps(
            sign_doc, sort_keys=True, separators=(",", ":")
        ).encode()
        signature = self.sign_b64(raw_sign_doc)
        enc_sign_doc = base64.b64encode(raw_sign_doc).decode()

        return enc_sign_doc, signature

    @staticmethod
    def verify_digest(address: str, digest: bytes, signature: str) -> bool:
        """
        Verify that the signature is correct for the provided signer address and digest.
        """
        pk_prefix, pk_data = _decode_bech32(address)
        sig_prefix, sig_data = _decode_bech32(signature)

        if pk_prefix != "agent":
            raise ValueError("Unable to decode agent address")

        if sig_prefix != "sig":
            raise ValueError("Unable to decode signature")

        # build the verifying key
        verifying_key = ecdsa.VerifyingKey.from_string(pk_data, curve=ecdsa.SECP256k1)

        try:
            result = verifying_key.verify_digest(sig_data, digest)
        except ecdsa.keys.BadSignatureError:
            return False

        return result
