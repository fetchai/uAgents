import asyncio
import logging
from datetime import datetime, timezone
from secrets import token_bytes

import aiohttp
from aiohttp.client_exceptions import ClientConnectorError
from pydantic import UUID4, BaseModel, ValidationError
from uagents_core.config import AgentverseConfig
from uagents_core.envelope import Envelope
from uagents_core.identity import Identity, is_user_address
from uagents_core.models import Model
from uagents_core.registration import (
    ChallengeResponse,
    IdentityProof,
    RegistrationRequest,
)
from uagents_core.storage import compute_attestation
from uagents_core.types import AddressPrefix, AgentEndpoint, AgentType

from uagents.config import MAILBOX_POLL_INTERVAL_SECONDS
from uagents.dispatch import dispatcher
from uagents.utils import get_logger

logger = get_logger("mailbox")


class AgentverseConnectRequest(Model):
    user_token: str
    agent_type: AgentType
    endpoint: str | None = None
    team: str | None = None


class ChallengeProof(BaseModel):
    address: str
    challenge: str
    challenge_response: str


class ChallengeProofResponse(Model):
    access_token: str
    expiry: str


class RegistrationResponse(Model):
    success: bool
    detail: str | None = None


class AgentverseDisconnectRequest(Model):
    user_token: str
    team: str | None = None


class UnregistrationResponse(Model):
    success: bool
    detail: str | None = None


class StoredEnvelope(BaseModel):
    uuid: UUID4
    envelope: Envelope
    received_at: datetime
    expires_at: datetime


def is_mailbox_agent(
    endpoints: list[AgentEndpoint], agentverse: AgentverseConfig
) -> bool:
    """
    Check if the agent is a mailbox agent.

    Returns:
        bool: True if the agent is a mailbox agent, False otherwise.
    """
    return any(agentverse.mailbox_endpoint in ep.url for ep in endpoints)


def _get_headers(
    request: AgentverseConnectRequest | AgentverseDisconnectRequest,
) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {request.user_token}",
        "Content-Type": "application/json",
    }
    if request.team:
        headers["x-team"] = request.team
    return headers


async def register_in_agentverse(
    request: AgentverseConnectRequest,
    identity: Identity,
    prefix: AddressPrefix,
    agentverse: AgentverseConfig,
    agent_details: RegistrationRequest,
) -> RegistrationResponse:
    """
    Registers agent in Agentverse

    Args:
        request (AgentverseConnectRequest): Request object
        identity (Identity): Agent identity object
        prefix (AddressPrefix): Agent address prefix
            can be "agent" (mainnet) or "test-agent" (testnet)
        agentverse (AgentverseConfig): Agentverse configuration
        agent_details (RegistrationRequest | None): Agent details to register

    Returns:
        RegistrationResponse: Registration response object
    """
    async with aiohttp.ClientSession() as session:
        # get challenge
        challenge_url = f"{agentverse.identity_api}/{identity.address}/challenge"
        logger.debug("Requesting mailbox access challenge")
        async with session.get(
            challenge_url,
            headers=_get_headers(request),
        ) as resp:
            if resp.status == 200:
                logger.debug("Received challenge from Agentverse")
                challenge = ChallengeResponse.model_validate_json(await resp.text())
            else:
                detail = (await resp.json())["detail"]
                return RegistrationResponse(success=False, detail=detail)

        # prove identity to agentverse
        logger.debug("Proving mailbox access challenge")
        identity_proof = IdentityProof(
            address=identity.address,
            challenge=challenge.challenge,
            challenge_response=identity.sign(challenge.challenge.encode()),
        )
        async with session.post(
            url=agentverse.identity_api,
            data=identity_proof.model_dump_json(),
            headers=_get_headers(request),
        ) as resp:
            if resp.status == 200:
                logger.debug("Successfully proved identity to Agentverse")
            else:
                detail = (await resp.json())["detail"]
                return RegistrationResponse(success=False, detail=detail)

        # register agent details in agentverse
        logger.debug("Registering agent in Agentverse")
        async with session.post(
            url=agentverse.agents_api,
            data=agent_details.model_dump_json(),
            headers=_get_headers(request),
        ) as resp:
            if resp.status == 200:
                logger.info(
                    f"Successfully registered as {request.agent_type} agent in Agentverse"
                )
                return RegistrationResponse(success=True)

            detail = (await resp.json())["detail"]
            return RegistrationResponse(success=False, detail=detail)


