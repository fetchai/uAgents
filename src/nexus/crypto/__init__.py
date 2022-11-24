import hashlib
import struct
from typing import Tuple, Union
import json
import os
from cosmpy.aerial.wallet import PrivateKey

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


file_path = os.path.dirname(os.path.realpath(__file__))
keys_path = os.path.join(file_path, "keys.json")


def load_wallet_keys() -> dict:
    if os.path.exists(keys_path):
        with open(keys_path, encoding="utf-8") as load_file:
            return json.load(load_file)
    return {}


def save_wallet_key(name: str, key: str):
    keys = load_wallet_keys()
    keys[name] = key
    with open(keys_path, "w", encoding="utf-8") as write_file:
        json.dump(keys, write_file, indent=4)


def query_wallet_key(name: str):
    keys = load_wallet_keys()
    if name in keys.keys():
        return keys[name]
    return ""


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

    @staticmethod  # hasla mas bonita nmms!!!!!
    def get_wallet_key(name: str) -> str:
        saved_key = query_wallet_key(name)
        if saved_key:
            return saved_key
        key = PrivateKey().private_key
        save_wallet_key(name, key)
        return key

    @property
    def address(self) -> str:
        return self._address

    def sign_digest(self, digest: bytes) -> str:
        return _encode_bech32("sig", self._sk.sign_digest(digest))

    def sign_registration(self, contract_address: str, sequence: int) -> str:
        hasher = hashlib.sha256()
        hasher.update(encode_length_prefixed(contract_address))
        hasher.update(encode_length_prefixed(self.address))
        hasher.update(encode_length_prefixed(sequence))
        return self.sign_digest(hasher.digest())

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
