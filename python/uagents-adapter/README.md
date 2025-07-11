# uAgents Adapter

This package provides adapters for integrating [uAgents](https://github.com/fetchai/uAgents) with popular AI libraries:

- **LangChain Adapter**: Convert LangChain agents to uAgents
- **CrewAI Adapter**: Convert CrewAI crews to uAgents
- **MCP Server Adapter**: Integrate Model Control Protocol (MCP) servers with uAgents
- **A2A Inbound Adapter**: Bridge Agentverse agents to A2A protocol for AI assistants

## Installation

```bash
# Install the base package
pip install uagents-adapter

# Install with LangChain support
pip install "uagents-adapter[langchain]"

# Install with CrewAI support
pip install "uagents-adapter[crewai]"

# Install with MCP support
pip install "uagents-adapter[mcp]"

# Install with A2A Inbound support
pip install "uagents-adapter[a2a-inbound]"

# Install with all extras
pip install "uagents-adapter[langchain,crewai,mcp,a2a-inbound]"
```

## LangChain Adapter

The LangChain adapter allows you to convert any LangChain agent into a uAgent that can interact with other agents in the Agentverse ecosystem.

```python
from langchain_core.agents import AgentExecutor, create_react_agent
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

from uagents_adapter import LangchainRegisterTool

# Create your LangChain agent
llm = ChatOpenAI(model_name="gpt-4")
tools = [...]  # Your tools here
agent = create_react_agent(llm, tools)
agent_executor = AgentExecutor(agent=agent, tools=tools)

# Create uAgent register tool
register_tool = LangchainRegisterTool()

# Register the agent as a uAgent
result = register_tool.invoke({
    "agent_obj": agent_executor,
    "name": "my_langchain_agent",
    "port": 8000,
    "description": "My LangChain agent as a uAgent",
    "mailbox": True,  # Use Agentverse mailbox service
    "api_token": "YOUR_AGENTVERSE_API_TOKEN",  # Optional: for Agentverse registration
    "return_dict": True  # Return a dictionary instead of a string
})

print(f"Created uAgent '{result['agent_name']}' with address {result['agent_address']} on port {result['agent_port']}")
```

## CrewAI Adapter

The CrewAI adapter allows you to convert any CrewAI crew into a uAgent.

```python
from crewai import Crew, Agent, Task
from uagents_adapter import CrewaiRegisterTool

# Define your CrewAI crew
agent1 = Agent(
    role="Researcher",
    goal="Research thoroughly",
    backstory="You are a skilled researcher",
    verbose=True,
    allow_delegation=False
)

task1 = Task(
    description="Research about a topic",
    agent=agent1
)

crew = Crew(
    agents=[agent1],
    tasks=[task1],
    verbose=True
)

# Create CrewAI register tool
register_tool = CrewaiRegisterTool()

# Register the crew as a uAgent
result = register_tool.invoke({
    "crew_obj": crew,
    "name": "my_crew_agent",
    "port": 8001,
    "description": "My CrewAI crew as a uAgent",
    "mailbox": True,  # Use Agentverse mailbox service
    "api_token": "YOUR_AGENTVERSE_API_TOKEN",  # Optional: for Agentverse registration
    "query_params": {
        "topic": {
            "type": "string",
            "description": "The topic to research",
            "required": True
        }
    },
    "example_query": "Research about artificial intelligence",
    "return_dict": True  # Return a dictionary instead of a string
})

print(f"Created uAgent '{result['agent_name']}' with address {result['agent_address']} on port {result['agent_port']}")
```

## MCP Server Adapter

The MCP Server Adapter allows you to host your MCP Servers on Agentverse and get discovered by ASI:One by enabling Chat Protocol.

First, create a FastMCP server implementation in a `server.py` file that exposes the required `list_tools` and `call_tool` async methods. Then, in the following `agent.py`, import the MCP server instance and use it with the MCPServerAdapter:

```python
from uagents import Agent
from uagents_adapter import MCPServerAdapter
from server import mcp

# Create an MCP adapter
mcp_adapter = MCPServerAdapter(
    mcp_server=mcp,
    asi1_api_key="your_asi1_api_key",
    model="asi1-mini"     # Model options: asi1-mini, asi1-extended, asi1-fast
)

# Create a uAgent
agent = Agent()

# Add the MCP adapter protocols to the agent
for protocol in mcp_adapter.protocols:
    agent.include(protocol)

# Run the MCP adapter with the agent
mcp_adapter.run(agent)
```

> **Important**: When creating MCP tools, always include detailed docstrings using triple quotes (`"""`) to describe what each tool does, when it should be used, and what parameters it expects. These descriptions are critical for ASI:One to understand when and how to use your tools.

For more detailed instructions and advanced configuration options, see the [MCP Server Adapter Documentation](src/uagents_adapter/mcp/README.md).

## A2A Inbound Adapter

The A2A Inbound Adapter allows you to bridge any existing Agentverse agent to the A2A (Agent-to-Agent) ecosystem, making your uAgents accessible through the A2A protocol for AI assistants and other applications.

```python
from uagents_adapter import A2ARegisterTool

# Create A2A register tool
register_tool = A2ARegisterTool()

# Choose the agent you want to use from Agentverse.ai, copy its address in the config, add agent details or create a custom agent yourself and add its address in the config
# Configure your agent bridge
config = {
    "agent_address": "agent1qv4zyd9sta4f5ksyhjp900k8kenp9vczlwqvr00xmmqmj2yetdt4se9ypat",
    "name": "Finance Analysis Agent", 
    "description": "Financial analysis and market insights agent",
    "skill_tags": ["finance", "analysis", "markets", "investment"],
    "skill_examples": ["Analyze AAPL stock performance", "Compare crypto portfolios"],
    "port": 8001,
    "host": "127.0.0.1"
}

# Start the A2A bridge server
result = register_tool.invoke(config)

print(f"A2A server running on {config['host']}:{config['port']}")
print(f"Bridging to Agentverse agent: {config['agent_address']}")
```

For CLI usage:

```bash
# Set unique bridge seed for production
export UAGENTS_BRIDGE_SEED="your_unique_production_seed_2024"

# Start the A2A bridge
python -m uagents_adapter.a2a_inbound.cli \
  --agent-address agent1qv4zyd9sta4f5ksyhjp900k8kenp9vczlwqvr00xmmqmj2yetdt4se9ypat \
  --agent-name "Finance Agent" \
  --skill-tags "finance,analysis,markets" \
  --port 8001
```

> **Security Note**: Always set `UAGENTS_BRIDGE_SEED` environment variable for production deployments to ensure consistent bridge agent addresses across restarts and prevent conflicts.

For more detailed instructions and configuration options, see the [A2A Inbound Adapter Documentation](src/uagents_adapter/a2a_inbound/README.md).

## Agentverse Integration

### Mailbox Service

By default, agents are created with `mailbox=True`, which enables the agent to use the Agentverse mailbox service. This allows agents to communicate with other agents without requiring a publicly accessible endpoint.

When mailbox is enabled:
- Agents can be reached by their agent address (e.g., `agent1q...`)
- No port forwarding or public IP is required
- Messages are securely handled through the Agentverse infrastructure

### Agentverse Registration

You can optionally register your agent with the Agentverse API, which makes it discoverable and usable by other users in the Agentverse ecosystem:

1. Obtain an API token from [Agentverse.ai](https://agentverse.ai)
2. Include the token when registering your agent:
   ```python
   result = register_tool.invoke({
       # ... other parameters
       "api_token": "YOUR_AGENTVERSE_API_TOKEN"
   })
   ```

When an agent is registered with Agentverse:
- It connects to the mailbox service automatically
- It appears in the Agentverse directory
- A README with input/output models is automatically generated
- The agent gets an "innovationlab" badge
- Other users can discover and interact with it
- You can monitor its usage and performance through the Agentverse dashboard

Example of auto-generated README for LangChain agents:
```markdown
# Agent Name
Agent Description
![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)

**Input Data Model**
```python
class QueryMessage(Model):
    query: str
```

**Output Data Model**
```python
class ResponseMessage(Model):
    response: str
```
```

Example of auto-generated README for CrewAI agents with parameters:
```markdown
# Agent Name
Agent Description
![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)

**Input Data Model**
```python
class ParameterMessage(Model):
    topic: str
    max_results: int | None = None
```

**Output Data Model**
```python
class ResponseMessage(Model):
    response: str
```

**Example Query**
```
Research about artificial intelligence
```
```

## License

Apache 2.0