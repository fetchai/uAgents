"""
This module provides methods to register your identity with the Fetch.ai services.
"""

import urllib.parse

import requests
from pydantic import BaseModel

from uagents_core.config import (
    DEFAULT_ALMANAC_API_PATH,
    DEFAULT_CHALLENGE_PATH,
    DEFAULT_REGISTRATION_PATH,
    DEFAULT_REQUEST_TIMEOUT,
    AgentverseConfig,
)
from uagents_core.identity import Identity
from uagents_core.logger import get_logger
from uagents_core.protocol import is_valid_protocol_digest
from uagents_core.registration import (
    AgentRegistrationAttestation,
    AgentRegistrationAttestationBatch,
    AgentStatusUpdate,
    AgentUpdates,
    AgentverseConnectRequest,
    ChallengeRequest,
    ChallengeResponse,
    RegistrationRequest,
    RegistrationResponse,
)
from uagents_core.types import AddressPrefix, AgentEndpoint

logger = get_logger("uagents_core.utils.registration")


class AgentRegistrationInput:
    identity: Identity
    prefix: str | None = None
    endpoints: list[str]
    protocol_digests: list[str]
    metadata: dict[str, str | list[str] | dict[str, str]] | None = None

    def __init__(
        self,
        identity: Identity,
        endpoints: list[str],
        protocol_digests: list[str],
        prefix: AddressPrefix | None = None,
        metadata: dict[str, str | list[str] | dict[str, str]] | None = None,
    ):
        self.identity = identity
        self.prefix = prefix
        self.endpoints = endpoints
        self.protocol_digests = protocol_digests
        self.metadata = metadata


def _send_post_request(
    url: str,
    data: BaseModel,
    *,
    headers: dict[str, str] | None = None,
    timeout: int = DEFAULT_REQUEST_TIMEOUT,
) -> tuple[bool, requests.Response | None]:
    final_headers: dict[str, str] = {"content-type": "application/json"}
    if headers:
        final_headers.update(headers)
    try:
        response: requests.Response = requests.post(
            url=url,
            headers=final_headers,
            data=data.model_dump_json(),
            timeout=timeout,
        )
        response.raise_for_status()
        return True, response
    except requests.RequestException as e:
        error_detail = getattr(e, "response", None)
        if error_detail is not None:
            error_detail = error_detail.text
        logger.error(
            msg=f"Error submitting request: {error_detail}",
            extra={"url": url, "data": data.model_dump_json()},
            exc_info=e,
        )
    return False, None


def _build_signed_attestation(
    item: AgentRegistrationInput,
) -> AgentRegistrationAttestation:
    agent_endpoints: list[AgentEndpoint] = [
        AgentEndpoint(url=endpoint, weight=1) for endpoint in item.endpoints
    ]

    attestation = AgentRegistrationAttestation(
        agent_identifier=f"{item.prefix}://{item.identity.address}"
        if item.prefix
        else item.identity.address,
        protocols=item.protocol_digests,
        endpoints=agent_endpoints,
        metadata=item.metadata,
    )

    attestation.sign(item.identity)
    return attestation


def register_in_almanac(
    identity: Identity,
    endpoints: list[str],
    protocol_digests: list[str],
    metadata: dict[str, str | list[str] | dict[str, str]] | None = None,
    prefix: AddressPrefix | None = None,
    *,
    agentverse_config: AgentverseConfig | None = None,
    timeout: int = DEFAULT_REQUEST_TIMEOUT,
) -> bool:
    """
    Register the identity with the Almanac API to make it discoverable by other agents.

    Args:
        identity (Identity): The identity of the agent.
        prefix (AddressPrefix | None): The prefix for the agent identifier.
        endpoints (list[str]): The endpoints that the agent can be reached at.
        protocol_digests (list[str]): The digests of the protocol that the agent supports
        agentverse_config (AgentverseConfig): The configuration for the agentverse API
        timeout (int): The timeout for the request
    """
    # check endpoints
    if not endpoints:
        logger.warning("No endpoints provided; skipping registration")
        return False
    for endpoint in endpoints:
        result = urllib.parse.urlparse(endpoint)
        if not all([result.scheme, result.netloc]):
            logger.error(
                msg="Invalid endpoint provided; skipping registration",
                extra={"endpoint": endpoint},
            )
            return False

    # check protocol digests
    for proto_digest in protocol_digests:
        if not is_valid_protocol_digest(proto_digest):
            logger.error(
                msg="Invalid protocol digest provided; skipping registration",
                extra={"protocol_digest": proto_digest},
            )
            return False

    # get the almanac API endpoint
    agentverse_config = agentverse_config or AgentverseConfig()
    almanac_api = urllib.parse.urljoin(agentverse_config.url, DEFAULT_ALMANAC_API_PATH)

    # create the attestation
    item = AgentRegistrationInput(
        identity=identity,
        prefix=prefix,
        endpoints=endpoints,
        protocol_digests=protocol_digests,
        metadata=metadata,
    )
    attestation = _build_signed_attestation(item)

    logger.info(msg="Registering with Almanac API", extra=attestation.model_dump())

    # submit the attestation to the API
    status, _ = _send_post_request(
        url=f"{almanac_api}/agents", data=attestation, timeout=timeout
    )
    return status


