"""
This module provides methods to enable an identity to interact with other agents.

Note: All methods in this module act synchronously / blocking.
"""

import urllib.parse

import requests

from uagents_core.config import (
    DEFAULT_ALMANAC_API_PATH,
    DEFAULT_CHALLENGE_PATH,
    DEFAULT_REGISTRATION_PATH,
    DEFAULT_REQUEST_TIMEOUT,
    AgentverseConfig,
)
from uagents_core.crypto import Identity
from uagents_core.logger import get_logger
from uagents_core.registration import (
    AgentRegistrationAttestation,
    AgentUpdates,
    AgentverseConnectRequest,
    ChallengeRequest,
    ChallengeResponse,
    RegistrationRequest,
    RegistrationResponse,
)
from uagents_core.types import AgentEndpoint

logger = get_logger("uagents_core.utils.registration")


def register_in_almanac(
    request: AgentverseConnectRequest,
    identity: Identity,
    *,
    protocol_digests: list[str],
    agentverse_config: AgentverseConfig | None = None,
    timeout: int = DEFAULT_REQUEST_TIMEOUT,
) -> None:
    """
    Register the identity with the Almanac API to make it discoverable by other agents.

    Args:
        request (AgentverseConnectRequest): The request containing the agent details.
        identity (Identity): The identity of the agent.
        protocol_digest (list[str]): The digest of the protocol that the agent supports
        agentverse_config (AgentverseConfig): The configuration for the agentverse API
        timeout (int): The timeout for the request
    """
    # get the almanac API endpoint
    agentverse_config = agentverse_config or AgentverseConfig()
    almanac_api = urllib.parse.urljoin(agentverse_config.url, DEFAULT_ALMANAC_API_PATH)

    # get the agent address
    agent_address = identity.address

    registration_metadata = {
        "almanac_endpoint": almanac_api,
        "agent_address": agent_address,
        "agent_endpoint": request.endpoint or "",
        "protocol_digest": ",".join(protocol_digests),
    }
    if request.endpoint is None:
        if request.agent_type == "mailbox":
            request.endpoint = f"{agentverse_config.url}/v1/submit"
        elif request.agent_type == "proxy":
            request.endpoint = f"{agentverse_config.url}/v1/proxy/submit"

    # if no endpoint is provided for normal and proxy agents, log a warning
    if request.endpoint is None:
        logger.warning(
            msg="No endpoint provided for agent registration",
            extra=registration_metadata,
        )
        return

    logger.info(
        msg="Registering with Almanac API",
        extra=registration_metadata,
    )

    # create the attestation
    attestation = AgentRegistrationAttestation(
        agent_identifier=agent_address,
        protocols=protocol_digests,
        endpoints=[AgentEndpoint(url=request.endpoint, weight=1)],
        metadata=None,
    )

    # sign the attestation
    attestation.sign(identity)

    # submit the attestation to the API
    r = requests.post(
        f"{almanac_api}/agents",
        headers={"content-type": "application/json"},
        data=attestation.model_dump_json(),
        timeout=timeout,
    )
    r.raise_for_status()
    logger.debug(
        "Agent attestation submitted",
        extra=registration_metadata,
    )


# associate user account with your agent
def register_in_agentverse(
    request: AgentverseConnectRequest,
    identity: Identity,
    agent_details: AgentUpdates | None = None,
    *,
    agentverse_config: AgentverseConfig | None = None,
):
    """
    Register the agent with the Agentverse API.

    Args:
        request (AgentverseConnectRequest): The request containing the agent details.
        identity (Identity): The identity of the agent.
        agent_details (Optional[AgentUpdates]): The agent details to update.
        agentverse_config (AgentverseConfig): The configuration for the agentverse API
    """
    # API endpoints
    agentverse_config = agentverse_config or AgentverseConfig()
    registration_api = urllib.parse.urljoin(
        agentverse_config.url, DEFAULT_REGISTRATION_PATH
    )
    challenge_api = urllib.parse.urljoin(agentverse_config.url, DEFAULT_CHALLENGE_PATH)

    # get the agent address
    agent_address = identity.address

    registration_metadata = {
        "registration_api": registration_api,
        "challenge_api": challenge_api,
        "agent_address": agent_address,
        "agent_endpoint": request.endpoint or "",
        "agent_type": request.agent_type,
        "agent_name": agent_details.name if agent_details else "",
    }

    # check to see if the agent exists
    r = requests.get(
        f"{registration_api}/{agent_address}",
        headers={
            "content-type": "application/json",
            "authorization": f"Bearer {request.user_token}",
        },
        timeout=10,
    )

    # if it doesn't then create it
    if r.status_code == 404:
        logger.debug(
            "Agent did not exist on agentverse; registering it",
            extra=registration_metadata,
        )

        challenge_request = ChallengeRequest(address=identity.address)
        logger.debug(
            "Requesting mailbox access challenge",
            extra=registration_metadata,
        )
        r = requests.post(
            challenge_api,
            data=challenge_request.model_dump_json(),
            headers={
                "content-type": "application/json",
                "Authorization": f"Bearer {request.user_token}",
            },
            timeout=10,
        )
        r.raise_for_status()
        challenge = ChallengeResponse.model_validate_json(r.text)
        registration_payload = RegistrationRequest(
            address=identity.address,
            challenge=challenge.challenge,
            challenge_response=identity.sign(challenge.challenge.encode()),
            endpoint=request.endpoint,
            agent_type=request.agent_type,
        ).model_dump_json()
        r = requests.post(
            registration_api,
            headers={
                "content-type": "application/json",
                "authorization": f"Bearer {request.user_token}",
            },
            data=registration_payload,
            timeout=10,
        )
        if r.status_code == 409:
            logger.info(
                "Agent already registered with Agentverse",
                extra=registration_metadata,
            )
        else:
            r.raise_for_status()
            registration_response = RegistrationResponse.model_validate_json(r.text)
            if registration_response.success:
                logger.info(
                    f"Successfully registered as {request.agent_type} agent in Agentverse",
                    extra=registration_metadata,
                )
    if not agent_details:
        logger.debug(
            "No agent details provided; skipping agent update",
            extra=registration_metadata,
        )
        return

    # update the readme and the title of the agent to make it easier to find
    logger.debug(
        "Registering agent title and readme with Agentverse",
        extra=registration_metadata,
    )
    update = AgentUpdates(name=agent_details.name, readme=agent_details.readme)
    r = requests.put(
        f"{registration_api}/{agent_address}",
        headers={
            "content-type": "application/json",
            "authorization": f"Bearer {request.user_token}",
        },
        data=update.model_dump_json(),
        timeout=10,
    )
    r.raise_for_status()
    logger.info(
        "Completed registering agent with Agentverse",
        extra=registration_metadata,
    )
