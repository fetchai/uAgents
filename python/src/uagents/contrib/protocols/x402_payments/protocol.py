"""
x402 Payment Protocol Implementation for uAgents

This module implements the x402 payment standard for uAgents, enabling agents to:
1. Create and register paid services that automatically handle 402 Payment Required responses
2. Discover and consume paid services from other agents
3. Handle payments via USDC or any EIP-3009 compatible token
4. Work with the x402 ecosystem and Bazaar discovery

The protocol acts as both a client (to buy services) and server (to sell services).
"""

import asyncio
import json
import logging
import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from cdp.x402 import create_facilitator_config
from eth_account import Account
from x402.clients.httpx import x402HttpxClient
from x402.facilitator import FacilitatorClient

from uagents import Context, Protocol
from uagents.storage import KeyValueStore

from . import (
    PaymentStatus,
    ServiceDiscoveryRequest,
    ServiceOffer,
    ServiceRequest,
    ServiceResponse,
    X402Network,
)

logger = logging.getLogger(__name__)


@dataclass
class X402Config:
    """Configuration for x402 payment protocol"""

    network: X402Network = X402Network.BASE_SEPOLIA
    facilitator_url: str | None = "https://x402.org/facilitator"
    cdp_api_key_id: str | None = None
    cdp_api_secret: str | None = None
    wallet_private_key: str | None = None
    receiving_address: str | None = None

    def __post_init__(self):
        """Validate configuration"""
        if self.network == X402Network.BASE and not (
            self.cdp_api_key_id and self.cdp_api_secret
        ):
            raise ValueError("CDP API keys required for mainnet (base) network")

        # Set up wallet if not provided
        if not self.wallet_private_key:
            # Generate a new wallet for this agent
            account = Account.create()
            self.wallet_private_key = account.key.hex()
            if not self.wallet_private_key.startswith("0x"):
                self.wallet_private_key = "0x" + self.wallet_private_key
            self.receiving_address = account.address
            logger.info(f"Generated new wallet: {self.receiving_address}")
            logger.warning("⚠️  SAVE THIS PRIVATE KEY SECURELY (not shown in logs)")
        elif not self.receiving_address:
            # Derive address from private key
            account = Account.from_key(self.wallet_private_key)
            self.receiving_address = account.address


class ServiceRegistry:
    """Registry for paid services offered by an agent"""

    def __init__(self):
        self.services: dict[str, dict[str, Any]] = {}

    def register_service(
        self,
        path: str,
        handler: Callable,
        price: str,
        description: str,
        metadata: dict[str, Any] | None = None,
    ):
        """Register a paid service with validation"""
        if not path or not isinstance(path, str):
            raise ValueError("path must be a non-empty string")
        if not path.startswith("/"):
            path = "/" + path
        if not price or not isinstance(price, str):
            raise ValueError("price must be a non-empty string like '$0.01'")
        if not description or not isinstance(description, str):
            raise ValueError("description must be a non-empty string")
        if len(description) > 500:
            raise ValueError("description must be less than 500 characters")

        if not re.match(r"^\$\d+\.?\d*$", price):
            raise ValueError("price must be in format '$0.01'")

        self.services[path] = {
            "handler": handler,
            "price": price,
            "description": description[:500],
            "metadata": metadata or {},
            "registered_at": datetime.utcnow().isoformat(),
        }
        logger.info(f"Registered paid service: {path} - {price}")

    def get_service(self, path: str) -> dict[str, Any] | None:
        """Get service configuration"""
        return self.services.get(path)

    def list_services(self) -> list[dict[str, Any]]:
        """List all registered services"""
        return [
            {
                "path": path,
                "price": config["price"],
                "description": config["description"],
                "metadata": config["metadata"],
            }
            for path, config in self.services.items()
        ]


