# uAgents Adapter Quick Start Guide

This guide helps you quickly get started with the uAgents adapters for LangChain, CrewAI, and MCP (Model Control Protocol) integration.

## Overview

The uAgents adapter package provides seamless integration between uAgents and popular AI frameworks:

- **LangChain Adapter**: Convert LangChain agents to uAgents
- **CrewAI Adapter**: Convert CrewAI crews to uAgents  
- **MCP Adapter**: Integrate Model Control Protocol servers with uAgents

## Quick Installation

```bash
# Install with all adapters
pip install "uagents-adapter[langchain,crewai,mcp]"

# Or install specific adapters
pip install "uagents-adapter[langchain]"  # LangChain only
pip install "uagents-adapter[crewai]"     # CrewAI only
pip install "uagents-adapter[mcp]"        # MCP only
```

## Basic Usage Examples

### 1. MCP Server Integration

```python
from uagents import Agent
from uagents_adapter.mcp import MCPServerAdapter

# Create agent
agent = Agent(name="mcp_agent", seed="your_seed")

# Set up MCP adapter
adapter = MCPServerAdapter(
    mcp_server=your_mcp_server,
    asi1_api_key="your_api_key",
    model="your_model"
)

# Register agent
result = adapter.register_agent(agent)
```

### 2. LangChain Agent Conversion

```python
from uagents_adapter.langchain import register_tool
from langchain.agents import create_openai_functions_agent

# Convert LangChain agent to uAgent
result = register_tool.invoke({
    "agent": your_langchain_agent,
    "name": "My LangChain Agent",
    "description": "An agent converted from LangChain"
})
```

### 3. CrewAI Integration

```python
from uagents_adapter.crewai import register_tool
from crewai import Crew

# Convert CrewAI crew to uAgent
result = register_tool.invoke({
    "crew": your_crew,
    "name": "My CrewAI Agent", 
    "description": "A crew converted to uAgent"
})
```

## Configuration

### Environment Variables

Set these environment variables for enhanced functionality:

```bash
# For MCP integration
export ASI1_API_KEY="your_asi1_api_key"
export MCP_SERVER_URL="your_mcp_server_url"

# For Agentverse integration (optional)
export AGENTVERSE_API_TOKEN="your_agentverse_token"
```

### Agent Configuration

```python
from uagents import Agent

# Create agent with custom configuration
agent = Agent(
    name="my_agent",
    seed="unique_seed_string",
    port=8001,  # Custom port
    endpoint=["http://localhost:8001"]  # Custom endpoint
)
```

## Advanced Features

### Agentverse Registration

Optionally register your agents with Agentverse for discoverability:

```python
result = register_tool.invoke({
    "agent": your_agent,
    "name": "My Agent",
    "description": "Agent description",
    "api_token": "your_agentverse_token"  # Makes agent discoverable
})
```

### Custom Message Handling

```python
from uagents import Context, Model

class CustomMessage(Model):
    content: str
    priority: int = 1

@agent.on_message(CustomMessage)
async def handle_custom_message(ctx: Context, sender: str, msg: CustomMessage):
    ctx.logger.info(f"Received: {msg.content} with priority {msg.priority}")
    
    # Send response
    await ctx.send(sender, CustomMessage(
        content=f"Processed: {msg.content}",
        priority=msg.priority
    ))
```

### Protocol Integration

```python
from uagents import Protocol

# Create custom protocol
my_protocol = Protocol("MyProtocol")

@my_protocol.on_message(CustomMessage)
async def protocol_handler(ctx: Context, sender: str, msg: CustomMessage):
    # Handle protocol-specific logic
    pass

# Include protocol in agent
agent.include(my_protocol)
```

## Testing Your Integration

### Basic Functionality Test

```python
import asyncio
from uagents import Agent, Context, Model

async def test_agent():
    agent = Agent(name="test_agent", seed="test")
    
    @agent.on_startup()
    async def startup(ctx: Context):
        ctx.logger.info("Agent started successfully!")
    
    # Test agent creation
    assert agent.name == "test_agent"
    assert agent.address is not None
    print(f"Agent address: {agent.address}")

# Run test
asyncio.run(test_agent())
```

### Integration Test with Mock

```python
from unittest.mock import Mock, patch

def test_mcp_integration():
    mock_server = Mock()
    
    adapter = MCPServerAdapter(
        mcp_server=mock_server,
        asi1_api_key="test_key",
        model="test_model"
    )
    
    # Test adapter initialization
    assert adapter._api_key == "test_key"
    assert adapter._model == "test_model"
```

## Common Issues & Solutions

### Import Errors
```bash
# If you get import errors, ensure all dependencies are installed
pip install --upgrade uagents uagents-adapter

# For development setup
pip install -e .[langchain,crewai,mcp]
```

### Network Issues
```python
# If agents can't communicate, check endpoints
agent = Agent(
    name="my_agent",
    seed="seed",
    endpoint=["http://0.0.0.0:8001"]  # Use 0.0.0.0 for external access
)
```

### Registration Issues
```python
# If Agentverse registration fails, check your API token
from uagents_adapter.common import register_tool

try:
    result = register_tool.invoke({
        "agent": agent,
        "api_token": "your_valid_token"
    })
    print("Registration successful:", result)
except Exception as e:
    print("Registration failed:", e)
```

## Next Steps

1. **Explore Examples**: Check the `examples/` directory for more complex use cases
2. **Read Documentation**: Review the full README.md for detailed API documentation
3. **Join Community**: Connect with other developers using uAgents
4. **Contribute**: Help improve the adapters by contributing to the project

## Resources

- [uAgents Documentation](https://fetch.ai/docs)
- [LangChain Documentation](https://langchain.readthedocs.io/)
- [CrewAI Documentation](https://docs.crewai.com/)
- [MCP Specification](https://modelcontextprotocol.io/)

For more detailed information, see the complete [README.md](README.md) file.