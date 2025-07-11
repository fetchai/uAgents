# A2A Inbound Adapter

The A2A Inbound Adapter allows you to bridge any existing Agentverse agent to the A2A (Agent-to-Agent) ecosystem, making your uAgents accessible through the A2A protocol for AI assistants and other applications.

## Overview

The A2A Inbound Adapter provides:

- A bridge between Agentverse uAgents and A2A protocol
- Secure communication through uAgent mailbox infrastructure  
- HTTP REST API endpoints compatible with A2A clients
- CLI interface for easy deployment
- Environment variable configuration for production deployments

## Installation

```bash
# Install with A2A Inbound support (includes all required dependencies)
pip install "uagents-adapter[a2a-inbound]"
```

## Usage

Using the A2A Inbound Adapter involves connecting your existing Agentverse agent to the A2A ecosystem through a bridge server.

**Choose your approach:**
- **Programmatic Usage**: When integrating into existing Python applications or services
- **CLI Usage**: For standalone deployments, containers, or simple server setups

### Programmatic Usage

#### Step 1: Get Your Agent Address

**Option A: Use an existing agent from Agentverse**
1. Visit [Agentverse.ai](https://agentverse.ai) and browse available agents
2. Choose an agent that matches your needs (e.g., finance, travel, research)
3. Copy the agent address from the agent's profile page

**Option B: Create your own agent**
1. Build a uAgent using the [uAgents framework](https://github.com/fetchai/uAgents)
2. Register your agent on [Agentverse.ai](https://agentverse.ai)
3. Copy the agent address from your agent's profile

#### Step 2: Configure the A2A Bridge

```python
from uagents_adapter import A2ARegisterTool

# Create A2A register tool
register_tool = A2ARegisterTool()

# Configure your agent bridge (replace with your agent's actual details)
config = {
    "agent_address": "agent1qv4zyd9sta4f5ksyhjp900k8kenp9vczlwqvr00xmmqmj2yetdt4se9ypat",  # Your agent's address from Agentverse
    "name": "Finance Analysis Agent",  # Descriptive name for your agent
    "description": "Financial analysis and market insights agent",  # What your agent does
    "skill_tags": ["finance", "analysis", "markets", "investment"],  # Match your agent's capabilities
    "skill_examples": ["Analyze AAPL stock performance", "Compare crypto portfolios"],  # Example queries your agent can handle
    "port": 10000,  # Port for the A2A server (default)
    "bridge_port": 9000,  # Optional: bridge port (auto-derived if not set)
    "host": "localhost"  # Host to bind the server
}

# Start the A2A bridge server
result = register_tool.invoke(config)

print(f"A2A server running on {config['host']}:{config['port']}")
print(f"Bridging to Agentverse agent: {config['agent_address']}")
```

#### Complete Copy-Paste Example

Here's a complete, ready-to-run example you can copy and save as `my_a2a_adapter.py`:

```python
from uagents_adapter import A2ARegisterTool

def main():
    """Start A2A adapter for Finance Q&A Agent - Simple CLI-like approach."""
    
    print("🔍 Starting Finance Q&A Agent A2A Adapter (Simple)")
    print("=" * 50)
    
    # Create adapter tool
    adapter = A2ARegisterTool()
    
    # Perplexity Agent configuration - same as CLI
    config = {
        "agent_address": "agent1qdv2qgxucvqatam6nv28qp202f3pw8xqpfm8man6zyegztuzd2t6yem9evl",
        "name": "Finance Q&A Agent",
        "description": "AI-powered financial advisor and Q&A assistant for investment, budgeting, and financial planning guidance",
        "skill_tags": ["finance", "investment", "budgeting", "financial_planning", "assistance"],
        "port": 10000,
        "host": "localhost"
    }
    
    print(f"🔧 Agent Address: {config['agent_address']}")
    print(f"🏷️  Agent Name: {config['name']}")
    print(f"🌐 Port: {config['port']}")
    print("")
    
    # Start adapter - this blocks just like CLI does
    try:
        result = adapter.invoke(config)
        if result.get("success"):
            print("✅ A2A Adapter Started Successfully!")
            print(f"🌐 Endpoint: http://localhost:{config['port']}")
            print("")
            
            # This blocks just like the CLI does - uvicorn handles Ctrl+C naturally
            
        else:
            print(f"❌ Failed to start adapter: {result}")
            
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
```

**To use this example:**
1. Save as `my_a2a_adapter.py`
2. Replace the `agent_address` with your actual agent's address
3. Update `name`, `description`, and `skill_tags` to match your agent
4. Run: `python my_a2a_adapter.py`

### CLI Usage

You can also run the adapter directly from the command line:

```bash
# Basic usage
python -m uagents_adapter.a2a_inbound.cli \
  --agent-address agent1qv4zyd9sta4f5ksyhjp900k8kenp9vczlwqvr00xmmqmj2yetdt4se9ypat \
  --agent-name "Finance Agent" \
  --port 10000

# Advanced configuration
python -m uagents_adapter.a2a_inbound.cli \
  --agent-address agent1qv4zyd9sta4f5ksyhjp900k8kenp9vczlwqvr00xmmqmj2yetdt4se9ypat \
  --agent-name "Airbnb Search Agent" \
  --agent-description "Find vacation rentals and accommodations" \
  --skill-tags "airbnb,vacation,rental,travel,accommodation,booking" \
  --skill-examples "Find Airbnb in San Francisco,Compare vacation rentals" \
  --host 0.0.0.0 \
  --port 10000 \
  --bridge-port 7001
```

## What to Expect When Running

### Startup Process

When you start the A2A Inbound Adapter, you'll see:

1. **Bridge Agent Initialization**:
   ```
   INFO: [a2a_agentverse_bridge]: Mailbox access token acquired
   ```

2. **Server Startup**:
   ```
   ✅ A2A Adapter Started Successfully!
   🌐 Endpoint: http://localhost:10000
   
   🧪 Test with cURL:
   curl -X POST http://localhost:10000 \
     -H "Content-Type: application/json" \
     -d '{
       "jsonrpc": "2.0",
       "id": "test-1",
       "method": "message/send",
       "params": {
         "message": {
           "role": "user",
           "parts": [{"kind": "text", "text": "Your query here"}],
           "messageId": "msg-1"
         },
         "contextId": "user-session"
       }
     }'
   ```

3. **Ready for Requests**:
   ```
   🏠 Ready for queries!
   Press Ctrl+C to stop...
   ```

### Normal Operation

During operation, you'll see HTTP request logs:

```
INFO: 127.0.0.1:54658 - "GET /agent_info HTTP/1.1" 200 OK
INFO: 127.0.0.1:54704 - "OPTIONS /messages HTTP/1.1" 204 No Content
INFO: 127.0.0.1:54704 - "GET /messages HTTP/1.1" 200 OK
```

**What these mean:**
- `GET /agent_info` - A2A clients discovering your agent's capabilities
- `OPTIONS /messages` - CORS preflight requests (normal for web browsers)
- `GET /messages` - A2A clients checking for responses

### Token Refresh (Automatic)

Periodically, you may see:

```
WARNING: [a2a_agentverse_bridge]: Access token expired: a new one should be retrieved automatically
INFO: [a2a_agentverse_bridge]: Mailbox access token acquired
```

This is **normal** - the bridge automatically refreshes its connection to Agentverse.

## Testing Your Deployment

### 1. Check Agent Info Endpoint

```bash
curl -X GET http://localhost:10000/agent_info
```

**Expected Response:**
```json
{
  "name": "Your Agent Name",
  "description": "Your agent description",
  "skill_tags": ["tag1", "tag2"],
  "skill_examples": ["Example query 1", "Example query 2"]
}
```

### 2. Send a Test Query

```bash
curl -X POST http://localhost:10000 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test-query-1",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "Hello, can you help me?"}],
        "messageId": "msg-test-1"
      },
      "contextId": "test-session"
    }
  }'
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": "test-query-1",
  "result": {
    "message": {
      "role": "assistant",
      "parts": [{"kind": "text", "text": "Response from your Agentverse agent"}],
      "messageId": "response-1"
    }
  }
}
```

### 3. Health Check

```bash
curl -X GET http://localhost:10000/health
```

## A2A Client Discovery

Once running, **A2A clients can discover your agent** by:

1. **Scanning your server** on the configured port (e.g., `localhost:10000`)
2. **Fetching agent card** from `/agent_info` endpoint
3. **Seeing your agent's capabilities**:
   - Name and description
   - Skill tags for categorization
   - Example queries to understand usage

**Your agent becomes discoverable** in the A2A ecosystem and can receive queries from:
- AI assistants
- Other A2A-compatible applications
- Direct API clients
- Web applications using A2A protocol

## Security Configuration

> **Important**: For production deployments, always configure a unique bridge seed to ensure consistent agent addresses across restarts and prevent conflicts between deployments.

### Environment Variable Configuration

Set the bridge agent seed using environment variables:

```bash
# Set a unique seed for your deployment
export UAGENTS_BRIDGE_SEED="your_unique_production_seed_2024"

# Start the adapter
python -m uagents_adapter.a2a_inbound.cli --agent-address agent1...
```

### CLI Seed Configuration

Alternatively, provide the seed directly via CLI:

```bash
python -m uagents_adapter.a2a_inbound.cli \
  --agent-address agent1... \
  --bridge-seed "your_unique_production_seed_2024"
```

### .env File Configuration

For development, create a `.env` file:

```bash
# Bridge Agent Seed (for consistent addresses)
UAGENTS_BRIDGE_SEED=my_consistent_development_seed_12345

# Agent Configuration
AGENT_ADDRESS=agent1qv4zyd9sta4f5ksyhjp900k8kenp9vczlwqvr00xmmqmj2yetdt4se9ypat
AGENT_NAME=Finance Analysis Agent
AGENT_DESCRIPTION=Financial analysis and market insights agent

# Server Configuration  
A2A_HOST=localhost
A2A_PORT=10000
```

Then load it in your code:

```python
from dotenv import load_dotenv
from uagents_adapter import A2ARegisterTool

# Load environment variables
load_dotenv()

# Your adapter will automatically use UAGENTS_BRIDGE_SEED
adapter = A2ARegisterTool()
```

## Configuration Options

### CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--agent-address` | Agentverse agent address to bridge to | **Required** |
| `--agent-name` | Name for the A2A agent | "Agentverse Agent" |
| `--agent-description` | Description for the A2A agent | "Agent bridged from Agentverse" |
| `--skill-tags` | Comma-separated skill tags | "general,assistance" |
| `--skill-examples` | Comma-separated skill examples | "Help me with my query" |
| `--host` | Host to bind the server to | "localhost" |
| `--port` | Port to bind the server to | 10000 |
| `--bridge-port` | Port for internal uAgent bridge | auto-derived |
| `--bridge-seed` | Seed for bridge agent | from env var |

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `UAGENTS_BRIDGE_SEED` | Seed for consistent bridge agent addresses | Recommended |

### Bridge Port Configuration

**NEW: Explicit Bridge Port Support** 🆕

The A2A adapter now supports explicit bridge port configuration through both the programmatic API and CLI. This gives you full control over which ports are used.

#### Auto-Derived Bridge Port (Default Behavior)

By default, the bridge port is automatically derived from the main A2A server port:

- **Formula**: `bridge_port = main_port - 1000`
- **Fallback**: If the result is < 1024, then `bridge_port = main_port + 1000`

```python
# Example: main port 10000 → bridge port 9000
config = {
    "port": 10000,  # A2A server port
    # bridge_port automatically becomes 9000
}
```

```bash
# CLI example: main port 10000 → bridge port 9000
python -m uagents_adapter.a2a_inbound.cli --port 10000
# Bridge will auto-derive to port 9000
```

#### Explicit Bridge Port (New Feature)

You can now explicitly specify the bridge port:

```python
# Programmatic API with explicit bridge port
config = {
    "port": 10000,        # A2A server port
    "bridge_port": 8500,  # Explicit bridge port
}
```

```bash
# CLI with explicit bridge port
python -m uagents_adapter.a2a_inbound.cli \
  --port 10000 \
  --bridge-port 8500
```

**Benefits of Explicit Bridge Port:**
- Avoid port conflicts in complex environments
- Better control for containerized deployments
- Easier firewall and network configuration
- Support for non-standard port arrangements

**Backward Compatibility:** All existing code continues to work unchanged. The `bridge_port` parameter is completely optional.

## Architecture

The A2A Inbound Adapter creates two components:

1. **A2A HTTP Server**: Exposes REST API endpoints on the main port
2. **Bridge uAgent**: Internal agent that communicates with your Agentverse agent

```
A2A Client → HTTP Server (:10000) → Bridge Agent (:9000) → Agentverse Agent
```

## Security Considerations

- **Unique Seeds**: Always use unique `UAGENTS_BRIDGE_SEED` values for different deployments
- **Network Security**: Configure appropriate firewall rules for your deployment
- **Agent Verification**: Ensure your Agentverse agent address is correct and active
- **Production Monitoring**: Monitor bridge agent connectivity and message flow

## Troubleshooting

### Bridge Agent Address Changes

If you see warnings about random seeds:

```
⚠️  No UAGENTS_BRIDGE_SEED provided - using random seed
⚠️  Bridge agent address will change on restart
```

**Solution**: Set `UAGENTS_BRIDGE_SEED` environment variable:

```bash
export UAGENTS_BRIDGE_SEED="your_unique_seed_here"
```

### Agent Communication Issues

If messages aren't reaching your Agentverse agent:

1. Verify your agent address is correct and active
2. Check Agentverse agent logs for incoming messages
3. Ensure bridge agent has mailbox access
4. Verify network connectivity

### Port Conflicts

If you encounter port binding errors:

1. Check if ports are already in use: `lsof -i :10000`
2. Use different ports: `--port 10001 --bridge-port 9001`
3. Ensure bridge-port doesn't conflict with main port

## Example Agents

### Finance Agent

```bash
python -m uagents_adapter.a2a_inbound.cli \
  --agent-address agent1qfinance123... \
  --agent-name "Finance Advisor" \
  --agent-description "Financial analysis and investment advice" \
  --skill-tags "finance,stocks,crypto,analysis,investment" \
  --skill-examples "Analyze AAPL stock,Compare crypto portfolios,Market trends" \
  --port 10000
```

### Travel Agent

```bash
python -m uagents_adapter.a2a_inbound.cli \
  --agent-address agent1qtravel456... \
  --agent-name "Travel Assistant" \
  --agent-description "Travel planning and booking assistance" \
  --skill-tags "travel,hotels,flights,vacation,booking" \
  --skill-examples "Find hotels in Paris,Book flights to Tokyo,Plan weekend trip" \
  --port 10001
```


