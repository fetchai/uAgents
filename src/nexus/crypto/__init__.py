import bech32
import ecdsa


class Identity:
    def __init__(self):
        self._sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)

        # build the address
        pub_key_bytes = self._sk.get_verifying_key().to_string(encoding='compressed')
        pub_key_base5 = bech32.convertbits(pub_key_bytes, 8, 5)
        self._address = bech32.bech32_encode('agent', pub_key_base5)

    @property
    def address(self) -> str:
        return self._address
