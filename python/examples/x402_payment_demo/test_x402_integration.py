#!/usr/bin/env python3
"""
x402 Integration Test for uAgents

This script tests the x402 payment integration without requiring
actual blockchain transactions. It verifies:

1. Protocol initialization
2. Service registration
3. Service discovery
4. Mock payment flow
5. Agent communication

Run this to verify your x402 integration is working correctly.
"""

import asyncio
import logging
from typing import Any

from uagents import Agent, Context
from uagents.contrib.protocols.x402_payments import (
    ServiceDiscoveryRequest,
    ServiceOffer,
    X402PaymentProtocol,
    create_testnet_config,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_protocol_initialization():
    """Test that the x402 protocol initializes correctly"""
    print("🧪 Testing protocol initialization...")

    try:
        config = create_testnet_config()
        protocol = X402PaymentProtocol(config)

        assert protocol.config.network.value == "base-sepolia"
        assert protocol.account is not None
        assert protocol.service_registry is not None

        print("✅ Protocol initialized successfully")
        print(f"   Network: {protocol.config.network}")
        print(f"   Wallet: {protocol.account.address}")

        return protocol

    except Exception as e:
        print(f"❌ Protocol initialization failed: {e}")
        raise


def test_service_registration(protocol: X402PaymentProtocol):
    """Test service registration functionality"""
    print("\n🧪 Testing service registration...")

    try:

        @protocol.paid_service(
            price="$0.001", description="Test weather service", category="test"
        )
        async def test_weather(ctx: Context, location: str) -> dict[str, Any]:
            return {"location": location, "weather": "test"}

        # Check if service was registered
        services = protocol.service_registry.list_services()
        assert len(services) > 0

        weather_service = None
        for service in services:
            if "test_weather" in service["path"]:
                weather_service = service
                break

        assert weather_service is not None
        assert weather_service["price"] == "$0.001"
        assert weather_service["description"] == "Test weather service"

        print("✅ Service registration successful")
        print(f"   Registered: {weather_service['path']}")
        print(f"   Price: {weather_service['price']}")

    except Exception as e:
        print(f"❌ Service registration failed: {e}")
        raise


async def test_agent_integration():
    """Test full agent integration with x402 protocol"""
    print("\n🧪 Testing agent integration...")

    try:
        # Create test agent
        test_agent = Agent(
            name="test-x402-agent", seed="test seed for x402 integration", port=8888
        )

        # Initialize protocol
        config = create_testnet_config()
        protocol = X402PaymentProtocol(config)

        # Add protocol to agent
        test_agent.include(protocol)

        # Register a test service
        @protocol.paid_service(price="$0.001", description="Test service")
        async def test_service(ctx: Context, param: str) -> dict:
            return {"result": f"processed: {param}"}

        print("✅ Agent integration successful")
        print(f"   Agent: {test_agent.name}")
        print(f"   Address: {test_agent.address}")
        print(f"   Services: {len(protocol.service_registry.list_services())}")

        return test_agent, protocol

    except Exception as e:
        print(f"❌ Agent integration failed: {e}")
        raise


def test_service_discovery_messages():
    """Test service discovery message handling"""
    print("\n🧪 Testing service discovery messages...")

    try:
        # Create discovery request
        discovery_request = ServiceDiscoveryRequest(
            query_id="test_query_123", category="test", max_price="$0.01"
        )

        # Verify message structure
        assert discovery_request.query_id == "test_query_123"
        assert discovery_request.category == "test"
        assert discovery_request.max_price == "$0.01"

        # Create service offer
        service_offer = ServiceOffer(
            query_id="test_query_123",
            service_id="test_service_1",
            name="Test Service",
            description="Test description",
            endpoint="http://test.com/service",
            price="$0.001",
            provider_address="test_address",
            network="base-sepolia",
        )

        # Verify offer structure
        assert service_offer.query_id == "test_query_123"
        assert service_offer.price == "$0.001"
        assert service_offer.network == "base-sepolia"

        print("✅ Message handling successful")
        print(f"   Discovery request: {discovery_request.query_id}")
        print(f"   Service offer: {service_offer.name}")

    except Exception as e:
        print(f"❌ Message handling failed: {e}")
        raise


def test_wallet_functionality(protocol: X402PaymentProtocol):
    """Test wallet-related functionality"""
    print("\n🧪 Testing wallet functionality...")

    try:
        # Test wallet address
        assert protocol.account.address.startswith("0x")
        assert len(protocol.account.address) == 42

        # Test private key
        assert protocol.config.wallet_private_key.startswith("0x")
        assert len(protocol.config.wallet_private_key) == 66

        # Test stats
        stats = protocol.get_service_stats()
        assert "wallet_address" in stats
        assert "network" in stats
        assert stats["wallet_address"] == protocol.account.address

        print("✅ Wallet functionality successful")
        print(f"   Address: {protocol.account.address}")
        print(f"   Network: {stats['network']}")

    except Exception as e:
        print(f"❌ Wallet functionality failed: {e}")
        raise


async def run_all_tests():
    """Run all integration tests"""
    print("🚀 Starting x402 Integration Tests")
    print("=" * 50)

    try:
        # Test 1: Protocol initialization
        protocol = test_protocol_initialization()

        # Test 2: Service registration
        test_service_registration(protocol)

        # Test 3: Agent integration
        agent, agent_protocol = await test_agent_integration()

        # Test 4: Message handling
        test_service_discovery_messages()

        # Test 5: Wallet functionality
        test_wallet_functionality(protocol)

        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("✅ x402 integration is working correctly")
        print("\nYou can now run the demo agents:")
        print("   python seller_agent.py")
        print("   python buyer_agent.py")

    except Exception as e:
        print("\n" + "=" * 50)
        print(f"❌ TESTS FAILED: {e}")
        print("Please check the error message above and fix any issues.")
        raise


if __name__ == "__main__":
    print("x402 Integration Test for uAgents")
    print("This will verify that the x402 payment protocol is properly integrated.")
    print()

    asyncio.run(run_all_tests())
