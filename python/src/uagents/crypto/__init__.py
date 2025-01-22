import base64
import json
from typing import Tuple

from uagents_core.crypto import Identity as BaseIdentity


class Identity(BaseIdentity):
    """An identity is a cryptographic keypair that can be used to sign messages."""

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
            sign_doc,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        signature = self.sign_b64(raw_sign_doc)
        enc_sign_doc = base64.b64encode(raw_sign_doc).decode()

        return enc_sign_doc, signature
