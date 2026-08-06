# x402 Payment Protocol for uAgents

A production-ready payment protocol that enables uAgents to buy and sell services using the x402 standard. This protocol adds cryptocurrency payment capabilities to any uAgent with just a few lines of code.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Security & Production Readiness](#security--production-readiness)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [API Reference](#api-reference)
- [Network Support](#network-support)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Overview

The x402 Payment Protocol integrates [x402](https://x402.dev) - a web standard for cryptocurrency payments - with the uAgents framework. This enables agents to:

- **Sell services**: Automatically charge USDC for API calls and services
- **Buy services**: Discover and purchase services from other agents
- **Gasless payments**: All transactions sponsored by facilitators (no ETH needed)
- **Real crypto**: Uses actual USDC on Base/Base Sepolia networks
- **Production ready**: Built for mainnet with enterprise security

### How it Works

```python
# Add payments to any agent in 3 lines:
payment_protocol = X402PaymentProtocol(create_testnet_config())
agent.include(payment_protocol)

@payment_protocol.paid_service(price="$0.001", description="AI service")
async def my_service(ctx: Context, query: str) -> dict:
    return {"result": "AI response"}
```

1. **Service Registration**: Agents register paid services with `@payment_protocol.paid_service()`
2. **Discovery**: Buyers find services through automated discovery or x402 Bazaar
3. **Payment**: x402 handles 402 Payment Required responses automatically
4. **Settlement**: USDC transfers happen via EIP-3009 signatures (gasless)

## Features

### 🚀 **Core Capabilities**
- ✅ **Automatic Payment Handling** - 402 Payment Required responses handled seamlessly
- ✅ **Service Discovery** - Find paid services across the agent network
- ✅ **Real Cryptocurrency** - USDC payments on Base/Base Sepolia
- ✅ **Gasless Transactions** - No ETH required for buyers or sellers
- ✅ **Transaction History** - Complete audit trail of all payments
- ✅ **Multi-Network** - Base mainnet, Base Sepolia, XDC support

### 💰 **Payment Features**
- ✅ **Flexible Pricing** - Support for micro-payments ($0.0001+)
- ✅ **Multiple Categories** - Organize services by type (AI, data, finance, etc.)
- ✅ **Metadata Support** - Rich service descriptions and schemas
- ✅ **Price Validation** - Automatic price format verification


## Quick Start

### 1. Install Dependencies

```bash
pip install x402 cdp-sdk eth-account httpx python-dotenv
```

### 2. Create a Seller Agent

```python
from uagents import Agent, Context
from uagents.contrib.protocols.x402_payments import (
    X402PaymentProtocol, 
    create_testnet_config
)

# Create agent
seller = Agent(name="ai-weather-service", port=8001)

# Add payment capability
payment_protocol = X402PaymentProtocol(create_testnet_config())
seller.include(payment_protocol)

# Register a paid service
@payment_protocol.paid_service(
    price="$0.001", 
    description="Get real-time weather data"
)
async def get_weather(ctx: Context, location: str) -> dict:
    return {
        "location": location,
        "weather": "sunny",
        "temperature": 72
    }

if __name__ == "__main__":
    seller.run()
```

### 3. Create a Buyer Agent

```python
from uagents import Agent, Context
from uagents.contrib.protocols.x402_payments import (
    X402PaymentProtocol,
    create_testnet_config,
    ServiceDiscoveryRequest
)

# Create buyer agent
buyer = Agent(name="weather-client", port=8002)

# Add payment capability
payment_protocol = X402PaymentProtocol(create_testnet_config())
buyer.include(payment_protocol)

@buyer.on_interval(period=30.0)
async def buy_weather_data(ctx: Context):
    # Discover services
    services = await payment_protocol.discover_services(
        category="data",
        max_price="$0.01"
    )
    
    # Buy from first weather service found
    for service in services:
        if "weather" in service.description.lower():
            result = await payment_protocol.buy_service(
                service_endpoint=service.endpoint,
                params={"location": "San Francisco"}
            )
            ctx.logger.info(f"Weather: {result}")
            break

if __name__ == "__main__":
    buyer.run()
```

## Installation

### Prerequisites

- Python 3.8+
- uAgents framework
- Internet connection for x402 facilitator communication

### Install x402 Dependencies

```bash
# Core x402 packages
pip install x402>=0.1.0
pip install cdp-sdk>=0.1.0

# Supporting packages
pip install eth-account>=0.8.0
pip install httpx>=0.24.0
pip install python-dotenv>=1.0.0
```

### Verify Installation

```python
# Test basic functionality
from uagents.contrib.protocols.x402_payments import X402PaymentProtocol, create_testnet_config

# This should not raise any errors
protocol = X402PaymentProtocol(create_testnet_config())
print(f"✅ x402 protocol initialized on {protocol.config.network}")
```

## Configuration

### Testnet Configuration (Recommended for Development)

```python
from uagents.contrib.protocols.x402_payments import create_testnet_config

# Basic testnet config (Base Sepolia)
config = create_testnet_config()

# With existing wallet
config = create_testnet_config(wallet_private_key="0x...")
```

### Mainnet Configuration (Production)

```python
from uagents.contrib.protocols.x402_payments import create_mainnet_config
import os

# Requires CDP API keys for mainnet
config = create_mainnet_config(
    cdp_api_key_id=os.getenv("CDP_API_KEY_ID"),
    cdp_api_secret=os.getenv("CDP_API_SECRET"),
    wallet_private_key=os.getenv("WALLET_PRIVATE_KEY")  # Optional
)
```

### Environment Variables

For security, use environment variables for all credentials:

```bash
# Testnet (optional)
export SELLER_PRIVATE_KEY="0x..."
export BUYER_PRIVATE_KEY="0x..."

# Mainnet (required)
export CDP_API_KEY_ID="your_cdp_key_id"
export CDP_API_SECRET="your_cdp_secret"
export MAINNET_WALLET_KEY="0x..."
```

## Usage Examples

### Creating Paid Services

```python
# Simple service
@payment_protocol.paid_service(price="$0.001", description="Echo service")
async def echo(ctx: Context, message: str) -> dict:
    return {"echo": message}

# Advanced service with metadata
@payment_protocol.paid_service(
    price="$0.01",
    description="AI-powered text analysis",
    category="ai",
    metadata={
        "model": "GPT-4",
        "max_tokens": 1000,
        "response_time": "< 2s"
    }
)
async def analyze_text(ctx: Context, text: str) -> dict:
    # Your AI processing logic here
    return {
        "sentiment": "positive",
        "entities": ["example"],
        "summary": "Text analysis complete"
    }
```

### Service Discovery & Purchase

```python
# Discover services by category
ai_services = await payment_protocol.discover_services(
    category="ai",
    max_price="$0.05"
)

# Discover by keywords
weather_services = await payment_protocol.discover_services(
    keywords=["weather", "climate"],
    max_price="$0.01"
)

# Purchase a service
result = await payment_protocol.buy_service(
    service_endpoint="https://agent123.com/api/weather",
    params={"location": "London", "units": "metric"},
    max_payment="$0.01"
)
```

### Transaction History

```python
# Get transaction history
history = await payment_protocol.get_transaction_history()

for tx in history:
    print(f"Service: {tx['service']}")
    print(f"Price: {tx['price']}")
    print(f"Status: {tx['status']}")
    print(f"Time: {tx['timestamp']}")
```

### Wallet Management

```python
# Check wallet balance
balance = payment_protocol.get_wallet_balance()
print(f"Address: {balance['address']}")
print(f"Network: {balance['network']}")
print(f"USDC: {balance['USDC']}")

# Get service statistics
stats = payment_protocol.get_service_stats()
print(f"Total services: {stats['total_services']}")
print(f"Total revenue: {stats['total_revenue_usd']}")
print(f"Total transactions: {stats['total_transactions']}")
```

## API Reference

### X402PaymentProtocol Class

#### Constructor
```python
X402PaymentProtocol(config: X402Config)
```

#### Methods

##### `paid_service(price: str, description: str, category: str = None)`
Decorator to register a function as a paid service.

**Parameters:**
- `price` (str): Price in format "$0.001"
- `description` (str): Service description (max 500 chars)
- `category` (str): Optional category ("ai", "data", "finance", "utility")

##### `buy_service(service_endpoint: str, params: dict = None, max_payment: str = None)`
Purchase and access a paid service.

**Parameters:**
- `service_endpoint` (str): Service URL
- `params` (dict): Service parameters
- `max_payment` (str): Maximum willing to pay

**Returns:** Service response data

##### `discover_services(category: str = None, keywords: List[str] = None, max_price: str = None)`
Discover available paid services.

**Returns:** List of ServiceOffer objects

##### `get_transaction_history()`
Get complete transaction history.

**Returns:** List of transaction records

##### `get_wallet_balance()`
Get wallet information and balance.

**Returns:** Dictionary with address, network, and USDC balance

##### `get_service_stats()`
Get statistics about registered services.

**Returns:** Dictionary with service and revenue statistics

### Configuration Classes

#### X402Config
Configuration for the payment protocol.

**Fields:**
- `network`: X402Network enum (BASE_SEPOLIA, BASE, XDC)
- `wallet_private_key`: Optional private key (hex string)
- `receiving_address`: Optional receiving address
- `cdp_api_key_id`: CDP API key ID (required for mainnet)
- `cdp_api_secret`: CDP API secret (required for mainnet)
- `facilitator_url`: Custom facilitator URL

#### Helper Functions

##### `create_testnet_config(wallet_private_key: str = None)`
Create testnet configuration for Base Sepolia.

##### `create_mainnet_config(cdp_api_key_id: str, cdp_api_secret: str, wallet_private_key: str = None)`
Create mainnet configuration for Base.

### Data Models

#### ServiceOffer
Represents an available paid service.

**Fields:**
- `service_id`: Unique service identifier
- `name`: Service name
- `description`: Service description
- `endpoint`: Service URL
- `price`: Price string
- `network`: Network name
- `provider_address`: Provider agent address
- `category`: Service category

#### ServiceRequest
Request to purchase a service.

**Fields:**
- `request_id`: Unique request identifier
- `service_endpoint`: Service URL
- `params`: Service parameters
- `max_payment`: Maximum payment amount

#### ServiceResponse
Response from a service purchase.

**Fields:**
- `request_id`: Request identifier
- `success`: Success boolean
- `data`: Response data
- `error`: Error message (if failed)
- `payment_made`: Payment confirmation

## Network Support

### Supported Networks

| Network | Chain ID | Status | Facilitator | Required Setup |
|---------|----------|--------|-------------|----------------|
| Base Sepolia | 84532 | ✅ Testnet | x402.org | None |
| Base | 8453 | ✅ Mainnet | CDP | CDP API Keys |
| XDC | 50 | ✅ Mainnet | x402.rs | None |

### Network Features

- **Base Sepolia**: Free testnet with x402.org facilitator
- **Base Mainnet**: Production network with CDP facilitator
- **XDC**: Alternative mainnet with community facilitator

### Token Support

All networks support any EIP-3009 compatible token:
- **USDC**: Primary supported token
- **Custom EIP-3009 tokens**: Advanced configuration available

## Security Best Practices

### 🔐 **Wallet Security**

```python
# ✅ DO: Use environment variables
wallet_key = os.getenv("WALLET_PRIVATE_KEY")

# ❌ DON'T: Hardcode private keys
wallet_key = "0x1234..."  # Never do this!
```

### 🔐 **API Key Management**

```python
# ✅ DO: Secure credential management
config = create_mainnet_config(
    cdp_api_key_id=os.getenv("CDP_API_KEY_ID"),
    cdp_api_secret=os.getenv("CDP_API_SECRET")
)

# ❌ DON'T: Embed credentials in code
config = create_mainnet_config("api-key", "secret")  # Never do this!
```

### 🔐 **Input Validation**

All inputs are automatically validated:
- Service endpoints must be valid URLs
- Prices must match `$0.000` format
- Descriptions are length-limited
- Parameters are type-checked

### 🔐 **Error Handling**

```python
try:
    result = await payment_protocol.buy_service(endpoint, params)
except ValueError as e:
    # Handle validation errors
    ctx.logger.error(f"Invalid input: {e}")
except Exception as e:
    # Handle payment/network errors
    ctx.logger.error(f"Payment failed: {e}")
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

```
ImportError: cannot import name 'x402HttpxClient'
```

**Solution**: Install x402 dependencies
```bash
pip install x402 cdp-sdk
```

#### 2. CDP API Errors

```
ValueError: CDP API keys required for mainnet
```

**Solution**: Set environment variables
```bash
export CDP_API_KEY_ID="your_key"
export CDP_API_SECRET="your_secret"
```

#### 3. Wallet Errors

```
Error: Invalid private key format
```

**Solution**: Ensure private key has `0x` prefix
```python
# Correct format
wallet_key = "0x1234567890abcdef..."
```

#### 4. Network Connection Issues

```
Error: Failed to connect to facilitator
```

**Solution**: Check internet connection and network configuration:
- Testnet: Uses x402.org (no configuration needed)
- Mainnet: Uses CDP facilitator (requires API keys)

#### 5. Transaction Failures

```
Error: Transaction failed
```

**Debugging steps:**
1. Check wallet has sufficient USDC balance
2. Verify service endpoint is accessible
3. Confirm price is within max_payment limit
4. Check transaction history for details

### Debug Logging

Enable detailed logging:

```python
import logging
logging.getLogger("uagents.contrib.protocols.x402_payments").setLevel(logging.DEBUG)
```

### Testing Connectivity

```python
# Test protocol initialization
from uagents.contrib.protocols.x402_payments import X402PaymentProtocol, create_testnet_config

try:
    protocol = X402PaymentProtocol(create_testnet_config())
    print("✅ Protocol initialized successfully")
    
    # Test wallet
    balance = protocol.get_wallet_balance()
    print(f"✅ Wallet: {balance['address']}")
    
except Exception as e:
    print(f"❌ Error: {e}")
```

---

**🚀 Ready to monetize your agents with crypto payments? Start with the [Quick Start](#quick-start) guide!**
