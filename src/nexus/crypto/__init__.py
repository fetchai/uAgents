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


class Identity:
    def __init__(self, signing_key: ecdsa.SigningKey):
        self._sk = signing_key

        # build the address
        pub_key_bytes = self._sk.get_verifying_key().to_string(encoding="compressed")
        self._address = _encode_bech32("agent", pub_key_bytes)

    @staticmethod
    def from_seed(seed: str) -> 'Identity':
        h = hashlib.sha256()
        h.update(seed.encode())
        pk = h.digest()

        sk = ecdsa.SigningKey.from_string(pk, curve=ecdsa.SECP256k1)
        return Identity(sk)

    @staticmethod
    def generate() -> 'Identity':
        sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        return Identity(sk)

    @property
    def address(self) -> str:
        return self._address

    def sign_digest(self, digest: bytes) -> str:
        return _encode_bech32("sig", self._sk.sign_digest(digest))

    @staticmethod
    def verify_digest(pk: str, digest: bytes, sig: str) -> bool:
        pk_prefix, pk_data = _decode_bech32(pk)

        if pk_prefix != 'agent':
            raise ValueError('Unable to decode agent address')

        sig_prefix, sig_data = _decode_bech32(sig)

        if sig_prefix != 'sig':
            raise ValueError('Unable to decode signature')

        # build the verifying key
        vk = ecdsa.VerifyingKey.from_string(pk_data, curve=ecdsa.SECP256k1)

        try:
            result = vk.verify_digest(sig_data, digest)
        except ecdsa.keys.BadSignatureError:
            return False

        return result
