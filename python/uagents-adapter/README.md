# uAgents Adapter

This package provides adapters for integrating [uAgents](https://github.com/fetchai/uAgents) with popular AI libraries:

- **LangChain Adapter**: Convert LangChain agents to uAgents
- **CrewAI Adapter**: Convert CrewAI crews to uAgents

## Installation

```bash
# Install the base package
pip install uagents-adapter

# Install with LangChain support
pip install "uagents-adapter[langchain]"

# Install with CrewAI support
pip install "uagents-adapter[crewai]"

# Install with all extras
pip install "uagents-adapter[langchain,crewai]"
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
```
# Agent Name
Agent Description
![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)

**Input Data Model**
```
class QueryMessage(Model):
    query: str
```

**Output Data Model**
```
class ResponseMessage(Model):
    response: str
```
```

Example of auto-generated README for CrewAI agents with parameters:
```
# Agent Name
Agent Description
![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)

**Input Data Model**
```
class ParameterMessage(Model):
    topic: str
    max_results: int
```

**Output Data Model**
```
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