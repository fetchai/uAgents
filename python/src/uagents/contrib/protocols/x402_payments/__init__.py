"""
x402 Payment Protocol for uAgents

This protocol enables agents to conduct buy/sell transactions with each other
using the x402 payment standard. x402 allows for automatic cryptocurrency payments
when accessing APIs and services, with gasless transactions via EIP-3009.

Key Features:
- Automatic payment handling for agent services
- Support for USDC and any EIP-3009 compatible tokens
- Gasless payments (facilitator sponsors gas)
- Works on Base, Base Sepolia, and any EVM network
- Built-in discovery via x402 Bazaar

Example usage:
    from uagents import Agent
    from uagents.contrib.protocols.x402_payments import X402PaymentProtocol, MarketplaceQuery

    # Create an agent with payment capabilities
    agent = Agent(name="ai-weather-service")

    # Initialize x402 payment protocol
    payment_protocol = X402PaymentProtocol(
        # For testnet (no CDP keys needed)
        network="base-sepolia",
        facilitator_url="https://x402.org/facilitator",

        # For mainnet (requires CDP keys)
        # network="base",
        # cdp_api_key_id="your_cdp_api_key_id",
        # cdp_api_secret="your_cdp_api_secret",
    )

    # Add payment capability to the agent
    agent.include(payment_protocol)

    # Register a paid service
    @payment_protocol.paid_service(
        price="$0.001",  # 0.1 cent per request
        description="Get real-time weather data",
        path="/weather"
    )
    async def get_weather(ctx: Context, location: str) -> dict:
        return {
            "location": location,
            "weather": "sunny",
            "temperature": 72
        }

    # Discover and buy services from other agents
    @agent.on_message(model=MarketplaceQuery)
    async def discover_services(ctx: Context, sender: str, msg: MarketplaceQuery):
        # Query other agents for services
        services = await payment_protocol.discover_services(
            category="weather",
            max_price="$0.01"
        )

        for service in services:
            # Automatically pay and access the service
            result = await payment_protocol.buy_service(
                service_url=service.endpoint,
                params={"location": "San Francisco"}
            )
            ctx.logger.info(f"Got weather: {result}")
"""

from datetime import datetime
from enum import Enum
from typing import Any

from uagents import Model


# Payment Models
class X402Network(str, Enum):
    """Supported x402 networks"""

    BASE_SEPOLIA = "base-sepolia"  # Testnet - free facilitator at x402.org
    BASE = "base"  # Mainnet - requires CDP API keys
    XDC = "xdc"  # XDC Network


class PaymentStatus(str, Enum):
    """Status of a payment transaction"""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class ServiceRequest(Model):
    """Request to access a paid service"""

    request_id: str
    service_endpoint: str  # URL of the service
    params: dict[str, Any] | None = None  # Parameters for the service
    max_payment: str | None = None  # Maximum willing to pay (e.g., "$0.01")


class ServiceResponse(Model):
    """Response from a paid service"""

    request_id: str
    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    payment_made: str | None = None  # Amount paid
    transaction_hash: str | None = None


class ServiceDiscoveryRequest(Model):
    """Request to discover available paid services"""

    query_id: str
    category: str | None = None
    keywords: list[str] | None = None
    max_price: str | None = None
    network: str | None = None


class ServiceOffer(Model):
    """Offer for a paid service"""

    query_id: str
    service_id: str
    name: str
    description: str
    endpoint: str  # x402-enabled endpoint
    price: str  # e.g., "$0.001"
    category: str | None = None
    provider_address: str
    network: str
    metadata: dict[str, Any] | None = None


class PaymentNotification(Model):
    """Notification of a completed payment"""

    transaction_hash: str
    amount: str
    currency: str
    from_address: str
    to_address: str
    service_endpoint: str
    timestamp: datetime


# Import the protocol implementation at the bottom to avoid circular imports
from .protocol import (  # noqa: E402, F401
    X402Config,
    X402PaymentProtocol,
    create_mainnet_config,
    create_testnet_config,
)

__all__ = [
    "X402PaymentProtocol",
    "X402Config",
    "X402Network",
    "PaymentStatus",
    "ServiceRequest",
    "ServiceResponse",
    "ServiceDiscoveryRequest",
    "ServiceOffer",
    "PaymentNotification",
    "create_testnet_config",
    "create_mainnet_config",
]
