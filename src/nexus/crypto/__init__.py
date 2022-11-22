import hashlib
from typing import Tuple

import bech32
import ecdsa


def _decode_bech32(value: str) -> Tuple[str, bytes]:
    prefix, data_base5 = bech32.bech32_decode(value)
    data = bytes(bech32.convertbits(data_base5, 5, 8, False))
    return prefix, data


def _encode_bech32(prefix: str, value: bytes) -> str:
    value_base5 = bech32.convertbits(value, 8, 5)
    return bech32.bech32_encode(prefix, value_base5)


def _key_derivation_hash(prefix: str, index: int) -> bytes:
    hasher = hashlib.sha256()
    hasher.update(prefix.encode())
    hasher.update(str(index).encode())
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


class Identity:
    def __init__(self, signing_key: ecdsa.SigningKey):
        self._sk = signing_key

        # build the address
        pub_key_bytes = self._sk.get_verifying_key().to_string(encoding="compressed")
        self._address = _encode_bech32("agent", pub_key_bytes)

    @staticmethod
    def from_seed(seed: str, index: int) -> "Identity":
        key = derive_key_from_seed(seed, "agent", index)
        signing_key = ecdsa.SigningKey.from_string(key, curve=ecdsa.SECP256k1)
        return Identity(signing_key)

    @staticmethod
    def generate() -> "Identity":
        signing_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        return Identity(signing_key)

    @property
    def address(self) -> str:
        return self._address

    def sign_digest(self, digest: bytes) -> str:
        return _encode_bech32("sig", self._sk.sign_digest(digest))

    @staticmethod
    def verify_digest(address: str, digest: bytes, signature: str) -> bool:

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
