import base64
import hashlib
import struct
from secrets import token_bytes

import bech32
import ecdsa
from ecdsa.util import sigencode_string_canonize

from uagents_core.config import AGENT_ADDRESS_LENGTH, AGENT_PREFIX

USER_PREFIX = "user"
SHA_LENGTH = 256


def _decode_bech32(value: str) -> tuple[str, bytes]:
    prefix, data_base5 = bech32.bech32_decode(value)
    if not data_base5 or not prefix:
        raise ValueError("Unable to decode value")
    converted = bech32.convertbits(data_base5, 5, 8, False)
    if not converted:
        raise ValueError("Unable to convert value")
    return prefix, bytes(converted)


def _encode_bech32(prefix: str, value: bytes) -> str:
    value_base5 = bech32.convertbits(value, 8, 5)
    if not value_base5:
        raise ValueError("Unable to convert value")
    return bech32.bech32_encode(prefix, value_base5)


def is_user_address(address: str) -> bool:
    return address[0 : len(USER_PREFIX)] == USER_PREFIX


def generate_user_address() -> str:
    return _encode_bech32(prefix=USER_PREFIX, value=token_bytes(32))


def _key_derivation_hash(prefix: str, index: int) -> bytes:
    hasher = hashlib.sha256()
    hasher.update(prefix.encode())
    assert 0 <= index < SHA_LENGTH
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


def encode_length_prefixed(value: str | int | bytes) -> bytes:
    if isinstance(value, str):
        encoded = value.encode()
    elif isinstance(value, int):
        encoded = struct.pack(">Q", value)
    elif isinstance(value, bytes):
        encoded = value
    else:
        raise AssertionError()

    length = len(encoded)
    prefix = struct.pack(">Q", length)

    return prefix + encoded


class Identity:
    """An identity is a cryptographic keypair that can be used to sign messages."""

    def __init__(self, signing_key: ecdsa.SigningKey):
        """Create a new identity from a signing key."""
        self._sk = signing_key

        # build the address
        pub_key_bytes = self._sk.get_verifying_key().to_string("compressed")  # type: ignore
        self._address = _encode_bech32("agent", pub_key_bytes)
        self._pub_key = pub_key_bytes.hex()

    @staticmethod
    def from_seed(seed: str, index: int) -> "Identity":
        """Create a new identity from a seed and index."""
        key = derive_key_from_seed(seed, "agent", index)
        signing_key = ecdsa.SigningKey.from_string(
            key,
            curve=ecdsa.SECP256k1,
            hashfunc=hashlib.sha256,
        )
        return Identity(signing_key)

    @staticmethod
    def generate() -> "Identity":
        """Generate a random new identity."""
        signing_key = ecdsa.SigningKey.generate(
            curve=ecdsa.SECP256k1,
            hashfunc=hashlib.sha256,
        )
        return Identity(signing_key)

    @staticmethod
    def from_string(private_key_hex: str) -> "Identity":
        """Create a new identity from a private key."""
        bytes_key = bytes.fromhex(private_key_hex)
        signing_key = ecdsa.SigningKey.from_string(
            bytes_key,
            curve=ecdsa.SECP256k1,
            hashfunc=hashlib.sha256,
        )

        return Identity(signing_key)

    # this is not the real private key but a signing key derived from the private key
    @property
    def private_key(self) -> str:
        """Property to access the private key of the identity."""
        return self._sk.to_string().hex()

    @property
    def address(self) -> str:
        """Property to access the address of the identity."""
        return self._address

    @property
    def pub_key(self) -> str:
        return self._pub_key

    def sign(self, data: bytes) -> str:
        """Sign the provided data."""
        return _encode_bech32("sig", self._sk.sign(data))

    def sign_b64(self, data: bytes) -> str:
        raw_signature = bytes(self._sk.sign(data, sigencode=sigencode_string_canonize))
        return base64.b64encode(raw_signature).decode()

    def sign_digest(self, digest: bytes) -> str:
        """Sign the provided digest."""
        return _encode_bech32("sig", self._sk.sign_digest(digest))

    @staticmethod
    def verify_digest(address: str, digest: bytes, signature: str) -> bool:
        """Verify that the signature is correct for the provided signer address and digest."""
        pk_prefix, pk_data = _decode_bech32(address)
        sig_prefix, sig_data = _decode_bech32(signature)

        if pk_prefix != "agent":
            raise ValueError("Unable to decode agent address")

        if sig_prefix != "sig":
            raise ValueError("Unable to decode signature")

        # build the verifying key
        verifying_key = ecdsa.VerifyingKey.from_string(pk_data, curve=ecdsa.SECP256k1)

        return verifying_key.verify_digest(sig_data, digest)


def is_valid_address(address: str) -> bool:
    """
    Check if the given string is a valid address.

    Args:
        address (str): The address to be checked.

    Returns:
        bool: True if the address is valid; False otherwise.
    """
    return is_user_address(address) or (
        len(address) == AGENT_ADDRESS_LENGTH and address.startswith(AGENT_PREFIX)
    )


def parse_identifier(identifier: str) -> tuple[str, str, str]:
    """
    Parse an agent identifier string into prefix, name, and address.

    Args:
        identifier (str): The identifier string to be parsed.

    Returns:
        tuple[str, str, str]: A Tuple containing the prefix, name, and address as strings.
    """
    prefix = ""
    name = ""
    address = ""

    if "://" in identifier:
        prefix, identifier = identifier.split("://", 1)

    if "/" in identifier:
        name, identifier = identifier.split("/", 1)

    if is_valid_address(identifier):
        address = identifier
    else:
        name = identifier

    return prefix, name, address
