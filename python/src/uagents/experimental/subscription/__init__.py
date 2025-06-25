"""
This Protocol class provides a basic example to support subscriptions.

If a requesting agent is on the free tier, it will be rate-limited according
to the specification given for the QuotaProtocol. If the agent is on a paid
tier (PLUS or PRO), it will not be rate-limited and can make requests
without restrictions.

Usage examples:

```python
from uagents.experimental.subscription import SubscribableProtocol

protocol_spec = ProtocolSpecification(...) # Import or create any protocol specification

# Initialize the SubscribableProtocol instance
subs_protocol = SubscribableProtocol(
    storage_reference=agent.storage,
    identity=agent.identity,
    agentverse=agent.agentverse,
    spec=protocol_spec,
    # default_rate_limit=RateLimit(window_size_minutes=1, max_requests=3), # Optional
)

# Subscription and rate limiting does not apply to this message handler
@subs_protocol.on_message(ExampleMessage1)
async def handle(ctx: Context, sender: str, msg: ExampleMessage1):
    ...

# This message handler is rate limited with custom window size and request limit
# that will be bypassed if the agent is on a paid tier
@subs_protocol.on_message(
    ExampleMessage2,
    rate_limit=RateLimit(window_size_minutes=1, max_requests=3),
)
async def handle(ctx: Context, sender: str, msg: ExampleMessage2):
    ...
"""

from uagents_core.utils.subscriptions import TierType, get_subscription_tier

from uagents.config import AgentverseConfig
from uagents.crypto import Identity
from uagents.experimental.quota import AccessControlList, QuotaProtocol, RateLimit
from uagents.storage import StorageAPI


class SubscribableProtocol(QuotaProtocol):
    def __init__(
        self,
        storage_reference: StorageAPI,
        identity: Identity,
        agentverse: AgentverseConfig,
        name: str | None = None,
        version: str | None = None,
        default_rate_limit: RateLimit | None = None,
        default_acl: AccessControlList | None = None,
    ):
        """
        Initialize a SubscribableProtocol instance.

        Args:
            storage_reference (StorageAPI): The storage reference to use for rate limiting.
            identity (Identity): The identity of the agent supporting subscriptions.
            agentverse (AgentverseConfig): The agentverse configuration.
            name (str | None): The name of the protocol. Defaults to None.
            version (str | None): The version of the protocol. Defaults to None.
            default_rate_limit (RateLimit | None): The default rate limit. Defaults to None.
            default_acl (AccessControlList | None): The access control list. Defaults to None.
        """
        self._identity = identity
        self._agentverse = agentverse
        super().__init__(
            name=name,
            version=version,
            storage_reference=storage_reference,
            default_rate_limit=default_rate_limit,
            default_acl=default_acl,
        )

    def add_request(
        self,
        agent_address: str,
        function_name: str,
        window_size_minutes: int,
        max_requests: int,
    ) -> bool:
        """
        Add a request to the rate limiter if the current time is still within the
        time window since the beginning of the most recent time window. Otherwise,
        reset the time window and add the request.

        Args:
            agent_address: The address of the agent making the request.

        Returns:
            False if the agent is on the free tier and the maximum number of requests
              has been exceeded, True otherwise.
        """
        tier = get_subscription_tier(self._identity, agent_address, self._agentverse)
        if tier in (TierType.PLUS, TierType.PRO):
            return True

        return super().add_request(
            agent_address=agent_address,
            function_name=function_name,
            window_size_minutes=window_size_minutes,
            max_requests=max_requests,
        )
