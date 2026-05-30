# x402 Payment Demo for uAgents

This demonstration shows how to integrate x402 payments into uAgents, enabling agents to buy and sell services from each other using cryptocurrency payments.

## 🌟 What is x402?

x402 is a payment standard that enables automatic cryptocurrency payments for API access. When you try to access a paid API:

1. **402 Payment Required** - The API responds with payment requirements
2. **Automatic Payment** - Your client automatically pays using USDC (gasless via EIP-3009)
3. **Access Granted** - The API request succeeds with payment proof

## 🏗️ Architecture

```
┌─────────────────┐    Discovery     ┌─────────────────┐
│   Buyer Agent   │ ────────────────► │  Seller Agent   │
│                 │                   │                 │
│ • Discovers     │ ◄──── Offers ──── │ • Weather ($0.001) │
│   services      │                   │ • Stocks ($0.005)  │
│ • Pays via x402 │ ─── Purchase ───► │ • AI Chat ($0.01)  │
│ • Gets results  │ ◄─── Results ──── │ • Echo ($0.0001)   │
└─────────────────┘                   └─────────────────┘
        │                                       │
        └──────── x402 Facilitator ─────────────┘
               (Handles USDC payments)
```

## 🚀 Quick Start

### Prerequisites

1. **Python 3.11+** with the uAgents project set up
2. **x402 package** (automatically installed with our protocol)
3. **Virtual environment** activated

### Step 1: Run the Seller Agent

The seller agent offers multiple paid services:

```bash
cd examples/x402_payment_demo
python seller_agent.py
```

You'll see output like:
```
🏪 Seller Agent Starting...
💰 Wallet Address: 0x742d35Cc6634C0532925a3b8D431A68a3A5b0B2
🌐 Network: base-sepolia
⚠️  Save this private key: 0x1234567890abcdef...
📋 Registered 4 paid services:
  • /get_weather - $0.001 - Get real-time weather data
  • /get_stock_price - $0.005 - Get current stock price
  • /ai_chat - $0.01 - AI-powered chat service
  • /echo_service - $0.0001 - Simple echo for testing
```

### Step 2: Run the Buyer Agent

The buyer agent discovers and purchases services:

```bash
# In a new terminal
python buyer_agent.py
```

You'll see output like:
```
🛒 Buyer Agent Starting...
💰 Wallet Address: 0x2A5b8C9d123456789abcdef0123456789abcdef0
🔍 Discovering services in category: data
📝 Discovered service: get_weather - $0.001
💳 Purchasing service: get_weather
✅ Service purchase successful!
   Payment: $0.001
   Result: {"location": "San Francisco", "weather": "sunny"...}
```

## 📋 Available Services

The demo includes these services:

| Service | Price | Description |
|---------|-------|-------------|
| Weather | $0.001 | Real-time weather data |
| Stock Price | $0.005 | Current stock prices |
| AI Chat | $0.01 | AI-powered responses |
| Echo | $0.0001 | Simple echo testing |

## 🔧 Configuration

### Testnet (Default)

```python
from uagents.contrib.protocols.x402_payments import create_testnet_config

config = create_testnet_config()
# Uses Base Sepolia testnet with free facilitator at x402.org
```

### Mainnet (Production)

```python
from uagents.contrib.protocols.x402_payments import create_mainnet_config

config = create_mainnet_config(
    cdp_api_key_id="your_cdp_api_key_id",
    cdp_api_secret="your_cdp_api_secret"
)
# Uses Base mainnet with CDP facilitator
```

## 💻 Code Examples

### Creating a Paid Service

```python
@payment_protocol.paid_service(
    price="$0.001",
    description="Get weather data",
    category="data"
)
async def get_weather(ctx: Context, location: str) -> dict:
    return {"weather": "sunny", "location": location}
```

### Purchasing a Service

```python
# Automatic x402 payment handling
result = await payment_protocol.buy_service(
    service_endpoint="http://agent_address/weather",
    params={"location": "New York"}
)
```

### Service Discovery

```python
services = await payment_protocol.discover_services(
    category="ai",
    max_price="$0.05"
)
```

## 🌐 Networks & Tokens

### Supported Networks

- **Base Sepolia** (testnet) - Free facilitator
- **Base** (mainnet) - Requires CDP API keys
- **XDC Network** - Via community facilitators

### Supported Tokens

- **USDC** (default) - USD Coin with EIP-3009 support
- **Any EIP-3009 token** - Must implement `transferWithAuthorization`

## 🔐 Security Features

- **Gasless payments** - Facilitator sponsors gas fees
- **EIP-3009 signatures** - Cryptographically secure transfers
- **Maximum payment limits** - Buyers set spending limits
- **Payment verification** - Sellers verify payments via facilitator

## 🛠️ Advanced Usage

### Custom Service Metadata

```python
@payment_protocol.paid_service(
    price="$0.001",
    description="Premium weather with forecasts",
    metadata={
        "response_time": "< 500ms",
        "data_source": "NOAA",
        "accuracy": "99.9%"
    }
)
async def premium_weather(ctx: Context, location: str) -> dict:
    # Implementation here
    pass
```

### Transaction History

```python
history = await payment_protocol.get_transaction_history()
for tx in history:
    print(f"Service: {tx['service']}, Payment: {tx['price']}")
```

### Wallet Management

```python
balance = await payment_protocol.get_wallet_balance()
print(f"USDC Balance: {balance['USDC']}")
```

## 🐛 Troubleshooting

### Common Issues

1. **"x402 package not available"**
   ```bash
   pip install x402 cdp python-dotenv eth-account
   ```

2. **"CDP API keys required for mainnet"**
   - Sign up at [cdp.coinbase.com](https://cdp.coinbase.com)
   - Generate API credentials
   - Use `create_mainnet_config()`

3. **"Service not found"**
   - Make sure seller agent is running first
   - Check agent addresses in the logs

4. **"Payment failed"**
   - Ensure wallet has sufficient USDC balance
   - Check network configuration

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🌍 Real-World Integration

This demo shows the concept, but for production:

1. **HTTP Server Integration** - Integrate with FastAPI/Flask using x402 middleware
2. **Real Payment Processing** - Fund wallets with USDC for actual payments
3. **Service Registry** - Use proper service discovery mechanisms
4. **Error Handling** - Implement comprehensive error handling
5. **Rate Limiting** - Add rate limiting and abuse prevention

## 📚 Learn More

- [x402 Documentation](https://docs.cdp.coinbase.com/x402/)
- [x402 Bazaar](https://docs.cdp.coinbase.com/x402/bazaar) - Service Discovery
- [EIP-3009 Standard](https://eips.ethereum.org/EIPS/eip-3009)
- [Base Network](https://base.org/)

## 🤝 Contributing

This is a demonstration of x402 integration with uAgents. To contribute:

1. Fork the uAgents repository
2. Create a feature branch
3. Implement improvements
4. Add tests and documentation
5. Submit a pull request

## 📄 License

This example is part of the uAgents project and follows the same Apache 2.0 license.
