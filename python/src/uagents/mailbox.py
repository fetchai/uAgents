import asyncio
import logging
from datetime import datetime
from typing import Annotated, Literal, Optional

import aiohttp
from aiohttp.client_exceptions import ClientConnectorError
from pydantic import UUID4, BaseModel, StringConstraints, ValidationError

from uagents.config import MAILBOX_POLL_INTERVAL_SECONDS, AgentverseConfig
from uagents.crypto import Identity, is_user_address
from uagents.dispatch import dispatcher
from uagents.envelope import Envelope
from uagents.models import Model
from uagents.types import AgentEndpoint
from uagents.utils import get_logger

logger = get_logger("mailbox")


AgentType = Literal["mailbox", "proxy", "custom"]


class AgentverseConnectRequest(Model):
    user_token: str
    agent_type: AgentType


class ChallengeRequest(BaseModel):
    address: str


class ChallengeResponse(BaseModel):
    challenge: str


class ChallengeProof(BaseModel):
    address: str
    challenge: str
    challenge_response: str


class ChallengeProofResponse(Model):
    access_token: str
    expiry: str


class RegistrationRequest(BaseModel):
    address: str
    challenge: str
    challenge_response: str
    agent_type: AgentType
    endpoints: Optional[list[AgentEndpoint]] = None


class RegistrationResponse(Model):
    success: bool


class AgentUpdates(BaseModel):
    name: Annotated[str, StringConstraints(min_length=1, max_length=80)]
    readme: Optional[Annotated[str, StringConstraints(max_length=80000)]] = None
    avatar_url: Optional[Annotated[str, StringConstraints(max_length=4000)]] = None
    agent_type: Optional[AgentType] = "mailbox"


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
    return any([f"{agentverse.url}/v1/submit" in ep.url for ep in endpoints])


def is_proxy_agent(
    endpoints: list[AgentEndpoint], agentverse: AgentverseConfig
) -> bool:
    """
    Check if the agent is a proxy agent.

    Returns:
        bool: True if the agent is a proxy agent, False otherwise.
    """
    return any([f"{agentverse.url}/v1/proxy/submit" in ep.url for ep in endpoints])


async def register_in_agentverse(
    request: AgentverseConnectRequest,
    identity: Identity,
    endpoints: list[AgentEndpoint],
    agentverse: AgentverseConfig,
    agent_details: Optional[AgentUpdates] = None,
) -> RegistrationResponse:
    """
    Registers agent in Agentverse

    Args:
        request (AgentverseConnectRequest): Request object
        identity (Identity): Agent identity object
        endpoints (list[AgentEndpoint]): Endpoints of the agent
        agentverse (AgentverseConfig): Agentverse configuration

    Returns:
        RegistrationResponse: Registration
    """
    async with aiohttp.ClientSession() as session:
        # get challenge
        challenge_url = f"{agentverse.url}/v1/auth/challenge"
        challenge_request = ChallengeRequest(address=identity.address)
        logger.debug("Requesting mailbox access challenge")
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
        prove_url = f"{agentverse.url}/v1/agents"
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
            if resp.status == 409:
                logger.exception("Agent is already registered in Agentverse.")
                return RegistrationResponse(success=False)
            resp.raise_for_status()
            registration_response = RegistrationResponse.parse_raw(await resp.text())
            if registration_response.success:
                logger.info(
                    f"Successfully registered as {request.agent_type} agent in Agentverse"
                )

    if agent_details:
        await update_agent_details(
            request.user_token, identity.address, agent_details, agentverse
        )

    if request.agent_type == "mailbox" and not is_mailbox_agent(endpoints, agentverse):
        logger.exception(
            f"Agent endpoints {endpoints} do not match registered agent type: {request.agent_type}"
            f"Please restart agent with endpoint='{agentverse.url}/v1/submit'"
        )

    return registration_response


async def update_agent_details(
    user_token: str,
    agent_address: str,
    agent_details: AgentUpdates,
    agentverse: Optional[AgentverseConfig] = None,
):
    """
    Updates agent details in Agentverse.

    Args:
        user_token (str): User token
        agent_address (str): Agent address
        agent_details (AgentUpdates): Agent details
        agentverse (Optional[AgentverseConfig]): Agentverse configuration
    """
    agentverse = agentverse or AgentverseConfig()
    try:
        async with aiohttp.ClientSession() as session:
            update_url = f"{agentverse.url}/v1/agents/{agent_address}"
            async with session.put(
                update_url,
                data=agent_details.model_dump_json(),
                headers={
                    "Authorization": f"token {user_token}",
                },
            ) as resp:
                resp.raise_for_status()
                logger.info("Agent details updated in Agentverse")
    except Exception as ex:
        logger.warning(f"Failed to update agent details: {ex}")


