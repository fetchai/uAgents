import asyncio
import logging
from datetime import datetime
from typing import Optional

import aiohttp
from aiohttp.client_exceptions import ClientConnectorError
from pydantic import UUID4, BaseModel, ValidationError

from uagents.config import MAILBOX_POLL_INTERVAL_SECONDS, AgentType, AgentverseConfig
from uagents.crypto import Identity, is_user_address
from uagents.dispatch import dispatcher
from uagents.envelope import Envelope
from uagents.models import Model
from uagents.types import AgentEndpoint
from uagents.utils import get_logger

logger = get_logger("mailbox")


class AgentverseConnectRequest(Model):
    user_token: str
    agent_type: AgentType


class ChallengeRequest(BaseModel):
    address: str


class ChallengeResponse(BaseModel):
    challenge: str


class RegistrationRequest(BaseModel):
    address: str
    challenge: str
    challenge_response: str
    agent_type: AgentType
    endpoints: Optional[list[AgentEndpoint]] = None
    agent_mailbox_key: Optional[str] = None


class RegistrationResponse(Model):
    access_token: Optional[str] = None
    expiry: Optional[str] = None


class StoredEnvelope(BaseModel):
    uuid: UUID4
    envelope: Envelope
    received_at: datetime
    expires_at: datetime


async def register_in_agentverse(
    request: AgentverseConnectRequest,
    identity: Identity,
    endpoints: list[AgentEndpoint],
    agentverse: AgentverseConfig,
) -> RegistrationResponse:
    """
    Registers agent in Agentverse
    """
    async with aiohttp.ClientSession() as session:
        # get challenge
        challenge_url = f"{agentverse.url}/v1/auth/challenge"
        challenge_request = ChallengeRequest(address=identity.address)
        logger.info("Requesting mailbox access challenge")
        async with session.post(
            challenge_url,
            data=challenge_request.model_dump_json(),
            headers={
                "content-type": "application/json",
                "Authorization": f"Bearer {request.user_token}",
            },
        ) as resp:
            resp.raise_for_status()
            challenge = ChallengeResponse.model_validate_json(await resp.text())

        # response to challenge with signature to get token
        prove_url = f"{agentverse.url}/v1/auth/register"
        if request.agent_type == "proxy":
            endpoints = [AgentEndpoint(url=f"{agentverse.url}/v1/proxy", weight=1)]
        async with session.post(
            prove_url,
            data=RegistrationRequest(
                address=identity.address,
                challenge=challenge.challenge,
                challenge_response=identity.sign(challenge.challenge.encode()),
                endpoints=endpoints,
                agent_type=request.agent_type,
            ).model_dump_json(),
            headers={
                "content-type": "application/json",
                "Authorization": f"Bearer {request.user_token}",
            },
        ) as resp:
            resp.raise_for_status()
            registration_response = RegistrationResponse.parse_raw(await resp.text())

    return registration_response


class MailboxClient:
    """Client for interacting with the Agentverse mailbox server."""

    def __init__(
        self, agentverse: AgentverseConfig, logger: Optional[logging.Logger] = None
    ):
        self._agentverse = agentverse
        self._poll_interval = MAILBOX_POLL_INTERVAL_SECONDS
        self._logger = logger or get_logger("mailbox")

    async def run(self):
        """
        Runs the mailbox client.
        """
        self._logger.info(f"Starting mailbox client for {self._agentverse.url}")
        while True:
            try:
                await self._check_mailbox()
                await asyncio.sleep(self._poll_interval)
            except ClientConnectorError:
                self._logger.exception("Failed to connect to mailbox server")

    async def _check_mailbox(self):
        """
        Retrieves envelopes from the mailbox server and processes them.
        """
        async with aiohttp.ClientSession() as session:
            # check the inbox for envelopes and handle them
            mailbox_url = f"{self._agentverse.url}/v1/mailbox"
            async with session.get(
                mailbox_url,
                headers={
                    "Authorization": f"token {self._agentverse.agent_mailbox_key}"
                },
            ) as resp:
                success = resp.status == 200
                if success:
                    items = (await resp.json())["items"]
                    for item in items:
                        stored_env = StoredEnvelope.model_validate(item)
                        await self._handle_envelope(stored_env)
                elif resp.status == 401:
                    self._logger.warning(
                        f"Access token expired: reconnect your agent at {self._agentverse.url}"
                    )
                else:
                    self._logger.exception(
                        f"Failed to retrieve messages: {resp.status}:{(await resp.text())}"
                    )

    async def _handle_envelope(self, stored_env: StoredEnvelope):
        """
        Handles an envelope received from the mailbox server.
        Dispatches the incoming messages and adds the envelope to the deletion queue.
        """
        try:
            env = Envelope.model_validate(stored_env.envelope)
        except ValidationError:
            self._logger.warning("Received invalid envelope")
            return

        if not is_user_address(env.sender):  # verify signature if sent from agent
            try:
                env.verify()
            except Exception as err:
                self._logger.warning(
                    "Received envelope that failed verification: %s", err
                )
                return

        if not dispatcher.contains(env.target):
            self._logger.warning("Received envelope for unrecognized address")
            return

        await dispatcher.dispatch_msg(
            env.sender,
            env.target,
            env.schema_digest,
            env.decode_payload(),
            env.session,
        )

        # delete envelope from server
        await self._delete_envelope(stored_env.uuid)

    async def _delete_envelope(self, uuid: UUID4):
        """
        Deletes envelope from the mailbox server.
        """
        try:
            async with aiohttp.ClientSession() as session:
                env_url = f"{self._agentverse.url}/v1/mailbox/{str(uuid)}"
                self._logger.debug(f"Deleting message: {str(uuid)}")
                async with session.delete(
                    env_url,
                    headers={
                        "Authorization": f"token {self._agentverse.agent_mailbox_key}"
                    },
                ) as resp:
                    if resp.status != 200:
                        self._logger.exception(
                            f"Failed to delete envelope from inbox: {(await resp.text())}"
                        )
        except ClientConnectorError as ex:
            self._logger.warning(f"Failed to connect to mailbox server: {ex}")
        except Exception as ex:
            self._logger.exception(
                f"Got exception while processing deletion queue: {ex}"
            )