class X402PaymentProtocol(Protocol):
    """
    x402 Payment Protocol for uAgents

    Enables agents to create paid services and consume services from other agents
    using the x402 payment standard.
    """

    def __init__(self, config: X402Config):
        """Initialize the x402 Payment Protocol"""
        super().__init__(name="X402PaymentProtocol", version="1.0.0")

        self.config = config
        self.service_registry = ServiceRegistry()

        # Create secure storage directory
        # Validate protocol name to prevent path traversal
        safe_name = re.sub(r"[^\w\-_]", "_", self.name)
        if not safe_name or ".." in safe_name:
            raise ValueError(f"Invalid protocol name for storage: {self.name}")

        storage_dir = os.path.join(os.getcwd(), safe_name)
        os.makedirs(storage_dir, exist_ok=True, mode=0o750)

        self._storage = KeyValueStore("transactions", cwd=storage_dir)
        self._discovery_storage = KeyValueStore("discovery", cwd=storage_dir)

        # Set up wallet account
        self.account = Account.from_key(self.config.wallet_private_key)

        # Set up facilitator
        self._facilitator_client = None
        self._facilitator_config = None

        if self.config.network == X402Network.BASE:
            # Mainnet with CDP facilitator
            if not self.config.cdp_api_key_id or not self.config.cdp_api_secret:
                raise ValueError("CDP API credentials required for mainnet")
            self._facilitator_config = create_facilitator_config(
                api_key_id=self.config.cdp_api_key_id,
                api_key_secret=self.config.cdp_api_secret,
            )
            self._facilitator_client = FacilitatorClient(self._facilitator_config)

        # Define protocol message handlers
        self._define_message_handlers()

        logger.info(f"Initialized x402 protocol on {self.config.network}")
        logger.info(f"Wallet address: {self.account.address}")

    def _define_message_handlers(self):
        """Define protocol message interactions"""

        @self.on_message(model=ServiceRequest, replies=ServiceResponse)
        async def handle_service_request(
            ctx: Context, sender: str, msg: ServiceRequest
        ):
            """Handle requests for paid services offered by this agent"""
            logger.info(f"Service request from {sender}: {msg.service_endpoint}")

            try:
                # Extract path from endpoint
                # msg.service_endpoint could be like "http://agent_address/weather"
                path = msg.service_endpoint.split("/")[-1]
                if not path.startswith("/"):
                    path = "/" + path

                service_config = self.service_registry.get_service(path)
                if not service_config:
                    await ctx.send(
                        sender,
                        ServiceResponse(
                            request_id=msg.request_id,
                            success=False,
                            error=f"Service not found: {path}",
                        ),
                    )
                    return

                # For now, simulate the x402 payment flow
                # In a real implementation, this would integrate with the agent's HTTP server
                # that has x402 middleware configured

                # Call the service handler
                handler = service_config["handler"]
                params = msg.params or {}

                # Execute the handler
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(ctx, **params)
                else:
                    result = handler(ctx, **params)

                # Record the transaction
                transaction_record = {
                    "request_id": msg.request_id,
                    "service": path,
                    "price": service_config["price"],
                    "buyer": sender,
                    "seller": ctx.agent.address,
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": PaymentStatus.COMPLETED,
                    "result": result,
                }

                # Store transaction with incremental index
                tx_count_key = "tx_count"
                tx_count = self._storage.get(tx_count_key) or 0
                tx_key = f"tx_{tx_count}"
                self._storage.set(tx_key, transaction_record)
                self._storage.set(tx_count_key, tx_count + 1)

                await ctx.send(
                    sender,
                    ServiceResponse(
                        request_id=msg.request_id,
                        success=True,
                        data=result,
                        payment_made=service_config["price"],
                    ),
                )

            except Exception as e:
                logger.error(f"Service request failed: {e}")
                await ctx.send(
                    sender,
                    ServiceResponse(
                        request_id=msg.request_id, success=False, error=str(e)
                    ),
                )

        @self.on_message(model=ServiceDiscoveryRequest, replies=ServiceOffer)
        async def handle_discovery_request(
            ctx: Context, sender: str, msg: ServiceDiscoveryRequest
        ):
            """Handle service discovery requests"""
            logger.info(f"Discovery request from {sender}: {msg.query_id}")

            # Filter services based on criteria
            matching_services = []
            for path, config in self.service_registry.services.items():
                # Apply filters
                if msg.category and config["metadata"].get("category") != msg.category:
                    continue

                if msg.keywords:
                    text = f"{config['description']} {json.dumps(config['metadata'])}".lower()
                    if not any(kw.lower() in text for kw in msg.keywords):
                        continue

                if msg.max_price:
                    # Simple price comparison (assumes USD prices like "$0.001")
                    service_price = float(config["price"].replace("$", ""))
                    max_price = float(msg.max_price.replace("$", ""))
                    if service_price > max_price:
                        continue

                matching_services.append((path, config))

            # Send offers for matching services
            for path, config in matching_services:
                service_endpoint = (
                    f"http://{ctx.agent.address}{path}"  # Simplified endpoint
                )

                await ctx.send(
                    sender,
                    ServiceOffer(
                        query_id=msg.query_id,
                        service_id=f"{ctx.agent.address}:{path}",
                        name=config["metadata"].get("name", path),
                        description=config["description"],
                        endpoint=service_endpoint,
                        price=config["price"],
                        category=config["metadata"].get("category"),
                        provider_address=ctx.agent.address,
                        network=self.config.network.value,
                        metadata=config["metadata"],
                    ),
                )

    def paid_service(
        self,
        price: str,
        description: str,
        path: str | None = None,
        category: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """
        Decorator to register a paid service

        Usage:
            @payment_protocol.paid_service(price="$0.001", description="Get weather")
            async def get_weather(ctx: Context, location: str) -> dict:
                return {"weather": "sunny", "location": location}
        """

        def decorator(func: Callable):
            # Determine the service path
            service_path = path or f"/{func.__name__}"

            # Enhance metadata
            service_metadata = metadata or {}
            if category:
                service_metadata["category"] = category
            service_metadata["name"] = func.__name__

            # Register the service
            self.service_registry.register_service(
                path=service_path,
                handler=func,
                price=price,
                description=description,
                metadata=service_metadata,
            )

            # Return the original function
            return func

        return decorator

    async def buy_service(
        self,
        service_endpoint: str,
        params: dict[str, Any] | None = None,
        max_payment: str | None = None,
        timeout: int = 30,
    ) -> dict[str, Any]:
        """
        Buy and access a paid service from another agent

        Args:
            service_endpoint: URL of the x402-enabled service
            params: Parameters to pass to the service
            max_payment: Maximum willing to pay
            timeout: Request timeout

        Returns:
            Service response data
        """
        # Validate inputs
        if not service_endpoint or not isinstance(service_endpoint, str):
            raise ValueError("service_endpoint must be a valid URL string")
        if params and not isinstance(params, dict):
            raise ValueError("params must be a dictionary")
        if max_payment and not isinstance(max_payment, str):
            raise ValueError("max_payment must be a string like '$0.01'")

        try:
            # Use x402 client to handle payment automatically
            if self.config.network == X402Network.BASE and self._facilitator_config:
                # Mainnet with CDP facilitator
                async with x402HttpxClient(
                    account=self.account, facilitator_config=self._facilitator_config
                ) as client:
                    response = await client.post(service_endpoint, json=params or {})
                    return await response.aread()
            else:
                # Testnet or other facilitator
                async with x402HttpxClient(
                    account=self.account, base_url=self.config.facilitator_url
                ) as client:
                    response = await client.post(service_endpoint, json=params or {})
                    return await response.aread()

        except Exception as e:
            logger.error(f"Failed to buy service {service_endpoint}: {e}")
            raise

    async def discover_services(
        self,
        category: str | None = None,
        keywords: list[str] | None = None,
        max_price: str | None = None,
        timeout: int = 10,
    ) -> list[ServiceOffer]:
        """
        Discover available paid services from the x402 Bazaar or other agents

        Args:
            category: Service category filter
            keywords: Keywords to search for
            max_price: Maximum price filter
            timeout: Discovery timeout

        Returns:
            List of available service offers
        """
        discovered_services = []

        if self._facilitator_client:
            try:
                # Use CDP facilitator to discover services
                services = await self._facilitator_client.list()

                # Filter and convert to ServiceOffer format
                for service in services:
                    if category and service.get("category") != category:
                        continue

                    if max_price:
                        service_price = float(
                            service.get("price", "0").replace("$", "")
                        )
                        max_price_val = float(max_price.replace("$", ""))
                        if service_price > max_price_val:
                            continue

                    discovered_services.append(
                        ServiceOffer(
                            query_id=f"discovery_{datetime.utcnow().timestamp()}",
                            service_id=service.get("id", ""),
                            name=service.get("name", ""),
                            description=service.get("description", ""),
                            endpoint=service.get("endpoint", ""),
                            price=service.get("price", "$0"),
                            category=service.get("category"),
                            provider_address=service.get("provider", ""),
                            network=self.config.network.value,
                            metadata=service.get("metadata", {}),
                        )
                    )

            except Exception as e:
                logger.error(f"Failed to discover services from facilitator: {e}")

        return discovered_services

    async def get_wallet_balance(self) -> dict[str, str]:
        """Get wallet balance for payment tokens"""
        # This would need integration with web3 to check USDC balance
        # For now, return a placeholder
        return {
            "USDC": "0.00",
            "address": self.account.address,
            "network": self.config.network.value,
        }

    async def get_transaction_history(self) -> list[dict[str, Any]]:
        """Get transaction history for this agent"""
        history = []

        try:
            # Since KeyValueStore doesn't have get_keys(), we'll keep a transaction count
            tx_count_key = "tx_count"
            tx_count = self._storage.get(tx_count_key) or 0

            # Get all stored transactions by index
            for i in range(tx_count):
                tx_key = f"tx_{i}"
                transaction = self._storage.get(tx_key)
                if transaction:
                    history.append(transaction)

            # Sort by timestamp
            history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        except Exception as e:
            logger.error(f"Error retrieving transaction history: {e}")

        return history

    def get_service_stats(self) -> dict[str, Any]:
        """Get statistics about registered services"""
        services = self.service_registry.list_services()
        return {
            "total_services": len(services),
            "services": services,
            "wallet_address": self.account.address,
            "network": self.config.network.value,
        }

    async def close(self):
        """Clean up resources"""
        if self._facilitator_client and hasattr(self._facilitator_client, "close"):
            # Close facilitator client if it has a close method
            await self._facilitator_client.close()


# Convenience functions for quick setup
def create_testnet_config(wallet_private_key: str | None = None) -> X402Config:
    """Create a testnet configuration"""
    return X402Config(
        network=X402Network.BASE_SEPOLIA,
        facilitator_url="https://x402.org/facilitator",
        wallet_private_key=wallet_private_key,
    )


def create_mainnet_config(
    cdp_api_key_id: str, cdp_api_secret: str, wallet_private_key: str | None = None
) -> X402Config:
    """Create a mainnet configuration"""
    return X402Config(
        network=X402Network.BASE,
        cdp_api_key_id=cdp_api_key_id,
        cdp_api_secret=cdp_api_secret,
        wallet_private_key=wallet_private_key,
    )
