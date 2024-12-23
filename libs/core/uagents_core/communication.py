import base64
import hashlib
import json
import struct
from typing import Optional, Any
from uuid import uuid4, UUID
from dataclasses import dataclass

import requests
from pydantic import BaseModel, UUID4
import urllib.parse

from uagents_core.crypto import Identity
from uagents_core.config import DEFAULT_AGENTVERSE_URL, DEFAULT_ALMANAC_API_PATH
from uagents_core.utils import get_logger


JsonStr = str

logger = get_logger("uagents_core.communication")


class Envelope(BaseModel):
    version: int
    sender: str
    target: str
    session: UUID4
    schema_digest: str
    protocol_digest: str
    payload: Optional[str] = None
    expires: Optional[int] = None
    nonce: Optional[int] = None
    signature: Optional[str] = None

    def encode_payload(self, value: JsonStr):
        self.payload = base64.b64encode(value.encode()).decode()

    def decode_payload(self) -> str:
        if self.payload is None:
            return ""

        return base64.b64decode(self.payload).decode()

    def sign(self, identity: Identity):
        try:
            self.signature = identity.sign_digest(self._digest())
        except Exception as err:
            raise ValueError(f"Failed to sign envelope: {err}") from err

    def verify(self) -> bool:
        if self.signature is None:
            raise ValueError("Envelope signature is missing")
        return Identity.verify_digest(self.sender, self._digest(), self.signature)

    def _digest(self) -> bytes:
        hasher = hashlib.sha256()
        hasher.update(self.sender.encode())
        hasher.update(self.target.encode())
        hasher.update(str(self.session).encode())
        hasher.update(self.schema_digest.encode())
        if self.payload is not None:
            hasher.update(self.payload.encode())
        if self.expires is not None:
            hasher.update(struct.pack(">Q", self.expires))
        if self.nonce is not None:
            hasher.update(struct.pack(">Q", self.nonce))
        return hasher.digest()


def lookup_endpoint_for_agent(agent_address: str, *, agentverse_url: Optional[str] = None) -> str:
    agentverse_url = agentverse_url or DEFAULT_AGENTVERSE_URL
    almanac_api = urllib.parse.urljoin(agentverse_url, DEFAULT_ALMANAC_API_PATH)

    request_meta = {
        "agent_address": agent_address,
        "lookup_url": almanac_api,
    }
    logger.debug("looking up endpoint for agent", extra=request_meta)
    r = requests.get(f"{almanac_api}/agents/{agent_address}")
    r.raise_for_status()

    request_meta["response_status"] = r.status_code
    logger.info(
        "Got response looking up agent endpoint",
        extra=request_meta,
    )

    return r.json()["endpoints"][0]["url"]


def send_message_to_agent(
    sender: Identity,
    target: str,
    payload: Any,
    protocol_digest: str,
    model_digest: str,
    session: UUID = uuid4(),
    *,
    agentverse_url: Optional[str] = None,
):
    """
    Send a message to an agent.
    :param session: The unique identifier for the dialogue between two agents
    :param sender: The identity of the sender.
    :param target: The address of the target agent.
    :param protocol_digest: The digest of the protocol that is being used
    :param model_digest: The digest of the model that is being used
    :param payload: The payload of the message.
    :return:
    """
    json_payload = json.dumps(payload, separators=(",", ":"))

    env = Envelope(
        version=1,
        sender=sender.address,
        target=target,
        session=session,
        schema_digest=model_digest,
        protocol_digest=protocol_digest,
    )

    env.encode_payload(json_payload)
    env.sign(sender)

    logger.debug("Sending message to agent", extra={"envelope": env.model_dump()})

    # query the almanac to lookup the target agent
    endpoint = lookup_endpoint_for_agent(target, agentverse_url=agentverse_url)

    # send the envelope to the target agent
    request_meta = {"agent_address": target, "agent_endpoint": endpoint}
    logger.debug("Sending message to agent", extra=request_meta)
    r = requests.post(
        endpoint,
        headers={"content-type": "application/json"},
        data=env.model_dump_json(),
    )
    r.raise_for_status()
    logger.info("Sent message to agent", extra=request_meta)


@dataclass
class AgentMessage:
    # The address of the sender of the message.
    sender: str
    # The address of the target of the message.
    target: str
    # The payload of the message.
    payload: Any


def parse_message_from_agent(content: JsonStr) -> AgentMessage:
    """
    Parse a message from an agent.
    :param content: A string containing the JSON envelope.
    :return: An AgentMessage object.
    """

    env = Envelope.model_validate_json(content)

    if not env.verify():
        raise ValueError("Invalid envelope signature")

    json_payload = env.decode_payload()
    payload = json.loads(json_payload)

    return AgentMessage(sender=env.sender, target=env.target, payload=payload)