def register_batch_in_almanac(
    items: list[AgentRegistrationInput],
    *,
    agentverse_config: AgentverseConfig | None = None,
    timeout: int = DEFAULT_REQUEST_TIMEOUT,
    validate_all_before_registration: bool = False,
) -> tuple[bool, list[str]]:
    """
    Register multiple identities with the Almanac API to make them discoverable by other agents.

    The return value is a 2-tuple including:
    * (bool) Whether the registration request was both attempted and successful.
    * (list[str]) A list of addresses of identities that failed validation.

    If `validate_all_before_registration` is `True`, no registration request will be sent
    unless all identities pass validation.

    Args:
        items (list[AgentRegistrationInput]): The list of identities to register.
            See `register_in_almanac` for details about attributes in `AgentRegistrationInput`.
        agentverse_config (AgentverseConfig): The configuration for the agentverse API
        timeout (int): The timeout for the request
    """
    invalid_identities: list[str] = []
    attestations: list[AgentRegistrationAttestation] = []

    for item in items:
        # check endpoints
        if not item.endpoints:
            logger.warning(
                f"No endpoints provided for {item.identity.address}; skipping registration",
            )
            invalid_identities.append(item.identity.address)
        for endpoint in item.endpoints:
            result = urllib.parse.urlparse(endpoint)
            if not all([result.scheme, result.netloc]):
                logger.error(
                    msg=f"Invalid endpoint provided for {item.identity.address}; "
                    + "skipping registration",
                    extra={"endpoint": endpoint},
                )
                invalid_identities.append(item.identity.address)

        # check protocol digests
        for proto_digest in item.protocol_digests:
            if not is_valid_protocol_digest(proto_digest):
                logger.error(
                    msg=f"Invalid protocol digest provided for {item.identity.address}; "
                    + "skipping registration",
                    extra={"protocol_digest": proto_digest},
                )
                invalid_identities.append(item.identity.address)

    # Remove duplicates
    invalid_identities = sorted(list(set(invalid_identities)))

    for item in items:
        if item.identity.address not in invalid_identities:
            attestations.append(_build_signed_attestation(item))

    if validate_all_before_registration and invalid_identities:
        return False, invalid_identities

    # get the almanac API endpoint
    agentverse_config = agentverse_config or AgentverseConfig()
    almanac_api = urllib.parse.urljoin(agentverse_config.url, DEFAULT_ALMANAC_API_PATH)

    logger.info(
        msg="Bulk registering with Almanac API",
        extra={
            "agent_addresses": [
                attestation.agent_identifier for attestation in attestations
            ]
        },
    )
    attestation_batch = AgentRegistrationAttestationBatch(
        attestations=attestations,
    )

    # submit the attestation to the API
    status, _ = _send_post_request(
        url=f"{almanac_api}/agents/batch",
        data=attestation_batch,
        timeout=timeout,
    )
    return status, invalid_identities


