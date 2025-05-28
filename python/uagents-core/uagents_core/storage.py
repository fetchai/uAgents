import base64
import struct
from datetime import datetime
from secrets import token_bytes
from typing import Optional

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
    def __init__(
        self,
        identity: Optional[Identity] = None,
        storage_url: Optional[str] = None,
        api_token: Optional[str] = None,
    ):
        self.identity = identity
        self.api_token = api_token
        self.storage_url = storage_url or AgentverseConfig().storage_endpoint

    def _make_attestation(self) -> str:
        nonce = token_bytes(32)
        now = datetime.now()
        return compute_attestation(self.identity, now, 3600, nonce)

    def _get_auth_header(self) -> dict:
        if self.api_token:
            return {"Authorization": f"Bearer {self.api_token}"}
        elif self.identity:
            return {"Authorization": f"Agent {self._make_attestation()}"}
        else:
            raise RuntimeError("No identity or API token available for authentication")

    def upload(
        self, asset_id: str, content: bytes, mime_type: str = "text/plain"
    ) -> dict:
        url = f"{self.storage_url}/assets/{asset_id}/contents/"
        headers = self._get_auth_header()
        headers["Content-Type"] = "application/json"
        payload = {
            "contents": base64.b64encode(content).decode(),
            "mime_type": mime_type,
        }
        response = requests.put(url, json=payload, headers=headers)
        if response.status_code != 200:
            raise RuntimeError(
                f"Upload failed: {response.status_code}, {response.text}"
            )

        return response.json()

    def download(self, asset_id: str) -> dict:
        url = f"{self.storage_url}/assets/{asset_id}/contents/"
        headers = self._get_auth_header()

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise RuntimeError(
                f"Download failed: {response.status_code}, {response.text}"
            )

        return response.json()

    def create_asset(
        self,
        name: str,
        content: bytes,
        mime_type: str = "text/plain",
        lifetime_hours: int = 24,
    ) -> str:
        if not self.api_token:
            raise RuntimeError("API token required to create assets")
        url = f"{self.storage_url}/assets/"
        headers = self._get_auth_header()
        headers["Content-Type"] = "application/json"
        payload = {
            "name": name,
            "mime_type": mime_type,
            "contents": base64.b64encode(content).decode(),
            "lifetime_hours": lifetime_hours,
        }

        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 201:
            raise RuntimeError(
                f"Asset creation failed: {response.status_code}, {response.text}"
            )

        return response.json()["asset_id"]

    def set_permissions(
        self, asset_id: str, agent_address: str, read: bool = True, write: bool = True
    ):
        if not self.api_token:
            raise RuntimeError("API token required to set permissions")
        url = f"{self.storage_url}/assets/{asset_id}/permissions/"
        headers = self._get_auth_header()
        headers["Content-Type"] = "application/json"
        payload = {
            "agent_address": agent_address,
            "read": read,
            "write": write,
        }

        response = requests.put(url, json=payload, headers=headers)
        if response.status_code != 200:
            raise RuntimeError(
                f"Set permissions failed: {response.status_code}, {response.text}"
            )

        return response.json()