async def unregister_in_agentverse(
    request: AgentverseDisconnectRequest,
    agent_address: str,
    agentverse: AgentverseConfig,
) -> UnregistrationResponse:
    """
    Unregisters agent in Agentverse

    Args:
        request (AgentverseDisconnectRequest): Request object
        agent_address (str): The agent's address
        agentverse (AgentverseConfig): Agentverse configuration

    Returns:
        UnregistrationResponse: Unregistration response object
    """
    async with (
        aiohttp.ClientSession() as session,
        session.delete(
            f"{agentverse.agents_api}/{agent_address}",
            headers=_get_headers(request),
        ) as resp,
    ):
        if resp.status == 200:
            logger.info("Successfully unregistered from Agentverse")
            return UnregistrationResponse(success=True)

        detail = (await resp.json())["detail"]
        return UnregistrationResponse(success=False, detail=detail)


class MailboxClient:
    """Client for interacting with the Agentverse mailbox server."""

    def __init__(
        self,
        identity: Identity,
        agentverse: AgentverseConfig,
        logger: logging.Logger | None = None,
    ):
        self._identity = identity
        self._agentverse = agentverse
        self._attestation: str | None = None
        self._attestation_expiry: int = 0
        self._poll_interval = MAILBOX_POLL_INTERVAL_SECONDS
        self._attestation_validity_secs = int(self._poll_interval * 1000)
        self._logger = logger or get_logger("mailbox")
        self._missing_mailbox_warning_logged = False

    async def run(self):
        """Runs the mailbox client."""
        self._logger.info(f"Starting mailbox client for {self._agentverse.url}")
        loop = asyncio.get_event_loop()
        loop.create_task(self._check_mailbox_loop())

    async def _check_mailbox_loop(self):
        """Retrieves envelopes from the mailbox server and processes them."""
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    agents_url = self._agentverse.agents_api
                    async with session.get(
                        f"{agents_url}/{self._identity.address}/mailbox",
                        headers={
                            "Authorization": f"Agent {self.attestation}",
                        },
                    ) as resp:
                        success = resp.status == 200
                        if success:
                            items = await resp.json()
                            for item in items:
                                stored_env = StoredEnvelope.model_validate(item)
                                await self._handle_envelope(stored_env)
                        elif resp.status == 404:
                            if not self._missing_mailbox_warning_logged:
                                self._logger.warning(
                                    "Agent mailbox not found: create one using the agent inspector"
                                )
                                self._missing_mailbox_warning_logged = True
                        else:
                            self._logger.error(
                                f"Failed to retrieve messages: {resp.status}:{(await resp.text())}"
                            )
            except (ClientConnectorError, asyncio.TimeoutError) as ex:
                self._logger.warning(f"Failed to connect to mailbox server: {ex}")

            except Exception as ex:
                self._logger.exception(f"Got exception while checking mailbox: {ex}")

            await asyncio.sleep(self._poll_interval)

    async def _handle_envelope(self, stored_env: StoredEnvelope):
        """
        Handles an envelope received from the mailbox server.
        Dispatches the incoming messages and adds the envelope to the deletion queue.

        Args:
            stored_env (StoredEnvelope): Envelope to handle
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
            sender=env.sender,
            destination=env.target,
            schema_digest=env.schema_digest,
            message=env.decode_payload(),
            session=env.session,
        )

        # delete envelope from server
        await self._delete_envelope(stored_env.uuid)

    async def _delete_envelope(self, uuid: UUID4):
        """
        Deletes envelope from the mailbox server.

        Args:
            uuid (UUID4): UUID of the envelope to delete
        """
        try:
            async with aiohttp.ClientSession() as session:
                agents_url = self._agentverse.agents_api
                self._logger.debug(f"Deleting message: {str(uuid)}")
                async with session.delete(
                    f"{agents_url}/{self._identity.address}/mailbox/{str(uuid)}",
                    headers={
                        "Authorization": f"Agent {self.attestation}",
                    },
                ) as resp:
                    if resp.status >= 300:
                        self._logger.exception(
                            f"Failed to delete envelope from inbox: {(await resp.text())}"
                        )
        except ClientConnectorError as ex:
            self._logger.warning(f"Failed to connect to mailbox server: {ex}")
        except Exception as ex:
            self._logger.exception(f"Got exception while deleting message: {ex}")

    @property
    def attestation(self) -> str:
        """
        Creates and returns an attestation for the mailbox server.
        """
        if self._attestation_expiry - datetime.now(timezone.utc).timestamp() < 10:
            now = datetime.now(timezone.utc)
            self._attestation = compute_attestation(
                identity=self._identity,
                validity_start=now,
                validity_secs=self._attestation_validity_secs,
                nonce=token_bytes(nbytes=32),
            )
            self._attestation_expiry = (
                int(now.timestamp()) + self._attestation_validity_secs
            )

        return self._attestation
