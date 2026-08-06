#!/usr/bin/env python3
"""
x402 Buyer Agent Example

This agent demonstrates how to discover and purchase services using the x402 protocol.
It acts as a customer that finds services from other agents and automatically handles
the payment process.

Features:
- Service discovery from other agents
- Automatic x402 payment handling
- Multiple service purchases
- Transaction tracking

To run:
    python buyer_agent.py

The agent will:
1. Discover available paid services
2. Purchase services from seller agents
3. Handle x402 payments automatically
4. Display results and transaction history

Make sure to run seller_agent.py first!
"""

import asyncio
import logging
import os

from uagents import Agent, Context
from uagents.contrib.protocols.x402_payments import (
    ServiceDiscoveryRequest,
    ServiceOffer,
    ServiceRequest,
    ServiceResponse,
    X402PaymentProtocol,
    create_testnet_config,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the buyer agent
buyer = Agent(
    name="ai-services-buyer",
    seed="buyer agent secret seed phrase for x402 demo",
    port=8002,
    endpoint=["http://127.0.0.1:8002/submit"],
)

# Initialize x402 payment protocol with secure config
# Get private key from environment for security
private_key = os.getenv("BUYER_PRIVATE_KEY")
if not private_key:
    print("⚠️  No BUYER_PRIVATE_KEY environment variable found.")
    print("   A new wallet will be generated. Save the private key from the logs!")
    print("   For production, set: export BUYER_PRIVATE_KEY=0x...")
    print("")

payment_config = create_testnet_config(wallet_private_key=private_key)
payment_protocol = X402PaymentProtocol(payment_config)

# Add payment capability to the agent
buyer.include(payment_protocol)

print("🛒 Buyer Agent Starting...")
print(f"💰 Wallet Address: {payment_protocol.account.address}")
print(f"🌐 Network: {payment_config.network}")
print(f"📡 Agent Address: {buyer.address}")
print(f"⚠️  Save this private key: {payment_config.wallet_private_key}")
print("-" * 60)


# Agent state for tracking discoveries and purchases
class AgentState:
    def __init__(self):
        self.discovered_services: list[ServiceOffer] = []
        self.purchase_results: list[dict] = []


agent_state = AgentState()


@buyer.on_message(model=ServiceOffer)
async def handle_service_offer(ctx: Context, sender: str, msg: ServiceOffer):
    """Handle service offers from discovery requests"""
    logger.info(f"📝 Discovered service: {msg.name} - {msg.price} from {sender}")
    agent_state.discovered_services.append(msg)


@buyer.on_message(model=ServiceResponse)
async def handle_service_response(ctx: Context, sender: str, msg: ServiceResponse):
    """Handle responses from purchased services"""
    if msg.success:
        logger.info("✅ Service purchase successful!")
        logger.info(f"   Payment: {msg.payment_made}")
        logger.info(f"   Result: {str(msg.data)[:100]}...")

        agent_state.purchase_results.append(
            {
                "request_id": msg.request_id,
                "success": True,
                "payment": msg.payment_made,
                "data": msg.data,
                "seller": sender,
            }
        )
    else:
        logger.error(f"❌ Service purchase failed: {msg.error}")
        agent_state.purchase_results.append(
            {
                "request_id": msg.request_id,
                "success": False,
                "error": msg.error,
                "seller": sender,
            }
        )


async def discover_services(ctx: Context, category: str = None):
    """Discover available services"""
    logger.info(f"🔍 Discovering services in category: {category or 'all'}")

    # Get list of known agents (in real scenario, this would come from agent registry)
    # For demo, we'll use the seller agent address
    seller_address = "agent1qfzwpu8jcz9gc5r3rzzwzje9ra3j43nxyzsjgpkae5ygccezaawtqr3uwlf"

    discovery_request = ServiceDiscoveryRequest(
        query_id=f"discovery_{ctx.agent.address}_{asyncio.get_event_loop().time()}",
        category=category,
        max_price="$0.02",  # Willing to pay up to 2 cents
    )

    # In a real implementation, this would broadcast to multiple agents
    # For demo, we'll send directly to known seller
    await ctx.send(seller_address, discovery_request)

    # Wait a bit for responses
    await asyncio.sleep(2)


async def purchase_service(ctx: Context, service: ServiceOffer, params: dict):
    """Purchase a specific service"""
    logger.info(f"💳 Purchasing service: {service.name}")

    request_id = f"purchase_{ctx.agent.address}_{asyncio.get_event_loop().time()}"

    service_request = ServiceRequest(
        request_id=request_id,
        service_endpoint=service.endpoint,
        params=params,
        max_payment=service.price,
    )

    await ctx.send(service.provider_address, service_request)


@buyer.on_event("startup")
async def startup_handler(ctx: Context):
    """Handle agent startup"""
    logger.info("🚀 Buyer agent started!")
    logger.info("💡 Will discover and purchase services from other agents")


@buyer.on_interval(period=15.0)
async def automated_shopping(ctx: Context):
    """Periodically discover and purchase services"""
    # Clear previous discoveries for fresh search
    agent_state.discovered_services = []

    # Discover different types of services
    categories = ["data", "ai", "finance", "utility"]
    for category in categories:
        await discover_services(ctx, category)
        await asyncio.sleep(1)  # Small delay between discoveries

    # Wait for discovery responses
    await asyncio.sleep(3)

    if not agent_state.discovered_services:
        logger.info("🤷 No services discovered this round")
        return

    logger.info(
        f"🎯 Found {len(agent_state.discovered_services)} services, making purchases..."
    )

    # Purchase some services
    for service in agent_state.discovered_services[:3]:  # Buy first 3 services found
        try:
            if service.name == "get_weather":
                await purchase_service(ctx, service, {"location": "San Francisco"})
            elif service.name == "get_stock_price":
                await purchase_service(ctx, service, {"symbol": "AAPL"})
            elif service.name == "ai_chat":
                await purchase_service(
                    ctx,
                    service,
                    {"message": "What is the meaning of life?", "max_tokens": 100},
                )
            elif service.name == "echo_service":
                await purchase_service(ctx, service, {"text": "Hello x402 payments!"})

            await asyncio.sleep(1)  # Delay between purchases

        except Exception as e:
            logger.error(f"Failed to purchase {service.name}: {e}")


@buyer.on_interval(period=45.0)
async def show_purchase_summary(ctx: Context):
    """Show summary of purchases"""
    if not agent_state.purchase_results:
        return

    successful = [r for r in agent_state.purchase_results if r["success"]]
    failed = [r for r in agent_state.purchase_results if not r["success"]]

    logger.info("📊 Purchase Summary:")
    logger.info(f"   ✅ Successful: {len(successful)}")
    logger.info(f"   ❌ Failed: {len(failed)}")

    if successful:
        total_spent = 0
        logger.info("   Recent successful purchases:")
        for result in successful[-3:]:  # Show last 3
            payment = result.get("payment", "$0")
            logger.info(f"     • Payment: {payment}")
            if payment and payment.startswith("$"):
                total_spent += float(payment[1:])

        logger.info(f"   💰 Total spent: ${total_spent:.4f}")

    # Clear old results to avoid memory buildup
    if len(agent_state.purchase_results) > 20:
        agent_state.purchase_results = agent_state.purchase_results[-10:]


@buyer.on_interval(period=60.0)
async def wallet_status(ctx: Context):
    """Check wallet status"""
    try:
        balance = await payment_protocol.get_wallet_balance()
        logger.info(f"💳 Wallet: {balance['address'][:10]}... on {balance['network']}")

        # Show transaction history
        history = await payment_protocol.get_transaction_history()
        if history:
            logger.info(f"📋 Transaction history: {len(history)} transactions")

    except Exception as e:
        logger.error(f"Failed to get wallet status: {e}")


if __name__ == "__main__":
    print("Starting x402 Buyer Agent...")
    print("This agent will discover and purchase services:")
    print("• Weather data")
    print("• Stock prices")
    print("• AI chat responses")
    print("• Echo testing")
    print("\nMake sure seller_agent.py is running first!")
    print("The agent will automatically discover and purchase services.")
    print("\nPress Ctrl+C to stop")

    buyer.run()
