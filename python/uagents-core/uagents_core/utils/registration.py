"""Registration utilities for the Agentverse platform.

This module provides functions to register agents with Agentverse, the Fetch.ai
agent discovery and marketplace service. Registration makes your agent
discoverable by other agents and sets up the webhook endpoint for receiving
messages.

Typical usage for a chat-capable agent::

    from uagents_core.utils.registration import (
        AgentverseRequestError,
        RegistrationRequestCredentials,
        register_chat_agent,
    )

    credentials = RegistrationRequestCredentials(
        agent_seed_phrase="your-agent-seed-phrase",
        agentverse_api_key="your-agentverse-api-key",
    )

    try:
        register_chat_agent(
            name="My Agent",
            endpoint="https://my-server.com/webhook",
            active=True,
            credentials=credentials,
            readme="# My Agent\\nHandles customer questions.",
        )
    except AgentverseRequestError as error:
        print(f"Registration failed: {error}")
        # Access the underlying network/HTTP exception:
        print(f"Caused by: {error.from_exc}")

Registration performs three steps:

1. **Identity verification** -- proves ownership of the agent address via a
   cryptographic challenge-response flow with the Agentverse identity API.
2. **Agent details registration** -- creates or updates the agent's profile,
   endpoint, protocols, and metadata on Agentverse.
3. **Status activation** -- marks the agent as active in the Almanac so
   Agentverse keeps the entry synchronized and discoverable.

All HTTP failures are wrapped in :class:`AgentverseRequestError`, which
preserves the original exception in its ``from_exc`` attribute for debugging.
"""

import urllib.parse
from json import JSONDecodeError
from typing import Literal

import requests
from pydantic import BaseModel, Field, model_validator

from uagents_core.config import (
    DEFAULT_ALMANAC_API_PATH,
    DEFAULT_REQUEST_TIMEOUT,
    AgentverseConfig,
)
from uagents_core.contrib.protocols.chat import chat_protocol_spec
from uagents_core.identity import Identity
from uagents_core.logger import get_logger
from uagents_core.protocol import ProtocolSpecification, is_valid_protocol_digest
from uagents_core.registration import (
    AgentProfile,
    AgentStatusUpdate,
    AgentverseConnectRequest,
    BatchRegistrationRequest,
    ChallengeResponse,
    IdentityProof,
    RegistrationRequest,
)
from uagents_core.types import AgentEndpoint, AgentMetadata, AgentType

logger = get_logger("uagents_core.utils.registration")


class AgentverseRegistrationRequest(BaseModel):
    """All information needed to register an agent with Agentverse.

    This is the internal representation used by :func:`register_agent` and
    :func:`register_chat_agent`. Most callers should use those functions
    directly rather than constructing this model manually.

    Raises:
        ValueError: If ``endpoint`` is not a valid URL or any protocol
            digest in ``protocols`` is malformed.
    """

    name: str = Field(description="Agent name in Agentverse.")
    endpoint: str = Field(
        description="Endpoint where the existing agent is accessible at."
    )
    protocols: list[str] = Field(
        description="List of protocols supported by the agent."
    )
    metadata: dict[str, str | list[str] | dict[str, str]] | None = Field(
        default=None,
        description="Additional metadata about the agent (e.g. geolocation).",
    )
    type: AgentType = Field(
        default="uagent", description="Agentverse registration type."
    )
    description: str | None = Field(
        default=None,
        description="Agent short description, shown on its Agentverse profile.",
    )
    readme: str | None = Field(default=None, description="Agent skills description.")
    avatar_url: str | None = Field(
        default=None,
        description="Agent avatar URL to be shown on its Agentverse profile.",
    )
    handle: str | None = Field(
        default=None,
        max_length=40,
        description="Agent's unique handle in Agentverse.",
    )
    active: bool = Field(
        default=True,
        description="Set agent as active immediately after registration.",
    )
    track_interactions: bool | None = Field(
        default=True,
        description="Whether to track interactions of this agent in Agentverse.",
    )

    @model_validator(mode="after")
    def check_request(self) -> "AgentverseRegistrationRequest":
        result = urllib.parse.urlparse(self.endpoint)
        if not all([result.scheme, result.netloc]):
            raise ValueError(f"Invalid endpoint provided: {self.endpoint}")

        for proto_digest in self.protocols:
            if not is_valid_protocol_digest(proto_digest):
                raise ValueError(
                    f"Invalid protocol digest provided: {proto_digest}",
                )
        return self


