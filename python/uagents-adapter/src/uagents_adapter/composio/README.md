## 🏁 Quick Start

### 1. Basic Setup

```python
import asyncio
from uagents import Agent
from uagents_composio_adapter import ComposioConfig, ToolConfig, ComposioService

async def main():
    # Configure tools
    tool_config = ToolConfig.from_toolkit(
        tool_group_name="GitHub Tools",
        auth_config_id="your_github_auth_config_id",
        toolkit="GITHUB",
        limit=5
    )

    # Create Composio configuration
    composio_config = ComposioConfig.from_env(tool_configs=[tool_config])

    # Initialize agent
    agent = Agent(name="My Composio Agent", seed="my_seed", port=8001, mailbox=True)

    # Create and configure Composio service
    async with ComposioService(composio_config=composio_config) as service:
        agent.include(service.protocol, publish_manifest=True)
        await agent.run_async()

if __name__ == "__main__":
    asyncio.run(main())
```

> **Note**: For advanced use cases with tool modifiers, see the [Tool Modifiers](#tool-modifiers-for-customization) section below.

### 2. Environment Variables

Create a `.env` file with the following variables:

```bash
# Composio Configuration
COMPOSIO_API_KEY=your_composio_api_key_here
COMPOSIO_DEFAULT_TIMEOUT=300

# Authentication Configuration IDs (from Composio dashboard)
GITHUB_AUTH_CONFIG_ID=your_github_auth_config_id
LINKEDIN_AUTH_CONFIG_ID=your_linkedin_auth_config_id

# LLM Configuration (ASI1 or OpenAI compatible)
LLM_API_KEY=your_llm_api_key_here
LLM_BASE_URL=https://api.asi1.ai/v1
LLM_MODEL_NAME=asi1-mini

# PostgreSQL Configuration (optional - for memory persistence)
PSQL_HOST=localhost
PSQL_PORT=5432
PSQL_DATABASE=composio_memory
PSQL_USERNAME=your_db_username
PSQL_PASSWORD=your_db_password
```

## 📚 Comprehensive Examples

### Tool Configuration Patterns

```python
from uagents_composio_adapter import ToolConfig

# 1. Specific tools by name
github_tools = ToolConfig.from_tools(
    tool_group_name="GitHub Issue Management",
    auth_config_id="auth_123",
    tools=["GITHUB_CREATE_AN_ISSUE", "GITHUB_LIST_ISSUES"]
)

# 2. All tools from a toolkit with limit
slack_tools = ToolConfig.from_toolkit(
    tool_group_name="Slack Communication",
    auth_config_id="auth_456",
    toolkit="SLACK",
    limit=10
)

# 3. Tools filtered by OAuth scopes
gmail_tools = ToolConfig.from_toolkit_with_scopes(
    tool_group_name="Email Management",
    auth_config_id="auth_789",
    toolkit="GMAIL",
    scopes=["gmail.send", "gmail.compose"],
    limit=5
)

# 4. Semantic search for relevant tools
crm_tools = ToolConfig.from_search(
    tool_group_name="CRM Tools",
    auth_config_id="auth_101",
    search="customer relationship management contacts",
    limit=8
)
```

### Tool Modifiers for Customization

```python
from uagents_composio_adapter import Modifiers, ToolExecutionResponse

# Define modifier functions (no decorators needed)
def enhance_github_schema(tool_name: str, toolkit: str, schema):
    schema.description += " [Enhanced with context awareness]"
    return schema

# Before-execute modifier to inject parameters
def add_slack_context(tool_name: str, toolkit: str, params):
    if 'channel' not in params.arguments:
        params.arguments['channel'] = '#general'
    return params

# After-execute modifier to process results
def log_email_sent(tool_name: str, toolkit: str, response: ToolExecutionResponse) -> ToolExecutionResponse:
    print(f"Email sent successfully via {tool_name}")
    return response

# Combine modifiers using function-to-tools mapping
modifiers = Modifiers.combine(
    schema_functions={enhance_github_schema: ["GITHUB_CREATE_AN_ISSUE"]},
    before_execute_functions={add_slack_context: ["SLACK_SEND_MESSAGE"]},
    after_execute_functions={log_email_sent: ["GMAIL_SEND_EMAIL"]}
)

# Apply to tool configuration
config = ToolConfig.from_toolkit(
    tool_group_name="Enhanced Tools",
    auth_config_id="auth_123",
    toolkit="GITHUB",
    modifiers=modifiers
)
```

### Real-World Modifier Example

```python
from uagents_composio_adapter import ToolConfig, Modifiers, ToolExecutionResponse

# After-execute modifier to log LinkedIn data loading
def show_loaded_linkedin_data(
    tool: str,
    toolkit: str,
    response: ToolExecutionResponse
) -> ToolExecutionResponse:
    print(f"\n[LinkedIn Data Loaded] Tool: {tool}, Toolkit: {toolkit}, Response: {response}\n")
    return response

# Create tool configuration with modifier
linkedin_tool_config = ToolConfig.from_toolkit(
    tool_group_name="LinkedIn Marketing",
    auth_config_id="your_linkedin_auth_config_id",
    toolkit="LINKEDIN",
    modifiers=Modifiers.combine(
        after_execute_functions={
            show_loaded_linkedin_data: ["LINKEDIN_GET_MY_INFO"]
        }
    )
)
```

### Memory Persistence with PostgreSQL

```python
from uagents_composio_adapter import PostgresMemoryConfig, ComposioService

# Configure PostgreSQL memory
memory_config = PostgresMemoryConfig.from_env()

# Or configure manually
memory_config = PostgresMemoryConfig(
    host="localhost",
    port=5432,
    database="agent_memory",
    user="postgres",
    password="your_password"
)

# Use with ComposioService
async with ComposioService(
    composio_config=composio_config,
    memory_config=memory_config
) as service:
    # Service now has persistent conversation memory
    agent.include(service.protocol, publish_manifest=True)
```

### Multi-Agent Orchestrator System

```python
import asyncio
from uagents import Agent
from uagents_composio_adapter import ComposioConfig, ToolConfig, ComposioService

async def main():
    # Multiple tool configurations for different specialized agents
    tool_configs = [
        ToolConfig.from_toolkit(
            tool_group_name="GitHub Management",
            auth_config_id=os.getenv("GITHUB_AUTH_ID"),
            toolkit="GITHUB",
            limit=5
        ),
        ToolConfig.from_toolkit(
            tool_group_name="Email Operations",
            auth_config_id=os.getenv("GMAIL_AUTH_ID"),
            toolkit="GMAIL",
            limit=3
        ),
        ToolConfig.from_toolkit(
            tool_group_name="Calendar Management",
            auth_config_id=os.getenv("CALENDAR_AUTH_ID"),
            toolkit="GOOGLECALENDAR",
            limit=4
        )
    ]

    # Create configuration with persona prompt
    composio_config = ComposioConfig.from_env(
        tool_configs=tool_configs,
        persona_prompt="You are a productivity-focused AI assistant. Prioritize efficiency and provide clear, actionable guidance for task automation."
    )

    # Initialize agent
    agent = Agent(
        name="Multi-Agent Orchestrator",
        seed="orchestrator_seed",
        port=8001,
        mailbox=True
    )

    # Create orchestrator service with specialized agents
    async with ComposioService(composio_config=composio_config) as service:
        # The service automatically creates specialized agents based on tool configurations:
        # - One specialized agent for each tool group (e.g., GitHub Management, Email Operations)
        # - Each agent optimized for its specific domain with tailored prompts and capabilities
        # - Main Orchestrator Agent that intelligently routes requests to appropriate specialists

        agent.include(service.protocol, publish_manifest=True)
        logger.info("🚀 Multi-agent orchestrator system started!")
        await agent.run_async()

if __name__ == "__main__":
    asyncio.run(main())
```

### Complete Production Example

```python
import os
import asyncio
import logging
from uagents import Agent
from uagents_composio_adapter import (
    ComposioConfig, ToolConfig, ComposioService,
    PostgresMemoryConfig, Modifiers, ToolExecutionResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Define modifier function for LinkedIn data logging
    def show_loaded_linkedin_data(
        tool: str,
        toolkit: str,
        response: ToolExecutionResponse
    ) -> ToolExecutionResponse:
        print(f"\n[LinkedIn Data Loaded] Tool: {tool}, Toolkit: {toolkit}, Response: {response}\n")
        return response

    # Multiple tool configurations with modifiers
    tool_configs = [
        ToolConfig.from_tools(
            tool_group_name="Repository Tracker",
            auth_config_id=os.getenv("GITHUB_AUTH_CONFIG_ID"),
            tools=[
                "GITHUB_LIST_COMMITS",
                "GITHUB_GET_A_COMMIT",
                "GITHUB_GET_A_REPOSITORY",
                "GITHUB_COMPARE_TWO_COMMITS",
                "GITHUB_LIST_RELEASES",
                "GITHUB_GET_REPOSITORY_CONTENT"
            ]
        ),
        ToolConfig.from_toolkit(
            tool_group_name="LinkedIn Marketing",
            auth_config_id=os.getenv("LINKEDIN_AUTH_CONFIG_ID"),
            toolkit="LINKEDIN",
            modifiers=Modifiers.combine(
                after_execute_functions={
                    show_loaded_linkedin_data: ["LINKEDIN_GET_MY_INFO"]
                }
            )
        )
    ]

    # Create configurations with persona prompt
    composio_config = ComposioConfig.from_env(
        tool_configs=tool_configs,
        persona_prompt="You are a productivity-focused AI assistant for building in public..."
    )
    memory_config = PostgresMemoryConfig.from_env()

    # Initialize agent
    agent = Agent(
        name="BuildInPublic Agent",
        seed="build_public_secret_seed_123123",
        port=8001,
        mailbox=True
    )

    # Run with proper resource management
    async with ComposioService(
        composio_config=composio_config,
        memory_config=memory_config
    ) as service:
        # Health check
        health = await service.health_check()
        if health['status'] != 'healthy':
            logger.error(f"Service unhealthy: {health}")
            return

        # Integrate with agent
        agent.include(service.protocol, publish_manifest=True)

        logger.info("🚀 BuildInPublic agent started successfully!")
        await agent.run_async()

if __name__ == "__main__":
    asyncio.run(main())
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    uAgents Agent                            │
├─────────────────────────────────────────────────────────────┤
│                 ComposioService                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │               Protocol Handler                      │    │
│  │  ┌─────────────────────────────────────────────┐    │    │
│  │  │           Authentication Flow               │    │    │
│  │  └─────────────────────────────────────────────┘    │    │
│  │  ┌─────────────────────────────────────────────┐    │    │
│  │  │          Orchestrator Agent                 │    │    │
│  │  │  ┌─────────────┬─────────────┬───────────┐  │    │    │
│  │  │  │ Tool Group  │ Tool Group  │   ...     │  │    │    │
│  │  │  │ Agent A     │ Agent B     │ Agent N   │  │    │    │
│  │  │  └─────────────┴─────────────┴───────────┘  │    │    │
│  │  └─────────────────────────────────────────────┘    │    │
│  │  ┌─────────────────────────────────────────────┐    │    │
│  │  │           Tool Management                   │    │    │
│  │  │        (Dynamic Tool Groups)                │    │    │
│  │  └─────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│                  ComposioClient                             │
│              (Composio API Interface)                       │
├─────────────────────────────────────────────────────────────┤
│               PostgreSQL Memory                             │
│            (Optional Persistence)                           │
└─────────────────────────────────────────────────────────────┘
```

## 📖 API Reference

### Core Classes

#### `ComposioService`
Main service class for Composio integration with multi-agent orchestrator support.

```python
class ComposioService:
    def __init__(
        self,
        composio_config: ComposioConfig,
        api_key: str | None = None,
        model_name: str | None = None,
        base_url: str | None = None,
        memory_config: PostgresMemoryConfig | None = None,
    ) -> None: ...

    @property
    def protocol(self) -> Protocol: ...

    async def health_check(self) -> dict[str, Any]: ...
    async def cleanup(self) -> None: ...
```

#### `ComposioConfig`
Configuration class with persona prompt support.

```python
class ComposioConfig:
    api_key: str
    persona_prompt: str | None = None
    tool_configs: list[ToolConfig]
    timeout: int = 300

    @classmethod
    def from_env(
        cls,
        tool_configs: list[ToolConfig] | None = None,
        persona_prompt: str | None = None,
    ) -> "ComposioConfig": ...
```

#### `ToolConfig`
Configuration for tool retrieval with multiple patterns.

```python
class ToolConfig:
    @classmethod
    def from_tools(cls, tool_group_name: str, auth_config_id: str, tools: list[str]) -> "ToolConfig": ...

    @classmethod
    def from_toolkit(cls, tool_group_name: str, auth_config_id: str, toolkit: str, limit: int | None = None) -> "ToolConfig": ...

    @classmethod
    def from_search(cls, tool_group_name: str, auth_config_id: str, search: str, toolkit: str | None = None, limit: int | None = None) -> "ToolConfig": ...
```

#### `Modifiers`
Tool modifier management for customization.

```python
class Modifiers:
    @classmethod
    def with_schema(cls, modifiers: dict[SchemaModifierFunc, list[str]]) -> "Modifiers": ...

    @classmethod
    def with_before_execute(cls, modifiers: dict[BeforeExecuteModifierFunc, list[str]]) -> "Modifiers": ...

    @classmethod
    def with_after_execute(cls, modifiers: dict[AfterExecuteModifierFunc, list[str]]) -> "Modifiers": ...

    @classmethod
    def combine(cls, schema_functions: dict | None = None, before_execute_functions: dict | None = None, after_execute_functions: dict | None = None) -> "Modifiers": ...
```