# associate user account with your agent
def register_in_agentverse(
    request: AgentverseConnectRequest,
    identity: Identity,
    *,
    agent_details: AgentUpdates | None = None,
    agentverse_config: AgentverseConfig | None = None,
    timeout: int = DEFAULT_REQUEST_TIMEOUT,
) -> bool:
    """
    Register an agent in Agentverse and update its details if provided.

    Args:
        request (AgentverseConnectRequest): The request containing the agent details.
        identity (Identity): The identity of the agent.
        agent_details (AgentUpdates | None): The agent details to update.
        agentverse_config (AgentverseConfig | None): The configuration for the agentverse API
        timeout (int): The timeout for the requests
    """
    agentverse_config = agentverse_config or AgentverseConfig()
    registration_api = urllib.parse.urljoin(
        agentverse_config.url, DEFAULT_REGISTRATION_PATH
    )
    challenge_api = urllib.parse.urljoin(agentverse_config.url, DEFAULT_CHALLENGE_PATH)

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
    response = requests.get(
        f"{registration_api}/{agent_address}",
        headers={
            "content-type": "application/json",
            "authorization": f"Bearer {request.user_token}",
        },
        timeout=timeout,
    )

    # if it doesn't then create it
    if response.status_code == 404:
        logger.debug(
            msg="Agent does not exist on agentverse; registering it...",
            extra=registration_metadata,
        )

        challenge_request = ChallengeRequest(address=identity.address)
        logger.debug(
            msg="Requesting mailbox access challenge", extra=registration_metadata
        )
        status, response = _send_post_request(
            url=challenge_api,
            data=challenge_request,
            headers={"authorization": f"Bearer {request.user_token}"},
            timeout=timeout,
        )
        if not status or not response:
            logger.error(
                msg="Error requesting mailbox access challenge",
                extra=registration_metadata,
            )
            return False

        challenge = ChallengeResponse.model_validate_json(response.text)
        registration_payload = RegistrationRequest(
            address=identity.address,
            challenge=challenge.challenge,
            challenge_response=identity.sign(challenge.challenge.encode()),
            endpoint=request.endpoint,
            agent_type=request.agent_type,
        )
        status, response = _send_post_request(
            url=registration_api,
            data=registration_payload,
            headers={"authorization": f"Bearer {request.user_token}"},
            timeout=timeout,
        )
        if not status or not response:
            logger.error(
                msg="Error registering agent with Agentverse",
                extra=registration_metadata,
            )
            return False
        else:
            registration_response = RegistrationResponse.model_validate_json(
                response.text
            )
            if registration_response.success:
                logger.info(
                    msg=f"Successfully registered as {request.agent_type} agent in Agentverse",
                    extra=registration_metadata,
                )

    if not agent_details:
        logger.debug(
            msg="No agent details provided; skipping agent update",
            extra=registration_metadata,
        )
        return True

    # update the readme and the name of the agent to make it easier to find
    logger.debug(
        msg="Registering agent details with Agentverse",
        extra=registration_metadata,
    )
    try:
        response = requests.put(
            url=f"{registration_api}/{agent_address}",
            headers={
                "content-type": "application/json",
                "authorization": f"Bearer {request.user_token}",
            },
            data=agent_details.model_dump_json(),
            timeout=timeout,
        )
        response.raise_for_status()
        logger.info(
            msg="Completed registering agent with Agentverse",
            extra=registration_metadata,
        )
        return True
    except requests.RequestException as e:
        logger.error(
            msg="Error registering agent with Agentverse",
            extra=registration_metadata,
            exc_info=e,
        )
        return False


def update_agent_status(active: bool, identity: Identity):
    """
    Update the agent's active/inactive status in the Almanac API.

    Args:
        active (bool): The status of the agent.
        identity (Identity): The identity of the agent.
    """
    almanac_api = AgentverseConfig().url + DEFAULT_ALMANAC_API_PATH

    status_update = AgentStatusUpdate(
        agent_identifier=identity.address, is_active=active
    )
    status_update.sign(identity)

    logger.debug(
        msg="Updating agent status in Almanac API",
        extra=status_update.model_dump(),
    )

    status, _ = _send_post_request(
        url=f"{almanac_api}/agents/{identity.address}/status",
        data=status_update,
    )

    if status:
        logger.info(
            msg=f"Agent status updated to {'active' if active else 'inactive'}",
            extra={"agent_address": identity.address},
        )

    return status