class RegistrationRequestCredentials(BaseModel):
    """Credentials required to authenticate with the Agentverse API.

    Attributes:
        agentverse_api_key: An API key generated from the Agentverse dashboard
            (https://agentverse.ai). This authenticates the request.
        agent_seed_phrase: The secret seed phrase used to derive the agent's
            cryptographic identity. This must match the seed used when the
            agent was first created.
        team: Optional team identifier. When provided, the agent is registered
            under this team in Agentverse.
    """

    agentverse_api_key: str = Field(
        description="Agentverse API key generated by the owner of the agent."
    )
    agent_seed_phrase: str = Field(
        description="The secret seed phrase used to create the agent identity."
    )
    team: str | None = Field(
        default=None, description="The team the agent belongs to in Agentverse."
    )


class AgentverseRequestError(Exception):
    """Raised when an Agentverse API request fails.

    This exception wraps all HTTP and network errors that occur during
    registration, identity verification, or status updates. The human-readable
    message describes what went wrong, while ``from_exc`` preserves the
    original exception for debugging.

    Attributes:
        from_exc: The original exception that caused this error. Common types
            include ``requests.ConnectionError`` (network unreachable),
            ``requests.Timeout`` (request timed out),
            ``requests.HTTPError`` (non-2xx status code), and
            ``requests.RequestException`` (other request failures).

    Common error messages and their meaning:

    - ``"Connection error ..."`` -- Could not reach the Agentverse API. Check
      your network connection and the configured base URL.
    - ``"Operation timed out."`` -- The request exceeded the timeout
      (default: 10 seconds). The Agentverse API may be under heavy load.
    - ``"HTTP error: 401 ..."`` -- Invalid or expired API key. Generate a new
      key from the Agentverse dashboard.
    - ``"HTTP error: 406 ..."`` -- The request was not acceptable. This
      typically means the agent data is malformed or missing required fields.
    - ``"HTTP error: 409 ..."`` -- Conflict. The agent address or handle is
      already registered by a different account.
    - ``"Unexpected server error."`` -- HTTP 500 from Agentverse. Retry after
      a short delay. If persistent, check the Agentverse status page.
    - ``"failed to request proof-of-ownership challenge. ..."`` -- The
      identity verification step failed. This usually means the API key
      does not have permission to register this agent address.

    Example::

        try:
            register_chat_agent(...)
        except AgentverseRequestError as error:
            print(f"Registration failed: {error}")

            # Inspect the underlying cause
            if isinstance(error.from_exc, requests.Timeout):
                print("Consider increasing the timeout or retrying.")
            elif isinstance(error.from_exc, requests.HTTPError):
                print(f"HTTP status: {error.from_exc.response.status_code}")
    """

    def __init__(self, *args, from_exc: Exception):
        self.from_exc = from_exc
        super().__init__(*args)


def _send_http_request_agentverse(
    request_type: Literal["get", "post", "put"],
    url: str,
    *,
    data: BaseModel | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = DEFAULT_REQUEST_TIMEOUT,
) -> requests.Response:
    final_headers: dict[str, str] = {"content-type": "application/json"}
    if headers:
        final_headers.update(headers)

    send_request = {
        "get": requests.get,
        "post": requests.post,
        "put": requests.put,
    }[request_type]

    try:
        response: requests.Response = send_request(
            url=url,
            headers=final_headers,
            data=data.model_dump_json() if data else None,
            timeout=timeout,
        )
        response.raise_for_status()
    except Exception as e:
        err_msg = ""

        if isinstance(e, requests.ConnectionError):
            err_msg += f"Connection error {e.strerror}."
        elif isinstance(e, requests.Timeout):
            err_msg += "Operation timed out."
        elif isinstance(e, requests.HTTPError):
            code = e.response.status_code
            try:
                content = e.response.json()["detail"]
            except (JSONDecodeError, KeyError):
                content = e.response.content.decode()
            if code in [401, 406, 409]:
                err_msg += content
            elif code == 500:
                err_msg += "Unexpected server error."
            else:
                err_msg += f"HTTP error: {code} {content}"
        elif isinstance(e, requests.RequestException):
            err_msg += f"Unexpected request error: {e}."
        else:
            err_msg += f"Unexpected error: {e}."

        raise AgentverseRequestError(err_msg, from_exc=e) from e

    return response


def _send_post_request_agentverse(
    url: str,
    *,
    data: BaseModel | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = DEFAULT_REQUEST_TIMEOUT,
) -> requests.Response:
    return _send_http_request_agentverse(
        "post", url, data=data, headers=headers, timeout=timeout
    )