class MailboxClient:
    """Client for interacting with the Agentverse mailbox server."""

    def __init__(
        self,
        identity: Identity,
        agentverse: AgentverseConfig,
        logger: Optional[logging.Logger] = None,
    ):
        self._identity = identity
        self._agentverse = agentverse
        self._access_token: Optional[str] = None
        self._poll_interval = MAILBOX_POLL_INTERVAL_SECONDS
        self._logger = logger or get_logger("mailbox")

    async def run(self):
        """
        Runs the mailbox client.
        """
        self._logger.info(f"Starting mailbox client for {self._agentverse.url}")
        loop = asyncio.get_event_loop()
        loop.create_task(self._check_mailbox_loop())

    async def _check_mailbox_loop(self):
        """
        Retrieves envelopes from the mailbox server and processes them.
        """
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    if self._access_token is None:
                        await self._get_access_token()
                    mailbox_url = f"{self._agentverse.url}/v1/mailbox"
                    async with session.get(
                        mailbox_url,
                        headers={
                            "Authorization": f"token {self._access_token}",
                        },
                    ) as resp:
                        success = resp.status == 200
                        if success:
                            items = (await resp.json())["items"]
                            for item in items:
                                stored_env = StoredEnvelope.model_validate(item)
                                await self._handle_envelope(stored_env)
                        elif resp.status == 401:
                            self._access_token = None
                            self._logger.warning(
                                "Access token expired: a new one should be retrieved automatically"
                            )
                        else:
                            self._logger.debug(
                                f"Failed to retrieve messages: {resp.status}:{(await resp.text())}"
                            )
            except ClientConnectorError as ex:
                self._logger.warning(f"Failed to connect to mailbox server: {ex}")

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

        Args:
            uuid (UUID4): UUID of the envelope to delete
        """
        try:
            async with aiohttp.ClientSession() as session:
                env_url = f"{self._agentverse.url}/v1/mailbox/{str(uuid)}"
                self._logger.debug(f"Deleting message: {str(uuid)}")
                async with session.delete(
                    env_url,
                    headers={
                        "Authorization": f"token {self._access_token}",
                    },
                ) as resp:
                    if resp.status != 200:
                        self._logger.exception(
                            f"Failed to delete envelope from inbox: {(await resp.text())}"
                        )
        except ClientConnectorError as ex:
            self._logger.warning(f"Failed to connect to mailbox server: {ex}")
        except Exception as ex:
            self._logger.exception(f"Got exception while deleting message: {ex}")

    async def _get_access_token(self):
        """
        Gets an access token from the mailbox server.
        """
        async with aiohttp.ClientSession() as session:
            # get challenge
            challenge_url = f"{self._agentverse.url}/v1/auth/challenge"
            challenge_request = ChallengeRequest(address=self._identity.address)
            async with session.post(
                challenge_url,
                data=challenge_request.model_dump_json(),
                headers={"content-type": "application/json"},
            ) as resp:
                if resp and resp.status == 200:
                    challenge: str = (await resp.json())["challenge"]
                else:
                    self._logger.exception(
                        f"Failed to retrieve authorization challenge: {(await resp.text())}"
                    )
                    return

            # response to challenge with signature to get token
            prove_url = f"{self._agentverse.url}/v1/auth/prove"
            proof_request = ChallengeProof(
                address=self._identity.address,
                challenge=challenge,
                challenge_response=self._identity.sign(challenge.encode()),
            )
            async with session.post(
                prove_url,
                data=proof_request.model_dump_json(),
                headers={"content-type": "application/json"},
            ) as resp:
                if resp and resp.status == 200:
                    challenge_proof_response = ChallengeProofResponse.parse_raw(
                        await resp.text()
                    )
                    self._logger.info("Mailbox access token acquired")
                    self._access_token = challenge_proof_response.access_token
                else:
                    self._logger.exception(
                        f"Failed to prove authorization: {(await resp.text())}"
                    )
