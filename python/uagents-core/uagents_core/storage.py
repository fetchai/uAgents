import base64
import struct
from typing import Optional
from datetime import datetime
from secrets import token_bytes

import requests
from uagents_core.config import AgentverseConfig
from uagents_core.identity import Identity


def compute_attestation(
    identity: Identity, validity_start: datetime, validity_secs: int, nonce: bytes
) -> str:
    """
    Compute a valid agent attestation token for authentication.
    """
    assert len(nonce) == 32, "Nonce is of invalid length"

    valid_from = int(validity_start.timestamp())
    valid_to = valid_from + validity_secs

    public_key = bytes.fromhex(identity.pub_key)

    payload = public_key + struct.pack(">QQ", valid_from, valid_to) + nonce
    assert len(payload) == 81, "attestation payload is incorrect"

    signature = identity.sign(payload)
    attestation = f"attr:{base64.b64encode(payload).decode()}:{signature}"
    return attestation


class ExternalStorage:
    def __init__(self, identity: Identity, storage_url: Optional[str] = None):
        self.identity = identity
        self.storage_url = storage_url or AgentverseConfig().storage_endpoint

    def _make_attestation(self) -> str:
        nonce = token_bytes(32)
        now = datetime.utcnow()
        return compute_attestation(self.identity, now, 3600, nonce)

    def upload(self, asset_id: str, asset_content: str):
        url = f"{self.storage_url}/assets/{asset_id}/contents/"
        headers = {"Authorization": f"Agent {self._make_attestation()}"}
        payload = {
            "contents": base64.b64encode(asset_content.encode()).decode(),
            "mime_type": "text/plain",
        }

        response = requests.put(url, json=payload, headers=headers)
        if response.status_code != 200:
            raise RuntimeError(
                f"Upload failed: {response.status_code}, {response.text}"
            )
        return response

    def download(self, asset_id: str) -> str:
        url = f"{self.storage_url}/assets/{asset_id}/contents/"
        headers = {
            "Authorization": f"Agent {self._make_attestation()}",
            "accept": "text/plain",
        }

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise RuntimeError(
                f"Download failed: {response.status_code}, {response.text}"
            )

        return response