def _register_in_agentverse(
    request: AgentverseConnectRequest,
    identity: Identity,
    *,
    agent_details: AgentverseRegistrationRequest,
    agentverse_config: AgentverseConfig | None = None,
    timeout: int = DEFAULT_REQUEST_TIMEOUT,
):
    """Register an agent in Agentverse (internal implementation).

    Performs identity verification (if the agent is new) and then registers
    or updates the agent's details. This is the core implementation used by
    :func:`register_in_agentverse` and :func:`register_agent`.

    Raises:
        AgentverseRequestError: If any API call fails (identity challenge,
            identity proof submission, or agent details registration).
    """
    agentverse_config = agentverse_config or AgentverseConfig()
    agents_api = agentverse_config.agents_api
    identity_api = agentverse_config.identity_api

    agent_address = identity.address

    registration_metadata = {
        "agents_api": agents_api,
        "agent_address": agent_address,
        "agent_endpoint": request.endpoint or "",
        "agent_type": request.agent_type,
        "agent_name": agent_details.name,
    }

    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {request.user_token}",
    }
    if request.team:
        headers["x-team"] = request.team

    # check to see if the agent exists
    response = requests.get(
        f"{agents_api}/{agent_address}",
        headers=headers,
        timeout=timeout,
    )

    # if it doesn't then create it
    if response.status_code == 404:
        logger.debug(
            msg="Agent does not exist on agentverse; registering it...",
            extra=registration_metadata,
        )

        challenge_api = f"{identity_api}/{agent_address}/challenge"
        logger.debug(
            msg="Requesting proof-of-ownership challenge",
            extra={**registration_metadata, "challenge_api": challenge_api},
        )
        try:
            response = _send_http_request_agentverse(
                request_type="get",
                url=challenge_api,
                data=None,
                headers={"authorization": f"Bearer {request.user_token}"},
                timeout=timeout,
            )
        except AgentverseRequestError as e:
            raise AgentverseRequestError(
                f"failed to request proof-of-ownership challenge. {str(e)}",
                from_exc=e.from_exc,
            ) from e

        challenge = ChallengeResponse.model_validate_json(response.text)
        identity_proof = IdentityProof(
            address=identity.address,
            challenge=challenge.challenge,
            challenge_response=identity.sign(challenge.challenge.encode()),
        )

        response = _send_post_request_agentverse(
            url=identity_api,
            data=identity_proof,
            headers=headers,
            timeout=timeout,
        )

    # update the readme and the name of the agent to make it easier to find
    logger.debug(
        msg="Registering agent details with Agentverse",
        extra=registration_metadata,
    )

    if agent_details.track_interactions:
        endpoints = [AgentEndpoint(url=agentverse_config.proxy_endpoint, weight=1)]
    else:
        endpoints = [AgentEndpoint(url=agent_details.endpoint, weight=1)]

    reg_request = RegistrationRequest(
        address=agent_address,
        name=agent_details.name,
        handle=agent_details.handle,
        url=agent_details.endpoint,
        agent_type=agent_details.type,
        profile=AgentProfile(
            description=agent_details.description or "",
            readme=agent_details.readme or "",
            avatar_url=agent_details.avatar_url or "",
        ),
        endpoints=endpoints,
        protocols=agent_details.protocols,
        metadata=agent_details.metadata,
    )

    _send_post_request_agentverse(
        url=agents_api,
        headers=headers,
        data=reg_request,
        timeout=timeout,
    )


def register_in_agentverse(
    request: AgentverseConnectRequest,
    identity: Identity,
    agent_details: AgentverseRegistrationRequest,
    *,
    agentverse_config: AgentverseConfig | None = None,
    timeout: int = DEFAULT_REQUEST_TIMEOUT,
) -> bool:
    """Register an agent in Agentverse (error-safe wrapper).

    This is a convenience wrapper around :func:`_register_in_agentverse`
    that catches :class:`AgentverseRequestError` and returns ``False``
    instead of raising. Use this when you want simple boolean success/failure
    semantics without handling exceptions.

    For error details, use :func:`register_agent` or
    :func:`register_chat_agent` instead, which raise
    :class:`AgentverseRequestError` with diagnostic information.

    Args:
        request: Connection details including the API token and endpoint.
        identity: The cryptographic identity of the agent.
        agent_details: Agent profile data to register.
        agentverse_config: Custom API configuration. Defaults to the
            standard Agentverse production endpoint.
        timeout: HTTP request timeout in seconds. Defaults to 10.

    Returns:
        ``True`` if registration succeeded, ``False`` if any API call failed.
        On failure, the error is logged but not raised.
    """
    try:
        _register_in_agentverse(
            request,
            identity,
            agent_details=agent_details,
            agentverse_config=agentverse_config,
            timeout=timeout,
        )
        return True
    except AgentverseRequestError as e:
        logger.error(msg=str(e), exc_info=e.from_exc)

    return False


