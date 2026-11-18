#!/usr/bin/env python3
"""
x402 Seller Agent Example

This agent demonstrates how to create paid services using the x402 protocol.
The agent offers multiple services (weather, stock prices, AI chat) that other
agents can discover and purchase.

Features:
- Multiple paid services with different prices
- Automatic x402 payment handling
- Service discovery support
- Transaction history tracking

To run:
    python seller_agent.py

The agent will:
1. Register paid services
2. Listen for service discovery requests
3. Handle payment and service requests
4. Log all transactions
"""

import logging
import os
from typing import Any

from uagents import Agent, Context
from uagents.contrib.protocols.x402_payments import (
    X402PaymentProtocol,
    create_testnet_config,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the seller agent
seller = Agent(
    name="ai-services-seller",
    seed="seller agent secret seed phrase for x402 demo",
    port=8001,
    endpoint=["http://127.0.0.1:8001/submit"],
)

# Initialize x402 payment protocol with secure config
# Get private key from environment for security
private_key = os.getenv("SELLER_PRIVATE_KEY")
if not private_key:
    print("⚠️  No SELLER_PRIVATE_KEY environment variable found.")
    print("   A new wallet will be generated. Save the private key from the logs!")
    print("   For production, set: export SELLER_PRIVATE_KEY=0x...")
    print("")

payment_config = create_testnet_config(wallet_private_key=private_key)
payment_protocol = X402PaymentProtocol(payment_config)

# Add payment capability to the agent
seller.include(payment_protocol)

print("🏪 Seller Agent Starting...")
print(f"💰 Wallet Address: {payment_protocol.account.address}")
print(f"🌐 Network: {payment_config.network}")
print(f"📡 Agent Address: {seller.address}")
print(f"⚠️  Save this private key: {payment_config.wallet_private_key}")
print("-" * 60)


# Register paid services using the decorator
@payment_protocol.paid_service(
    price="$0.001",  # 0.1 cent per request
    description="Get real-time weather data for any location worldwide",
    category="data",
    metadata={
        "response_time": "< 1s",
        "accuracy": "high",
        "data_source": "OpenWeatherMap",
    },
)
async def get_weather(ctx: Context, location: str) -> dict[str, Any]:
    """Weather service - returns weather data for a location"""
    logger.info(f"⛅ Weather request for: {location}")

    # Simulate weather API call
    weather_data = {
        "location": location,
        "weather": "sunny",
        "temperature": 72,
        "humidity": 45,
        "wind_speed": 8,
        "forecast": ["sunny", "partly_cloudy", "sunny"],
        "timestamp": "2024-01-15T10:30:00Z",
    }

    return weather_data


@payment_protocol.paid_service(
    price="$0.005",  # 0.5 cents per request
    description="Get current stock price and basic financial data",
    category="finance",
    metadata={
        "response_time": "< 2s",
        "data_source": "Yahoo Finance",
        "includes": ["price", "volume", "market_cap"],
    },
)
async def get_stock_price(ctx: Context, symbol: str) -> dict[str, Any]:
    """Stock price service - returns financial data for a stock symbol"""
    logger.info(f"📈 Stock price request for: {symbol}")

    # Simulate stock API call
    stock_data = {
        "symbol": symbol.upper(),
        "price": 150.25,
        "change": "+2.34",
        "change_percent": "+1.58%",
        "volume": 1250000,
        "market_cap": "2.5T",
        "timestamp": "2024-01-15T10:30:00Z",
    }

    return stock_data


@payment_protocol.paid_service(
    price="$0.01",  # 1 cent per request
    description="AI-powered chat and question answering service",
    category="ai",
    metadata={"model": "GPT-4", "max_tokens": 500, "response_time": "< 5s"},
)
async def ai_chat(ctx: Context, message: str, max_tokens: int = 150) -> dict[str, Any]:
    """AI chat service - provides AI-powered responses"""
    logger.info(f"🤖 AI chat request: {message[:50]}...")

    # Simulate AI API call
    ai_response = {
        "message": message,
        "response": (
            f"I understand you're asking about '{message}'. "
            "This is a simulated AI response that would normally come from a language model. "
            "The service is working correctly!"
        ),
        "tokens_used": min(max_tokens, 75),
        "model": "GPT-4",
        "timestamp": "2024-01-15T10:30:00Z",
    }

    return ai_response


@payment_protocol.paid_service(
    price="$0.0001",  # Very cheap for testing
    description="Simple echo service for testing x402 payments",
    category="utility",
    metadata={"response_time": "< 100ms", "use_case": "testing"},
)
async def echo_service(ctx: Context, text: str) -> dict[str, Any]:
    """Echo service - returns the input text"""
    logger.info(f"🔄 Echo request: {text}")

    return {
        "original": text,
        "echo": f"Echo: {text}",
        "timestamp": "2024-01-15T10:30:00Z",
        "service": "echo",
    }


@seller.on_event("startup")
async def startup_handler(ctx: Context):
    """Handle agent startup"""
    logger.info("🚀 Seller agent started!")

    # Display service catalog
    services = payment_protocol.service_registry.list_services()
    logger.info(f"📋 Registered {len(services)} paid services:")

    for service in services:
        logger.info(
            f"  • {service['path']} - {service['price']} - {service['description']}"
        )

    logger.info("💼 Ready to serve customers!")


@seller.on_interval(period=30.0)
async def log_stats(ctx: Context):
    """Periodically log service statistics"""
    stats = payment_protocol.get_service_stats()
    history = await payment_protocol.get_transaction_history()

    logger.info(
        f"📊 Stats: {stats['total_services']} services, {len(history)} transactions"
    )

    if history:
        recent = history[0]
        logger.info(f"   Last sale: {recent.get('service')} for {recent.get('price')}")


if __name__ == "__main__":
    print("Starting x402 Seller Agent...")
    print("This agent offers paid AI services:")
    print("• Weather data ($0.001)")
    print("• Stock prices ($0.005)")
    print("• AI chat ($0.01)")
    print("• Echo service ($0.0001)")
    print("\nOther agents can discover and purchase these services!")
    print("\nPress Ctrl+C to stop")

    seller.run()
