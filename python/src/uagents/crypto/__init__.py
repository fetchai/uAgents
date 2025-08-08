import base64
import hashlib
import json

from uagents_core.identity import Identity, encode_length_prefixed


def sign_registration(
    identity: Identity,
    contract_address: str,
    timestamp: int,
    wallet_address: str,
) -> str:
    """Sign the registration data for the Almanac contract."""
    hasher = hashlib.sha256()
    hasher.update(encode_length_prefixed(contract_address))
    hasher.update(encode_length_prefixed(identity.address))
    hasher.update(encode_length_prefixed(timestamp))
    hasher.update(encode_length_prefixed(wallet_address))
    return identity.sign_digest(hasher.digest())


def sign_arbitrary(identity: Identity, data: bytes) -> tuple[str, str]:
    """
    Sign arbitrary data with the given identity.

    Only used for wallet messaging.
    """
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
                    "signer": identity.address,
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
    signature = identity.sign_b64(raw_sign_doc)
    enc_sign_doc = base64.b64encode(raw_sign_doc).decode()

    return enc_sign_doc, signature