def _update_agent_status(active: bool, identity: Identity):
    """Update the agent's active/inactive status in the Almanac API.

    Active agents are kept synchronized by Agentverse and remain
    discoverable. Inactive agents are still registered but will not
    appear in search results.

    Raises:
        AgentverseRequestError: If the status update API call fails.
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

    _send_post_request_agentverse(
        url=f"{almanac_api}/agents/{identity.address}/status",
        data=status_update,
    )


def update_agent_status(active: bool, identity: Identity) -> bool:
    """Update the agent's active/inactive status (error-safe wrapper).

    This is a convenience wrapper that catches :class:`AgentverseRequestError`
    and returns ``False`` instead of raising.

    Args:
        active: ``True`` to mark the agent as active (discoverable),
            ``False`` to mark it as inactive.
        identity: The cryptographic identity of the agent.

    Returns:
        ``True`` if the status update succeeded, ``False`` otherwise.
        On failure, the error is logged but not raised.
    """
    try:
        _update_agent_status(active, identity)
        return True
    except AgentverseRequestError as e:
        logger.error(msg=str(e), exc_info=e.from_exc)

    return False


def register_agent(
    agent_registration: AgentverseRegistrationRequest,
    agentverse_config: AgentverseConfig,
    credentials: RegistrationRequestCredentials,
) -> bool:
    """Register an agent in Agentverse and optionally set it as active.

    This is the primary registration function. It derives the agent's
    cryptographic identity from the seed phrase, verifies ownership with
    Agentverse, registers the agent details, and (if ``active=True`` in
    the registration request) sets the agent status to active.

    For chat-capable agents, prefer :func:`register_chat_agent` which
    automatically includes the chat protocol digest.

    Args:
        agent_registration: The agent details to register (name, endpoint,
            protocols, metadata, etc.).
        agentverse_config: API configuration (base URL, HTTP prefix).
        credentials: Authentication credentials (API key, seed phrase,
            and optional team).

    Returns:
        ``True`` if registration (and activation, if requested) succeeded.

    Raises:
        AgentverseRequestError: If any step of the registration fails.
            Common causes include invalid API key (HTTP 401), malformed
            request data (HTTP 406), address conflict (HTTP 409), server
            errors (HTTP 500), network timeouts, or connection failures.
            The original exception is available via ``error.from_exc``.
        ValueError: If the endpoint URL or protocol digests in
            ``agent_registration`` are malformed (raised during model
            validation, before any API calls are made).
    """
    identity = Identity.from_seed(credentials.agent_seed_phrase, 0)
    connect_request = AgentverseConnectRequest(
        user_token=credentials.agentverse_api_key,
        agent_type=agent_registration.type,
        endpoint=agent_registration.endpoint,
        team=credentials.team,
    )

    logger.info("registering to Agentverse...")
    _register_in_agentverse(
        connect_request,
        identity,
        agent_details=agent_registration,
        agentverse_config=agentverse_config,
    )
    logger.info("successfully registered to Agentverse.")

    if agent_registration.active:
        logger.info("setting agent as active...")
        _update_agent_status(True, identity)
        logger.info("successfully set agent to active.")

    return True


def register_chat_agent(
    name: str,
    endpoint: str,
    active: bool,
    credentials: RegistrationRequestCredentials,
    track_interactions: bool = True,
    description: str | None = None,
    readme: str | None = None,
    avatar_url: str | None = None,
    metadata: AgentMetadata | dict[str, str | list[str] | dict[str, str]] | None = None,
    agentverse_config: AgentverseConfig | None = None,
) -> bool:
    """Register a chat-capable agent in Agentverse.

    This is the recommended entry point for registering agents that support
    the standard chat protocol. It automatically includes the chat protocol
    digest so the agent is discoverable for chat-based interactions.

    The function performs three steps:

    1. **Identity verification** -- If this is a new agent, proves ownership
       via a cryptographic challenge signed with the agent's seed phrase.
    2. **Agent details registration** -- Creates or updates the agent's name,
       endpoint, readme, avatar, and metadata on Agentverse.
    3. **Status activation** -- If ``active=True``, marks the agent as active
       in the Almanac so it remains discoverable.

    Args:
        name: Display name for the agent on Agentverse (max 80 characters
            recommended).
        endpoint: The publicly accessible webhook URL where the agent
            receives messages. Must include scheme (``https://``).
        active: Whether to set the agent as active immediately after
            registration. Active agents are discoverable and kept
            synchronized by Agentverse.
        credentials: Authentication credentials. See
            :class:`RegistrationRequestCredentials`.
        description: Short description shown on the agent's Agentverse
            profile page.
        readme: Longer markdown description of the agent's capabilities.
            This is displayed on the agent's detail page in Agentverse.
        avatar_url: URL to the agent's avatar image.
        metadata: Additional metadata such as categories, tags, geolocation,
            contact details, and visibility (``is_public``). Can be a dict
            or an :class:`AgentMetadata` instance.
        agentverse_config: Custom API configuration. Defaults to the
            standard Agentverse production endpoint (``agentverse.ai``).

    Returns:
        ``True`` if registration succeeded.

    Raises:
        AgentverseRequestError: If any step of the registration or
            activation fails. See :class:`AgentverseRequestError` for
            common error messages and their meaning.
        ValueError: If ``endpoint`` is not a valid URL.

    Example::

        from uagents_core.utils.registration import (
            AgentverseRequestError,
            RegistrationRequestCredentials,
            register_chat_agent,
        )

        credentials = RegistrationRequestCredentials(
            agent_seed_phrase="my-secret-seed",
            agentverse_api_key="av-key-...",
        )

        try:
            register_chat_agent(
                name="Customer Support Agent",
                endpoint="https://my-server.com/agent/webhook",
                active=True,
                credentials=credentials,
                readme="# Customer Support\\nAnswers product questions.",
                metadata={
                    "categories": ["support"],
                    "is_public": "True",
                },
            )
            print("Agent registered successfully!")
        except AgentverseRequestError as error:
            print(f"Registration failed: {error}")
    """
    chat_protocol = [
        ProtocolSpecification.compute_digest(chat_protocol_spec.manifest())
    ]
    raw_metadata = (
        metadata.model_dump(exclude_unset=True)
        if isinstance(metadata, AgentMetadata)
        else metadata
    )
    request = AgentverseRegistrationRequest(
        name=name,
        endpoint=endpoint,
        protocols=chat_protocol,
        active=active,
        description=description,
        readme=readme,
        avatar_url=avatar_url,
        metadata=raw_metadata,
        track_interactions=track_interactions,
    )
    config = agentverse_config or AgentverseConfig()

    return register_agent(request, config, credentials)


def register_batch_in_agentverse(
    batch_request: BatchRegistrationRequest,
    user_token: str,
    *,
    agentverse_config: AgentverseConfig | None = None,
    timeout: int = DEFAULT_REQUEST_TIMEOUT,
) -> bool:
    """Register multiple agents in a single batch request (error-safe).

    .. deprecated::
        Prefer individual :func:`register_chat_agent` calls. Batch
        registration does not include identity verification or status
        activation.

    Args:
        batch_request: The batch registration request containing a list
            of agents to register.
        user_token: The user's Agentverse API key.
        agentverse_config: Custom API configuration. Defaults to the
            standard Agentverse production endpoint.
        timeout: HTTP request timeout in seconds. Defaults to 10.

    Returns:
        ``True`` if the batch registration succeeded, ``False`` otherwise.
        On failure, the error is logged but not raised.
    """
    agentverse_config = agentverse_config or AgentverseConfig()
    agents_api = agentverse_config.agents_api
    batch_url = f"{agents_api}/batch"

    logger.debug(
        msg="Registering batch of agents in Agentverse",
        extra={
            "agents_api": agents_api,
            "batch_url": batch_url,
            "agent_count": len(batch_request.agents),
        },
    )

    try:
        _send_post_request_agentverse(
            url=batch_url,
            headers={
                "content-type": "application/json",
                "authorization": f"Bearer {user_token}",
            },
            data=batch_request,
            timeout=timeout,
        )
        logger.info(
            f"Successfully registered batch of {len(batch_request.agents)} agents in Agentverse"
        )
        return True
    except AgentverseRequestError as e:
        logger.error(
            msg=f"Failed to register batch of agents in Agentverse: {str(e)}",
            exc_info=e.from_exc,
        )
        return False
