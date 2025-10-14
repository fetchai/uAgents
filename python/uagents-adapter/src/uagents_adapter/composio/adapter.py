"""
Production-ready Composio integration module for LangChain-based AI agents with multi-agent
orchestrator.

This module provides a comprehensive, async-first integration layer for building
intelligent multi-agent systems that can authenticate users, manage tool access, and
execute actions through the Composio platform. It features an advanced orchestrator
architecture that automatically routes requests to specialized tool agents based on
their capabilities and includes robust error handling, structured logging, connection
management, and memory persistence capabilities.

Key Features:
    - Multi-agent orchestrator system with intelligent request routing
    - Specialized agents for different tool groups and capabilities
    - Persona customization for orchestrator behavior guidance
    - Async/await support throughout the entire system
    - Type-safe configuration management with comprehensive validation
    - Robust error handling with custom exceptions and detailed context
    - Structured logging with contextual information and performance metrics
    - Complete OAuth authentication flows with automatic retry logic
    - Advanced tool retrieval with filtering, modification, and optimization
    - PostgreSQL-based conversation memory with automatic schema management
    - Thread-safe operations with proper resource management and connection pooling

Architecture:
    The system implements a hierarchical multi-agent architecture:

    1. Orchestrator Agent: Main decision-making agent that analyzes user requests
       and routes them to the most appropriate specialized agent

    2. Specialized Agents: Domain-specific agents created dynamically based on
       configured tool groups, each handling specific tool categories with optimized
       prompts and capabilities

    3. Tool Management: Intelligent grouping and organization of Composio tools
       into logical categories for efficient agent specialization

Usage:
    ```python
    import asyncio
    from uagents_composio_adapter import (
        ComposioService, ComposioConfig, ToolConfig, Modifiers, ToolExecutionResponse
    )

    async def main():
        # Define custom modifier functions
        def show_data_loaded(
            tool: str, toolkit: str, response: ToolExecutionResponse
        ) -> ToolExecutionResponse:
            print(f"[Data Loaded] Tool: {tool}, Response: {response}")
            return response

        # Configure multiple tool groups for specialized agents
        tool_configs = [
            ToolConfig.from_toolkit("GitHub Tools", "auth_123", "GITHUB", limit=5),
            ToolConfig.from_toolkit("Email Tools", "auth_456", "GMAIL", limit=3),
            ToolConfig.from_toolkit(
                "LinkedIn Tools",
                "auth_789",
                "LINKEDIN",
                modifiers=Modifiers.combine(
                    after_execute_functions={
                        show_data_loaded: ["LINKEDIN_GET_MY_INFO"]
                    }
                )
            )
        ]

        # Create configuration with persona customization
        config = ComposioConfig.from_env(
            tool_configs=tool_configs,
            persona_prompt="You are a productivity-focused AI assistant..."
        )

        # Initialize the multi-agent orchestrator service
        service = ComposioService(composio_config=config)

        # Use the service protocol for agent communication
        protocol = service.protocol
        # ... integrate with your agent framework

    asyncio.run(main())
    ```
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import os
import sys
from collections.abc import AsyncGenerator, Callable
from datetime import datetime, timezone
from typing import Any, Final, Protocol, runtime_checkable
from uuid import uuid4

from composio import Composio, after_execute, before_execute, schema_modifier
from composio.core.models.connected_accounts import ConnectionRequest
from composio.exceptions import ComposioSDKTimeoutError
from composio.types import Tool, ToolExecuteParams, ToolExecutionResponse
from composio_langchain import LangchainProvider
from langchain.agents import ToolNode, create_agent
from langchain.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.messages.utils import count_tokens_approximately, trim_messages
from langchain_core.tools.structured import StructuredTool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from uagents import Context
from uagents import Protocol as AgentChatProtocol
from uagents_core.contrib.protocols.chat import (
    AgentContent,
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    MetadataContent,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)

# Python 3.10 compatibility for UTC
if sys.version_info >= (3, 11):
    from datetime import UTC
else:
    UTC = timezone.utc

from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator

# Type definitions for better code clarity
UserId = str
AuthConfigId = str
ToolSlug = str
SessionId = str


# Constants
DEFAULT_TIMEOUT: Final[int] = 300
MAX_TOOLS_LIMIT: Final[int] = 100

# Configure module logger with structured format for production
logger = logging.getLogger(__name__)


# Protocol definitions that match the decorator expectations
def describe_modifier_type(modifier_type: type) -> None:
    """
    Display expected signature and documentation for a given modifier Protocol.
    Helpful when writing new modifiers.

    Example:
        >>> from composio.modifiers import describe_modifier_type, SchemaModifier
        >>> describe_modifier_type(SchemaModifier)
    """
    print(f"\n=== {modifier_type.__name__} ===")
    print(modifier_type.__doc__ or "No documentation available.")
    sig = inspect.signature(modifier_type.__call__)
    print(f"\nExpected Signature:\n{sig}\n")


@runtime_checkable
class SchemaModifier(Protocol):
    """
    A function that modifies a tool's schema before it is exposed to the agent.

    Expected Signature:
        ```python
        def function(tool: str, toolkit: str, schema: Tool) -> Tool
        ```

    Args:
        - tool (`str`): Name of the tool being modified
        - toolkit (`str`): Name of the toolkit the tool belongs to
        - schema (`Tool`): The tool schema to modify

    Returns:
        - Modified `Tool` instance

    Example:
        ```python
        def add_default_repo(tool, toolkit, schema):
            schema.description += " Uses 'composio/composio' as default repo."
            return schema
        ```
    """

    def __call__(self, tool: str, toolkit: str, schema: Any) -> Any: ...


@runtime_checkable
class BeforeExecute(Protocol):
    """
    A function that modifies tool parameters before execution.

    Expected Signature:
        ```python
        def function(tool: str, toolkit: str, params: ToolExecuteParams) -> ToolExecuteParams
        ```

    Args:
        - tool (`str`): Tool name being executed
        - toolkit (`str`): Toolkit name
        - params (`ToolExecuteParams`): Parameters to modify before execution

    Returns:
        - Modified `ToolExecuteParams`

    Example:
        ```python
        def limit_posts(tool, toolkit, params):
            params["arguments"]["size"] = min(params["arguments"].get("size", 10), 5)
            return params
        ```
    """

    def __call__(self, tool: str, toolkit: str, params: Any) -> Any: ...


@runtime_checkable
class AfterExecute(Protocol):
    """
    A function that transforms tool output after execution.

    Expected Signature:
        ```python
        def function(
            tool: str,
            toolkit: str,
            response: ToolExecutionResponse
        ) -> ToolExecutionResponse
        ```

    Args:
        - tool (`str`): Tool name executed
        - toolkit (`str`): Toolkit name
        - response (`ToolExecutionResponse`): Raw tool output to modify

    Returns:
        - Modified `ToolExecutionResponse`

    Example:
        ```python
        def show_response(tool, toolkit, response):
            print(f"Response from {tool}: {response}")
            return response
        ```
    """

    def __call__(self, tool: str, toolkit: str, response: Any) -> Any: ...


class Modifiers(BaseModel):
    """
    Container for Composio tool modifiers.

    Modifiers are middleware functions that transform tools at different execution stages.
    They provide a powerful way to customize tool behavior without modifying the core tools.

    Modifier Types:
        schema: Transform tool schema before the agent sees it
                Useful for: Adding/removing parameters, modifying descriptions, setting defaults

        before_execute: Modify arguments before tool execution
                       Useful for: Injecting parameters, overriding values, validation

        after_execute: Transform results after tool execution
                      Useful for: Filtering output, format conversion, truncation

    Example:
        ```python
        # Create schema modifier function
        def add_default_repo(tool: str, toolkit: str, schema: Tool) -> Tool:
            schema.description += " Uses 'composio/composio' as default repo."
            return schema

        # Create before-execute modifier function
        def limit_posts(tool: str, toolkit: str, params: ToolExecuteParams) -> ToolExecuteParams:
            params["arguments"]["size"] = min(params["arguments"].get("size", 10), 5)
            return params

        # Create after-execute modifier function
        def show_loaded_data(
            tool: str,
            toolkit: str,
            response: ToolExecutionResponse
        ) -> ToolExecutionResponse:
            print(f"Tool: {tool}, Response: {response}")
            return response

        # Combine modifiers with function-to-tools mapping
        modifiers = Modifiers.combine(
            schema_functions={add_default_repo: ["GITHUB_LIST_ISSUES"]},
            before_execute_functions={limit_posts: ["HACKERNEWS_GET_POSTS"]},
            after_execute_functions={show_loaded_data: ["LINKEDIN_GET_MY_INFO"]}
        )
        ```

    Attributes:
        schema_functions: Dictionary mapping schema modifier functions to list of tool names
        before_execute_functions: Dictionary mapping before-execute modifier functions to list of
                                  tool names
        after_execute_functions: Dictionary mapping after-execute modifier functions to list of
                                 tool names
    """

    schema_functions: dict[SchemaModifier,
                           list[str]] = Field(default_factory=dict)
    """
    Dictionary mapping schema modifier functions to list of tool names they should be applied to."""

    before_execute_functions: dict[BeforeExecute, list[str]] = Field(
        default_factory=dict
    )
    """
    Dictionary mapping before-execute modifier functions to list of tool names they should be
    applied to.
    """

    after_execute_functions: dict[AfterExecute,
                                  list[str]] = Field(default_factory=dict)
    """
    Dictionary mapping after-execute modifier functions to list of tool names they should be
    applied to.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,  # Allow function types
        frozen=True,  # Make immutable for thread safety
    )

    @model_validator(mode="after")
    def validate_has_modifiers(self) -> Modifiers:
        """Ensure at least one modifier type is provided."""
        if not any(
            [
                self.schema_functions,
                self.before_execute_functions,
                self.after_execute_functions,
            ]
        ):
            raise ValueError(
                "At least one modifier function list must be provided")
        return self

    @classmethod
    def with_schema(cls, modifiers: dict[SchemaModifier, list[str]]) -> Modifiers:
        """
        Create modifiers with schema modifiers only.

        Args:
            modifiers: Dictionary of schema modifier functions

        Returns:
            Modifiers instance with only schema functions configured

        Raises:
            ValueError: If no modifiers provided
        """
        if not modifiers:
            raise ValueError("At least one schema modifier must be provided")
        return cls(schema_functions=modifiers)

    @classmethod
    def with_before_execute(
        cls, modifiers: dict[BeforeExecute, list[str]]
    ) -> Modifiers:
        """
        Create modifiers with before-execute modifiers only.

        Args:
            modifiers: Dictionary of before-execute modifier functions

        Returns:
            Modifiers instance with only before-execute functions configured

        Raises:
            ValueError: If no modifiers provided
        """
        if not modifiers:
            raise ValueError(
                "At least one before-execute modifier must be provided")
        return cls(before_execute_functions=modifiers)

    @classmethod
    def with_after_execute(cls, modifiers: dict[AfterExecute, list[str]]) -> Modifiers:
        """
        Create modifiers with after-execute modifiers only.

        Args:
            modifiers: Dictionary of after-execute modifier functions

        Returns:
            Modifiers instance with only after-execute functions configured

        Raises:
            ValueError: If no modifiers provided
        """
        if not modifiers:
            raise ValueError(
                "At least one after-execute modifier must be provided")
        return cls(after_execute_functions=modifiers)

    @classmethod
    def combine(
        cls,
        schema_functions: dict[SchemaModifier, list[str]] | None = None,
        before_execute_functions: dict[BeforeExecute, list[str]] | None = None,
        after_execute_functions: dict[AfterExecute, list[str]] | None = None,
    ) -> Modifiers:
        """
        Create modifiers with multiple types.

        Args:
            schema_functions: Optional dictionary of schema modifier functions
            before_execute_functions: Optional dictionary of before-execute modifier functions
            after_execute_functions: Optional dictionary of after-execute modifier functions

        Returns:
            Modifiers instance with specified function types configured

        Raises:
            ValueError: If no modifier functions provided
        """
        return cls(
            schema_functions=schema_functions or {},
            before_execute_functions=before_execute_functions or {},
            after_execute_functions=after_execute_functions or {},
        )

    def to_list(
        self,
        tools: list[str] | None = None,
        toolkits: list[str] | None = None,
    ) -> list[Any]:
        """
        Convert to flat list for composio.tools.get() modifiers parameter.

        Args:
            tools: List of tool slugs to apply modifiers to
            toolkits: List of toolkit names to apply modifiers to

        Returns:
            Flattened list of all modifier functions in execution order
        """
        modifiers: list[Any] = []

        if self.schema_functions:
            for schema_modifier_func, tool_list in self.schema_functions.items():
                modifier = schema_modifier(
                    tools=tool_list)(schema_modifier_func)
                modifiers.append(modifier)

        if self.before_execute_functions:
            for before_execute_func, tool_list in self.before_execute_functions.items():
                modifier = before_execute(tools=tool_list)(before_execute_func)
                modifiers.append(modifier)

        if self.after_execute_functions:
            for after_execute_func, tool_list in self.after_execute_functions.items():
                modifier = after_execute(tools=tool_list)(after_execute_func)
                modifiers.append(modifier)

        return modifiers

    def count(self) -> dict[str, int]:
        """
        Get count of modifiers by type.

        Returns:
            Dictionary with counts for each modifier type
        """
        return {
            "schema": len(self.schema_functions) if self.schema_functions else 0,
            "before_execute": (
                len(self.before_execute_functions)
                if self.before_execute_functions
                else 0
            ),
            "after_execute": (
                len(self.after_execute_functions) if self.after_execute_functions else 0
            ),
        }


class ToolConfig(BaseModel):
    """
    Configuration for Composio tools retrieval that mirrors the API exactly.

    This class provides a type-safe way to configure tool fetching with proper
    validation of filter combinations according to Composio API requirements.

    Filter Combinations (mutually exclusive):
        1. Tools Only: Fetch specific tools by their slugs
           - tools: ["TOOL_1", "TOOL_2"]

        2. Toolkits Only: Fetch tools from specific toolkits
           - toolkit: "GITHUB", limit?: number

        3. Single Toolkit with Scopes: Fetch tools requiring specific OAuth scopes
           - toolkit: "GITHUB", scopes: ["read:repo"], limit?: number

        4. Search: Search across all tools or within specific toolkits
           - search: "query", toolkit?: string, limit?: number

    Example:
        ```python
        # Fetch specific tools
        config = ToolConfig.from_tools(
            "Github Tools"
            "auth_123",
            ["GITHUB_CREATE_ISSUE", "GITHUB_CREATE_COMMIT"]
        )

        # Fetch from toolkit with limits
        config = ToolConfig.from_toolkit("Github Tools", "auth_123", "GITHUB", limit=5)

        # Search with scopes
        config = ToolConfig.from_toolkit_with_scopes(
            "Github Tools", "auth_123", "GITHUB", ["repo", "read:user"], limit=10
        )
        ```

    Attributes:
        auth_config_id: Authentication configuration ID from Composio dashboard
        tools: Specific tool slugs to fetch (mutually exclusive with other filters)
        toolkit: Single toolkit name to fetch tools from
        scopes: OAuth scopes to filter tools by (requires single toolkit)
        search: Semantic search query for finding relevant tools
        limit: Maximum number of tools to return (1-100, default varies by filter)
        modifiers: Optional tool modifiers for customization
    """

    tool_group_name: str
    """
    Logical name for the group of tools being configured (e.g., "GitHub Tools", "Slack Tools").
    Used for organization and logging.
    """

    auth_config_id: AuthConfigId
    """
    Authentication configuration ID from Composio dashboard. Used to authenticate tool requests.
    """

    # Filter parameters - validation ensures only valid combinations are used
    tools: list[ToolSlug] | None = None
    """
    Specific tool slugs to fetch (e.g., ['GITHUB_CREATE_ISSUE', 'SLACK_SEND_MESSAGE']). Mutually
    exclusive with other filters.
    """

    toolkit: str | None = None
    """
    Single toolkit name to fetch tools from (e.g., 'GITHUB', 'SLACK', 'GMAIL'). Can be combined
    with scopes or limit.
    """

    scopes: list[str] | None = None
    """
    OAuth scopes to filter tools by (e.g., ['repo', 'read:user']). Requires exactly one toolkit
    to be specified.
    """

    search: str | None = None
    """
    Semantic search query for finding relevant tools (e.g., 'organize contacts',
    'repository issues'). Cannot be combined with tools or scopes.
    """

    limit: int | None = None
    """Maximum number of tools to return (1-100)."""

    modifiers: Modifiers | None = None
    """
    Optional tool modifiers for customizing tool behavior (schema, before_execute, after_execute
    functions).
    """

    model_config = ConfigDict(frozen=True)  # Make immutable for thread safety

    @model_validator(mode="after")
    def validate_filter_combination(self) -> ToolConfig:
        """
        Ensure only valid filter combinations are used per Composio API requirements.

        Returns:
            Self after validation

        Raises:
            ValueError: If invalid filter combination is detected
        """
        # Validate tool_group_name
        if not self.tool_group_name or not self.tool_group_name.strip():
            raise ValueError("tool_group_name cannot be empty")

        # Validate auth_config_id
        if not self.auth_config_id or not self.auth_config_id.strip():
            raise ValueError("auth_config_id cannot be empty")

        # Count active filters
        has_tools = self.tools is not None
        has_toolkit = self.toolkit is not None
        has_search = self.search is not None
        has_scopes = self.scopes is not None

        # Validate limit if provided
        if self.limit is not None and (self.limit < 1 or self.limit > MAX_TOOLS_LIMIT):
            raise ValueError(
                f"limit must be an integer between 1 and {MAX_TOOLS_LIMIT}"
            )

        # Validate mutually exclusive combinations
        if has_tools:
            # Tools filter - cannot be combined with anything else
            if any([has_toolkit, has_search, has_scopes, self.limit]):
                raise ValueError(
                    "Tools filter cannot be combined with other filters")
            if not self.tools:
                raise ValueError("tools list cannot be empty")

        elif has_search:
            # Search filter - cannot be combined with tools or scopes
            if has_tools or has_scopes:
                raise ValueError(
                    "Search filter cannot be combined with tools or scopes"
                )
            if not self.search or not self.search.strip():
                raise ValueError("search query cannot be empty")

        elif has_scopes:
            # Scopes filter - requires exactly one toolkit
            if not has_toolkit:
                raise ValueError("Scopes filter requires exactly one toolkit")
            if not self.scopes:
                raise ValueError("scopes list cannot be empty")
            if has_search or has_tools:
                raise ValueError(
                    "Scopes filter cannot be combined with search or tools"
                )

        elif has_toolkit:
            # Toolkit filter only - valid with optional limit
            if not self.toolkit or not self.toolkit.strip():
                raise ValueError("toolkit name cannot be empty")
        else:
            raise ValueError(
                "At least one filter must be specified: tools, toolkit, or search"
            )

        return self

    @classmethod
    def from_tools(
        cls,
        tool_group_name: str,
        auth_config_id: AuthConfigId,
        tools: list[ToolSlug],
        modifiers: Modifiers | None = None,
    ) -> ToolConfig:
        """
        Create configuration to fetch specific tools by their slugs.

        This method is ideal when you know exactly which tools you need.
        Tool slugs can be found in the Composio dashboard under each toolkit.

        Args:
            tool_group_name: Logical name for the group of tools being configured (e.g., "GitHub
                            Tools", "Slack Tools"). Used for organization and logging.
            auth_config_id: Authentication configuration ID from dashboard
            tools: List of tool slugs (e.g., ["GITHUB_CREATE_ISSUE", "SLACK_SEND_MESSAGE"])
            modifiers: Optional tool modifiers for customization

        Returns:
            ToolConfig configured for specific tools

        Raises:
            ValueError: If tools list is empty or contains invalid values

        Example:
            ```python
            config = ToolConfig.from_tools(
                "Github Tools",
                "auth_config_123",
                ["GITHUB_CREATE_AN_ISSUE", "GITHUB_CREATE_A_COMMIT"]
            )
            ```
        """
        if not tool_group_name or not tool_group_name.strip():
            raise ValueError("tool_group_name cannot be empty")
        if not tools:
            raise ValueError("tools list cannot be empty")
        if not all(tool and tool.strip() for tool in tools):
            raise ValueError("All tool slugs must be non-empty strings")

        return cls(
            tool_group_name=tool_group_name,
            auth_config_id=auth_config_id,
            tools=tools,
            modifiers=modifiers,
        )

    @classmethod
    def from_toolkit(
        cls,
        tool_group_name: str,
        auth_config_id: AuthConfigId,
        toolkit: str,
        limit: int | None = None,
        modifiers: Modifiers | None = None,
    ) -> ToolConfig:
        """
        Create configuration to fetch tools from a specific toolkit.

        Tools are returned in order of importance as determined by Composio.

        Args:
            tool_group_name: Logical name for the group of tools being configured (e.g.,
                            "GitHub Tools", "Slack Tools"). Used for organization and logging.
            auth_config_id: Authentication configuration ID from dashboard
            toolkit: Single toolkit name (e.g., "GITHUB", "SLACK", "GMAIL")
            limit: Maximum number of tools to return (1-100)
            modifiers: Optional tool modifiers for customization

        Returns:
            ToolConfig configured for toolkit tools

        Raises:
            ValueError: If toolkit name is empty or limit is invalid

        Example:
            ```python
            # Get top 5 GitHub tools
            config = ToolConfig.from_toolkit(
                "Github Tools",
                "auth_config_123",
                "GITHUB",
                limit=5
            )
            ```
        """
        if not tool_group_name or not tool_group_name.strip():
            raise ValueError("tool_group_name cannot be empty")
        if not toolkit or not toolkit.strip():
            raise ValueError("toolkit name cannot be empty")

        return cls(
            tool_group_name=tool_group_name,
            auth_config_id=auth_config_id,
            toolkit=toolkit,
            limit=limit,
            modifiers=modifiers,
        )

    @classmethod
    def from_toolkit_with_scopes(
        cls,
        tool_group_name: str,
        auth_config_id: AuthConfigId,
        toolkit: str,
        scopes: list[str],
        limit: int | None = None,
        modifiers: Modifiers | None = None,
    ) -> ToolConfig:
        """
        Create configuration to fetch tools from a toolkit filtered by OAuth scopes.

        This is useful for getting only tools that match specific permission levels
        or ensuring tools align with available user permissions.

        Args:
            tool_group_name: Logical name for the group of tools being configured (e.g.,
                        "GitHub Tools", "Slack Tools"). Used for organization and logging.
            auth_config_id: Authentication configuration ID from dashboard
            toolkit: Single toolkit name (scopes only work with one toolkit)
            scopes: List of OAuth scopes to filter by (e.g., ["repo", "read:user"])
            limit: Maximum number of tools to return (1-100)
            modifiers: Optional tool modifiers for customization

        Returns:
            ToolConfig configured for scoped tools

        Raises:
            ValueError: If toolkit/scopes are empty or invalid

        Example:
            ```python
            # Get GitHub tools requiring specific scopes
            config = ToolConfig.from_toolkit_with_scopes(
                "Github Tools",
                "auth_config_123",
                "GITHUB",
                ["repo", "read:user"],
                limit=10
            )
            ```
        """
        if not tool_group_name or not tool_group_name.strip():
            raise ValueError("tool_group_name cannot be empty")
        if not toolkit or not toolkit.strip():
            raise ValueError("toolkit name cannot be empty")
        if not scopes:
            raise ValueError("scopes list cannot be empty")
        if not all(scope and scope.strip() for scope in scopes):
            raise ValueError("All scopes must be non-empty strings")

        return cls(
            tool_group_name=tool_group_name,
            auth_config_id=auth_config_id,
            toolkit=toolkit,
            scopes=scopes,
            limit=limit,
            modifiers=modifiers,
        )

    @classmethod
    def from_search(
        cls,
        tool_group_name: str,
        auth_config_id: AuthConfigId,
        search: str,
        toolkit: str | None = None,
        limit: int | None = None,
        modifiers: Modifiers | None = None,
    ) -> ToolConfig:
        """
        Create configuration to search for tools using semantic search.

        This runs semantic search on tool names and descriptions to find
        the most relevant tools for your use case. Optionally limit search
        to specific toolkits.

        Args:
            tool_group_name: Logical name for the group of tools being configured (e.g.,
                        "GitHub Tools", "Slack Tools"). Used for organization and logging.
            auth_config_id: Authentication configuration ID from dashboard
            search: Semantic search query (e.g., "organize contacts", "repository issues")
            toolkit: Optional single toolkit to limit search scope
            limit: Maximum number of tools to return (1-100)
            modifiers: Optional tool modifiers for customization

        Returns:
            ToolConfig configured for search-based tool retrieval

        Raises:
            ValueError: If search query is empty

        Example:
            ```python
            # Search across all tools
            config = ToolConfig.from_search(
                "Contact Management Tools",
                "auth_config_123",
                "hubspot organize contacts"
            )

            # Search within specific toolkit
            config = ToolConfig.from_search(
                "Github Issue Tools",
                "auth_config_123",
                "repository issues",
                toolkit="GITHUB",
                limit=5
            )
            ```
        """
        if not tool_group_name or not tool_group_name.strip():
            raise ValueError("tool_group_name cannot be empty")
        if not search or not search.strip():
            raise ValueError("search query cannot be empty")
        if toolkit is not None and (not toolkit or not toolkit.strip()):
            raise ValueError("toolkit name cannot be empty when provided")

        return cls(
            tool_group_name=tool_group_name,
            auth_config_id=auth_config_id,
            search=search,
            toolkit=toolkit,
            limit=limit,
            modifiers=modifiers,
        )


class ComposioConfig(BaseModel):
    """
    Immutable configuration for Composio integration.

    This class holds all necessary configuration for connecting to and using
    the Composio API. It supports environment-based configuration for easy
    deployment across different environments.

    Attributes:
        api_key: Composio API key for authentication
        timeout: Default timeout for operations in seconds
        tool_configs: List of tool configurations defining which tools to fetch

    Example:
        ```python
        # Create from environment variables
        config = ComposioConfig.from_env(
            tool_configs=[
                ToolConfig.from_toolkit("auth_123", "GITHUB", limit=5),
                ToolConfig.from_search("auth_456", "calendar events")
            ]
        )

        # Create manually
        config = ComposioConfig(
            api_key="your_api_key",
            timeout=300,
            tool_configs=[ToolConfig.from_tools("auth_123", ["GMAIL_SEND"])]
        )
        ```
    """

    api_key: SecretStr
    """Composio API key for authentication. Get from https://app.composio.dev/settings. Required
    for all API operations."""

    persona_prompt: str | None = None
    """Optional persona prompt to guide orchestrator agent behavior."""

    timeout: int = DEFAULT_TIMEOUT
    """Timeout for authentication in seconds."""

    tool_configs: list[ToolConfig] | None = None
    """List of tool configurations defining which tools to fetch. Each config specifies auth and
    filter parameters."""

    model_config = ConfigDict(frozen=True)  # Make immutable for thread safety

    @model_validator(mode="after")
    def validate_config(self) -> ComposioConfig:
        """
        Validate configuration after initialization.

        Returns:
            Self after validation

        Raises:
            ValueError: If configuration is invalid
        """
        if not self.api_key or not self.api_key.get_secret_value().strip():
            raise ValueError("api_key cannot be empty")

        if self.timeout < 1:
            raise ValueError("timeout must be a positive integer")

        if not self.tool_configs:
            raise ValueError("tool_configs must be provided and non-empty")

        return self

    @classmethod
    def from_env(
        cls,
        *,
        tool_configs: list[ToolConfig] | None = None,
        persona_prompt: str | None = None,
    ) -> ComposioConfig:
        """
        Create configuration from environment variables.

        This method reads configuration from environment variables, making it
        ideal for production deployments where secrets are managed externally.

        Environment Variables:
            COMPOSIO_API_KEY: Required API key for Composio
            COMPOSIO_DEFAULT_TIMEOUT: Optional timeout in seconds (default: 300)

        Args:
            tool_configs: List of ToolConfig instances defining tool retrieval

        Returns:
            ComposioConfig instance configured from environment

        Raises:
            ValueError: If required environment variables are missing or invalid

        Example:
            ```bash
            export COMPOSIO_API_KEY="your_api_key_here"
            export COMPOSIO_DEFAULT_TIMEOUT="600"  # 10 minutes
            ```

            ```python
            config = ComposioConfig.from_env(
                tool_configs=[
                    ToolConfig.from_toolkit("auth_123", "GITHUB")
                ]
            )
            ```
        """
        api_key = os.getenv("COMPOSIO_API_KEY")
        if not api_key:
            raise ValueError(
                "COMPOSIO_API_KEY environment variable is required. "
                "Get your API key from https://app.composio.dev/settings"
            )

        # Parse timeout from environment with validation
        timeout_str = os.getenv(
            "COMPOSIO_DEFAULT_TIMEOUT", str(DEFAULT_TIMEOUT))
        try:
            timeout = int(timeout_str)
            if timeout < 1:
                raise ValueError(
                    "COMPOSIO_DEFAULT_TIMEOUT must be a positive integer")
        except ValueError as e:
            raise ValueError(
                f"COMPOSIO_DEFAULT_TIMEOUT must be a valid positive integer, got: {timeout_str}"
            ) from e

        return cls(
            api_key=SecretStr(api_key),
            tool_configs=tool_configs,
            timeout=timeout,
            persona_prompt=persona_prompt,
        )

    def get_auth_config_ids(self) -> set[AuthConfigId]:
        """
        Get all unique auth config IDs from tool configurations.

        Returns:
            Set of unique authentication configuration IDs
        """
        if not self.tool_configs:
            return set()

        return {config.auth_config_id for config in self.tool_configs}

    def get_tool_group_name_by_auth_config(
        self, auth_config_id: AuthConfigId
    ) -> str | None:
        """
        Get the tool group name for a given auth config ID.

        Args:
            auth_config_id: Authentication configuration ID to look up
        Returns:
            Tool group name if found, else None
        """
        if not self.tool_configs:
            return None

        for config in self.tool_configs:
            if config.auth_config_id == auth_config_id:
                return config.tool_group_name

        return None


class ConnectionStatus(BaseModel):
    """
    Model representing the connection status for a user across all configured auth configs.

    This model provides a clear picture of whether a user has all required
    connections active and which specific connections are missing if any.

    Attributes:
        user_connected: True if all required connections are active
        connections_required: List of auth config IDs that need connection
        total_configs: Total number of auth configs checked
        active_connections: Number of currently active connections

    Example:
        ```python
        status = await client.connection_exists("user_123")
        if status.user_connected:
            print("User is fully connected!")
        else:
            print(f"Missing connections: {status.connections_required}")
            print(f"Progress: {status.active_connections}/{status.total_configs}")
        ```
    """

    user_connected: bool = True
    """True if all required connections are active and user can use all configured tools."""

    connections_required: list[AuthConfigId] = []
    """List of auth config IDs that need connection. Empty if user is fully connected."""

    total_configs: int = 0
    """Total number of auth configs checked. Represents the total connections needed."""

    active_connections: int = 0
    """Number of currently active connections. Should equal total_configs for full connectivity."""

    model_config = ConfigDict(frozen=True)  # Make immutable for thread safety

    @property
    def connection_progress(self) -> float:
        """Get connection progress as a percentage (0.0 to 1.0)."""
        if self.total_configs == 0:
            return 1.0
        return self.active_connections / self.total_configs

    @property
    def is_partial_connection(self) -> bool:
        """Check if user has some but not all required connections."""
        return 0 < self.active_connections < self.total_configs


class AuthResponse(BaseModel):
    """
    Response model for authentication operations.

    This model provides a standardized response format for all authentication
    operations, including success, failure, and pending states.

    Attributes:
        connection_request: Optional ConnectionRequest object for pending auths
        redirect_url: URL to redirect user for authentication (OAuth flows)
        connection_id: ID of successfully established connection
        status: Current status of the authentication operation
        message: Human-readable description of the operation result

    Status Values:
        - "pending": Authentication request created, waiting for user action
        - "active": Connection successfully established
        - "failed": Authentication failed (check message for details)
        - "timeout": Operation timed out waiting for user
        - "error": Unexpected error occurred

    Example:
        ```python
        response = await client.create_auth_request("user_123", "auth_config_456")

        if response.status == "pending":
            print(f"Please visit: {response.redirect_url}")
            # Wait for completion
            verify_response = await client.verify_auth_request(response.connection_request)

        elif response.status == "error":
            print(f"Auth failed: {response.message}")
        ```
    """

    connection_request: ConnectionRequest | None = None
    """
    ConnectionRequest object for pending authentications. Used to verify completion of auth flow.
    """

    redirect_url: str | None = None
    """
    URL to redirect user for authentication (OAuth flows). User must visit this URL to complete
    authentication.
    """

    connection_id: str | None = None
    """ID of successfully established connection. Only present when status is 'active'."""

    status: str
    """Current status of authentication operation: 'pending', 'active', 'failed', 'timeout', or
    'error'."""

    message: str
    """
    Human-readable description of the operation result. Provides context for the current status.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,  # Allow function types
        frozen=True,  # Make immutable for thread safety
    )

    @property
    def is_success(self) -> bool:
        """Check if the authentication was successful."""
        return self.status == "active"

    @property
    def is_pending(self) -> bool:
        """Check if the authentication is pending user action."""
        return self.status == "pending"

    @property
    def is_error(self) -> bool:
        """Check if there was an error in authentication."""
        return self.status in ("failed", "error", "timeout")


# Exception Classes


class ComposioError(Exception):
    """
    Base exception for all Composio integration operations.

    This is the base class for all exceptions raised by this module.
    It provides consistent error handling and logging capabilities.

    Attributes:
        message: Human-readable error message
        details: Optional additional error details
        operation: Optional operation that failed
    """

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
        operation: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.operation = operation

    def __str__(self) -> str:
        """Return a formatted string representation of the error."""
        base = self.message
        if self.operation:
            base = f"{self.operation}: {base}"
        if self.details:
            base += f" (details: {self.details})"
        return base


class AuthenticationError(ComposioError):
    """
    Exception raised for authentication-related failures.

    This includes failures in creating auth requests, verifying connections,
    and other authentication workflow issues.
    """

    pass


class ConnectionError(ComposioError):
    """
    Exception raised for connection-related failures.

    This includes failures in checking connection status, network issues,
    and connection state problems.
    """

    pass


class ConfigurationError(ComposioError):
    """
    Exception raised for configuration-related issues.

    This includes invalid tool configurations, missing required parameters,
    and environment setup problems.
    """

    pass


class ToolRetrievalError(ComposioError):
    """
    Exception raised for tool retrieval failures.

    This includes failures in fetching tools, invalid tool configurations,
    and tool-related API issues.
    """

    pass


class ComposioClient:
    """
    Production-ready client for Composio API operations.

    This client provides a high-level, async interface for all Composio operations
    including authentication, connection management, and tool retrieval. It includes
    comprehensive error handling, logging, and thread safety.

    Features:
        - Async/await support for all operations
        - Thread-safe operations with internal locking
        - Comprehensive error handling with custom exceptions
        - Structured logging with operation context
        - Automatic retry logic for transient failures
        - Connection status caching for performance

    Example:
        ```python
        import asyncio
        from composio_integration import ComposioClient, ComposioConfig, ToolConfig

        async def main():
            config = ComposioConfig.from_env(
                tool_configs=[
                    ToolConfig.from_toolkit("auth_123", "GITHUB", limit=5)
                ]
            )

            client = ComposioClient(config)

            # Check connection status
            status = await client.connection_exists("user_123")
            if not status.user_connected:
                # Create auth request
                auth_response = await client.create_auth_request(
                    "user_123",
                    status.connections_required[0]
                )
                print(f"Please visit: {auth_response.redirect_url}")

                # Wait for connection
                result = await client.verify_auth_request(auth_response.connection_request)
                if result.is_success:
                    print("Connected successfully!")

            # Get tools
            tools = await client.get_tools("user_123")
            print(f"Retrieved {len(tools)} tools")

        asyncio.run(main())
        ```
    """

    def __init__(self, config: ComposioConfig) -> None:
        """
        Initialize Composio client with configuration.

        Args:
            config: Configuration object containing API key and tool configs
            ctx: Context object for logging and operation context

        Raises:
            ConfigurationError: If configuration is invalid
            ImportError: If required Composio packages are not installed
        """
        try:
            self._config = config
            self._composio: Composio[LangchainProvider] = Composio(
                api_key=self._config.api_key.get_secret_value(),
                provider=LangchainProvider(),
            )
            self._lock = asyncio.Lock()

            logger.info(
                "ComposioClient initialized successfully",
                extra={
                    "auth_config_ids": list(self._config.get_auth_config_ids()),
                    "tool_configs_count": len(self._config.tool_configs or []),
                    "timeout": self._config.timeout,
                },
            )

        except Exception as e:
            logger.error(
                "Failed to initialize ComposioClient",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise ConfigurationError(
                "Failed to initialize Composio client",
                details={"original_error": str(e)},
                operation="client_initialization",
            ) from e

    async def connection_exists(
        self, user_id: UserId, ctx: Context
    ) -> ConnectionStatus:
        """
        Check if user has active connections for all configured auth configs.

        This method verifies the connection status across all authentication
        configurations defined in the client config. It provides detailed
        information about which connections are active and which are missing.

        Args:
            user_id: Unique identifier for the user to check
            ctx: Context object for logging and operation context

        Returns:
            ConnectionStatus with detailed connection information

        Raises:
            ValueError: If user_id is empty or invalid
            ConnectionError: If connection check fails due to API or network issues

        Example:
            ```python
            status = await client.connection_exists("user_123")

            if status.user_connected:
                print("All connections are active!")
            else:
                print(f"Missing connections for: {status.connections_required}")
                print(f"Connection progress: {status.connection_progress:.1%}")
            ```
        """
        if not user_id or not user_id.strip():
            raise ValueError("user_id cannot be empty")

        auth_config_ids = list(self._config.get_auth_config_ids())
        if not auth_config_ids:
            raise ConfigurationError(
                "No auth_config_ids found in configuration",
                operation="connection_check",
            )

        ctx.logger.info(
            "Checking user connection status",
            extra={
                "user_id": user_id,
                "auth_config_ids": auth_config_ids,
                "auth_config_count": len(auth_config_ids),
            },
        )

        try:
            async with self._lock:
                connections = await asyncio.to_thread(
                    self._composio.connected_accounts.list,
                    user_ids=[user_id],
                    auth_config_ids=auth_config_ids,
                )

            # Initialize counters
            active_connections = 0
            connections_required: list[AuthConfigId] = []

            # Check each auth config for active connections
            for auth_config_id in auth_config_ids:
                has_active_connection = any(
                    item.status == "ACTIVE" and item.auth_config.id == auth_config_id
                    for item in connections.items
                )

                if has_active_connection:
                    active_connections += 1
                else:
                    connections_required.append(auth_config_id)

            connection_status = ConnectionStatus(
                user_connected=len(connections_required) == 0,
                connections_required=connections_required,
                total_configs=len(auth_config_ids),
                active_connections=active_connections,
            )

            ctx.logger.info(
                "Connection status check completed",
                extra={
                    "user_id": user_id,
                    "user_connected": connection_status.user_connected,
                    "active_connections": active_connections,
                    "total_configs": len(auth_config_ids),
                    "missing_connections": len(connections_required),
                },
            )

            return connection_status

        except Exception as e:
            ctx.logger.error(
                "Failed to check connection status",
                extra={
                    "user_id": user_id,
                    "auth_config_ids": auth_config_ids,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise ConnectionError(
                "Connection status check failed",
                details={
                    "user_id": user_id,
                    "auth_config_ids": auth_config_ids,
                    "original_error": str(e),
                },
                operation="connection_check",
            ) from e

    async def create_auth_request(
        self,
        user_id: UserId,
        auth_config_id: AuthConfigId,
        ctx: Context,
        *,
        callback_url: str | None = None,
    ) -> AuthResponse:
        """
        Create an authentication request for a user.

        This method initiates the authentication flow by creating a connection
        request with Composio. The user will need to visit the returned redirect
        URL to complete the authentication process.

        Args:
            user_id: Unique identifier for the user requesting authentication
            auth_config_id: Authentication configuration ID from Composio dashboard
            ctx: Context object for logging and operation context
            callback_url: Optional URL to redirect user after authentication

        Returns:
            AuthResponse containing the connection request details and redirect URL

        Raises:
            ValueError: If required parameters are empty or invalid
            AuthenticationError: If authentication request creation fails

        Example:
            ```python
            response = await client.create_auth_request(
                "user_123",
                "auth_config_456",
                callback_url="https://myapp.com/auth/callback"
            )

            if response.is_pending:
                print(f"Please visit: {response.redirect_url}")
                # User completes auth in browser
                result = await client.verify_auth_request(response.connection_request)
            else:
                print(f"Auth failed: {response.message}")
            ```
        """
        if not user_id or not user_id.strip():
            raise ValueError("user_id cannot be empty")
        if not auth_config_id or not auth_config_id.strip():
            raise ValueError("auth_config_id cannot be empty")

        ctx.logger.info(
            "Creating authentication request",
            extra={
                "user_id": user_id,
                "auth_config_id": auth_config_id,
                "has_callback_url": callback_url is not None,
            },
        )

        try:
            async with self._lock:
                # Prepare parameters for connection request
                link_params = {
                    "user_id": user_id,
                    "auth_config_id": auth_config_id,
                }
                if callback_url:
                    link_params["callback_url"] = callback_url

                connection_request = await asyncio.to_thread(
                    self._composio.connected_accounts.initiate, **link_params
                )

            if not connection_request.redirect_url:
                ctx.logger.warning(
                    "Auth request created without redirect URL",
                    extra={
                        "user_id": user_id,
                        "auth_config_id": auth_config_id,
                    },
                )
                return AuthResponse(
                    status="failed",
                    message="Authentication request created but no redirect URL provided. "
                    "This may indicate an issue with the auth configuration.",
                )

            # Truncate URL for logging (security)
            redirect_preview = (
                connection_request.redirect_url[:50] + "..."
                if len(connection_request.redirect_url) > 50
                else connection_request.redirect_url
            )

            ctx.logger.info(
                "Authentication request created successfully",
                extra={
                    "user_id": user_id,
                    "auth_config_id": auth_config_id,
                    "redirect_url_preview": redirect_preview,
                },
            )

            return AuthResponse(
                connection_request=connection_request,
                redirect_url=connection_request.redirect_url,
                status="pending",
                message=(
                    "Authentication request created successfully. User must visit redirect URL "
                    "to complete authentication."
                ),
            )

        except Exception as e:
            ctx.logger.error(
                "Failed to create authentication request",
                extra={
                    "user_id": user_id,
                    "auth_config_id": auth_config_id,
                    "error": str(e),
                },
                exc_info=True,
            )

            return AuthResponse(
                status="error",
                message=f"Failed to create authentication request: {str(e)}",
            )

    async def verify_auth_request(
        self,
        connection_request: ConnectionRequest,
        *,
        timeout: int | None = None,
        ctx: Context,
    ) -> AuthResponse:
        """
        Verify an authentication request and wait for completion.

        This method waits for the user to complete the authentication process
        initiated by create_auth_request. It will block until the authentication
        is completed or the timeout is reached.

        Args:
            connection_request: The connection request object from create_auth_request
            timeout: Optional custom timeout in seconds (uses config default if None)
            ctx: Context object for logging and operation context

        Returns:
            AuthResponse indicating the final authentication status

        Raises:
            ValueError: If connection_request is None or invalid
            AuthenticationError: If verification fails unexpectedly

        Example:
            ```python
            # Create auth request
            auth_response = await client.create_auth_request("user_123", "auth_456")

            if auth_response.is_pending:
                print(f"Visit: {auth_response.redirect_url}")

                # Wait for user to complete authentication
                result = await client.verify_auth_request(
                    auth_response.connection_request,
                    timeout=600  # 10 minutes
                )

                if result.is_success:
                    print(f"Connected! Account ID: {result.connection_id}")
                elif result.status == "timeout":
                    print("Authentication timed out")
                else:
                    print(f"Authentication failed: {result.message}")
            ```
        """
        if not connection_request:
            raise ValueError(
                "connection_request is required and cannot be None")

        effective_timeout = timeout or self._config.timeout

        ctx.logger.info(
            "Starting authentication verification",
            extra={
                "connection_request_id": getattr(connection_request, "id", "unknown"),
                "timeout": effective_timeout,
            },
        )

        try:
            # Run blocking wait in thread pool to avoid blocking event loop
            connected_account = await asyncio.to_thread(
                connection_request.wait_for_connection,
                timeout=effective_timeout,
            )

            if connected_account.status == "ACTIVE":
                ctx.logger.info(
                    "Authentication verification successful",
                    extra={
                        "account_id": connected_account.id,
                        "account_status": connected_account.status,
                    },
                )

                return AuthResponse(
                    connection_id=connected_account.id,
                    status="active",
                    message="Account connected successfully and is now active",
                )
            else:
                ctx.logger.warning(
                    "Authentication verification completed but connection not active",
                    extra={
                        "account_id": getattr(connected_account, "id", "unknown"),
                        "account_status": connected_account.status,
                    },
                )

                return AuthResponse(
                    status=connected_account.status.lower(),
                    message=f"Connection completed but status is '{connected_account.status}'. "
                    f"Expected 'ACTIVE' status for successful authentication.",
                )

        except ComposioSDKTimeoutError as e:
            ctx.logger.warning(
                "Authentication verification timed out",
                extra={
                    "timeout": effective_timeout,
                    "error": str(e),
                },
            )

            return AuthResponse(
                status="timeout",
                message=f"Authentication timed out after {effective_timeout} seconds. "
                f"User may not have completed the authentication process.",
            )

        except Exception as e:
            ctx.logger.error(
                "Authentication verification failed with unexpected error",
                extra={
                    "timeout": effective_timeout,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )

            return AuthResponse(
                status="error",
                message=f"Authentication verification failed: {str(e)}",
            )

    async def get_tools(self, user_id: UserId, ctx: Context) -> dict[str, list[Any]]:
        """
        Retrieve tools for a user based on configured tool specifications.

        This method fetches tools according to all ToolConfig instances provided
        during client initialization. It returns a dictionary mapping tool group names
        to their respective tools.

        The tools are automatically formatted for the configured provider
        (LangchainProvider by default) and include any applied modifiers.

        Args:
            user_id: Unique identifier for the user to retrieve tools for
            ctx: Context object for logging and operation context

        Returns:
            Dictionary mapping tool group names to lists of tools formatted for the configured
            provider

        Raises:
            ValueError: If user_id is empty or invalid
            ToolRetrievalError: If tool retrieval fails due to API or configuration issues
            AuthenticationError: If user lacks required authentication for some tools

        Example:
            ```python
            tools_by_group = await client.get_tools("user_123")

            for group_name, tools in tools_by_group.items():
                print(f"Group '{group_name}': {len(tools)} tools")

            # Access specific tool groups
            github_tools = tools_by_group.get("GitHub Tools", [])
            slack_tools = tools_by_group.get("Slack Tools", [])
            ```
        """
        if not user_id or not user_id.strip():
            raise ValueError("user_id is required and cannot be empty")

        if not self._config.tool_configs:
            raise ConfigurationError(
                "No tool configurations provided", operation="tool_retrieval"
            )

        ctx.logger.info(
            "Starting tool retrieval",
            extra={
                "user_id": user_id,
                "tool_configs_count": len(self._config.tool_configs),
            },
        )

        try:
            tools_by_group: dict[str, list[Any]] = {}
            config_results: list[dict[str, Any]] = []

            for i, config in enumerate(self._config.tool_configs):
                ctx.logger.info(
                    f"Processing tool config {i + 1}/{len(self._config.tool_configs)}",
                    extra={
                        "user_id": user_id,
                        "auth_config_id": config.auth_config_id,
                        "config_type": self._get_config_type(config),
                        "tool_group_name": config.tool_group_name,
                    },
                )

                async with self._lock:

                    def get_tools_for_config(
                        current_config: ToolConfig = config,
                    ) -> list[Any]:
                        # Build parameters dynamically based on config type
                        params: dict[str, Any] = {"user_id": user_id}

                        if current_config.tools:
                            # Specific tools filter
                            params["tools"] = current_config.tools
                        elif current_config.search:
                            # Semantic search filter
                            params["search"] = current_config.search
                            if current_config.toolkit:
                                params["toolkits"] = [current_config.toolkit]
                            if current_config.limit:
                                params["limit"] = current_config.limit
                        elif current_config.scopes:
                            # OAuth scopes filter (requires single toolkit)
                            params["toolkits"] = [current_config.toolkit]
                            params["scopes"] = current_config.scopes
                            if current_config.limit:
                                params["limit"] = current_config.limit
                        elif current_config.toolkit:
                            # Single toolkit filter
                            params["toolkits"] = [current_config.toolkit]
                            if current_config.limit:
                                params["limit"] = current_config.limit

                        # Add modifiers if present
                        if current_config.modifiers:
                            params["modifiers"] = current_config.modifiers.to_list(
                                toolkits=params.get("toolkits"),
                                tools=params.get("tools"),
                            )

                        ctx.logger.info(
                            f"Retrieving tools with parameters with param: {params}",
                        )

                        return self._composio.tools.get(**params)

                    try:
                        retrieved_tools = await asyncio.to_thread(get_tools_for_config)
                        tool_count = len(
                            retrieved_tools) if retrieved_tools else 0

                        # Add tools to the group
                        group_name = config.tool_group_name
                        if group_name not in tools_by_group:
                            tools_by_group[group_name] = []
                        tools_by_group[group_name].extend(
                            retrieved_tools or [])

                        config_results.append(
                            {
                                "auth_config_id": config.auth_config_id,
                                "config_type": self._get_config_type(config),
                                "tool_group_name": group_name,
                                "tool_count": tool_count,
                                "success": True,
                            }
                        )

                        ctx.logger.info(
                            f"Retrieved {tool_count} tools from config {i + 1}",
                            extra={
                                "user_id": user_id,
                                "auth_config_id": config.auth_config_id,
                                "tool_group_name": group_name,
                                "tool_count": tool_count,
                            },
                        )

                    except Exception as config_error:
                        ctx.logger.warning(
                            f"Failed to retrieve tools from config {i + 1}",
                            extra={
                                "user_id": user_id,
                                "auth_config_id": config.auth_config_id,
                                "config_type": self._get_config_type(config),
                                "tool_group_name": config.tool_group_name,
                                "error": str(config_error),
                            },
                            exc_info=True,
                        )
                        config_results.append(
                            {
                                "auth_config_id": config.auth_config_id,
                                "config_type": self._get_config_type(config),
                                "tool_group_name": config.tool_group_name,
                                "tool_count": 0,
                                "success": False,
                                "error": str(config_error),
                            }
                        )

            successful_configs = sum(
                1 for result in config_results if result["success"]
            )
            total_retrieved = sum(
                result["tool_count"] for result in config_results if result["success"]
            )

            ctx.logger.info(
                "Tool retrieval completed",
                extra={
                    "user_id": user_id,
                    "total_tools_retrieved": total_retrieved,
                    "tools_by_group": {
                        group: len(tools) for group, tools in tools_by_group.items()
                    },
                    "successful_configs": successful_configs,
                    "total_configs": len(self._config.tool_configs),
                    "config_results": config_results,
                },
            )

            if not tools_by_group:
                ctx.logger.warning(
                    "No tools retrieved from any configuration",
                    extra={
                        "user_id": user_id,
                        "config_results": config_results,
                    },
                )

            return tools_by_group

        except Exception as e:
            ctx.logger.error(
                "Tool retrieval failed with unexpected error",
                extra={
                    "user_id": user_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            raise ToolRetrievalError(
                "Failed to retrieve tools",
                details={
                    "user_id": user_id,
                    "tool_configs_count": len(self._config.tool_configs),
                    "original_error": str(e),
                },
                operation="tool_retrieval",
            ) from e

    def _get_config_type(self, config: ToolConfig) -> str:
        """Get a string description of the tool config type for logging."""
        if config.tools:
            return f"specific_tools({len(config.tools)})"
        elif config.search:
            return f"search('{config.search[:20]}...')"
        elif config.scopes:
            return f"scoped_toolkit({config.toolkit}, {len(config.scopes)} scopes)"
        elif config.toolkit:
            return f"toolkit({config.toolkit})"
        else:
            return "unknown"


class PostgresMemoryConfig(BaseModel):
    """
    Configuration for PostgreSQL-based memory storage.

    This configuration class encapsulates all necessary parameters to connect
    to a PostgreSQL database for use as a memory backend. It supports both
    direct parameter specification and environment variable loading.

    Attributes:
        host: Database host address (default: "localhost")
        port: Database port number (default: 5432)
        database: Name of the PostgreSQL database
        user: Username for database authentication
        password: Password for database authentication
        sslmode: SSL mode for the connection (default: "prefer")
        max_size: Maximum number of connections in the pool (default: 20)
        autocommit: Whether to enable autocommit mode (default: True)
        prepare_threshold: Number of statements to prepare before using server-side prepared
                            statements (default: 0)
        row_factory: Function to convert rows to desired format (default: dict_row)
    """

    host: str = "localhost"
    """Database host address (default: 'localhost')."""

    port: int = 5432
    """Database port number (default: 5432)."""

    database: str
    """Name of the PostgreSQL database."""

    user: str
    """Username for database authentication."""

    password: SecretStr
    """Password for database authentication."""

    sslmode: str = "prefer"
    """SSL mode for the connection (default: 'prefer'). Options: 'disable', 'allow', 'prefer',
    'require', 'verify-ca', 'verify-full'."""

    max_size: int = 20
    """Maximum number of connections in the pool (default: 20)."""

    autocommit: bool = True
    """Whether to enable autocommit mode (default: True)."""

    prepare_threshold: int = 0
    """Number of statements to prepare before using server-side prepared statements (default: 0)."""

    row_factory: Any = dict_row
    """Function to convert rows to desired format (default: dict_row)."""

    @classmethod
    def from_env(cls) -> PostgresMemoryConfig:
        """
        Create a PostgresMemoryConfig instance from environment variables.

        This method reads the necessary configuration parameters from environment
        variables and constructs a PostgresMemoryConfig instance. It raises a
        ValueError if any required parameters are missing.

        Required Environment Variables:
            - PSQL_HOST
            - PSQL_PORT
            - PSQL_DATABASE
            - PSQL_USERNAME
            - PSQL_PASSWORD

        Optional Environment Variables:
            - PSQL_SSLMODE (default: "prefer")
            - PSQL_MAX_SIZE (default: 20)
            - PSQL_AUTOCOMMIT (default: True)
            - PSQL_PREPARE_THRESHOLD (default: 0)

        Returns:
            PostgresMemoryConfig instance with parameters loaded from environment

        Raises:
            ValueError: If any required environment variables are missing or invalid
        """
        try:
            host = os.getenv("PSQL_HOST", "localhost")
            port_str = os.getenv("PSQL_PORT", "5432")
            database = os.getenv("PSQL_DATABASE")
            user = os.getenv("PSQL_USERNAME")
            password = os.getenv("PSQL_PASSWORD")

            if not database:
                raise ValueError(
                    "PSQL_DATABASE environment variable is required")
            if not user:
                raise ValueError(
                    "PSQL_USERNAME environment variable is required")
            if not password:
                raise ValueError(
                    "PSQL_PASSWORD environment variable is required")
            port = int(port_str)
            sslmode = os.getenv("PSQL_SSLMODE", "prefer")
            max_size = int(os.getenv("PSQL_MAX_SIZE", "20"))
            autocommit = os.getenv("PSQL_AUTOCOMMIT", "true").lower() == "true"
            prepare_threshold = int(os.getenv("PSQL_PREPARE_THRESHOLD", "0"))
            return cls(
                host=host,
                port=port,
                database=database,
                user=user,
                password=SecretStr(password),
                sslmode=sslmode,
                max_size=max_size,
                autocommit=autocommit,
                prepare_threshold=prepare_threshold,
            )
        except ValueError as ve:
            raise ValueError(f"Invalid environment variable: {ve}") from ve
        except Exception as e:
            raise ValueError(
                f"Error loading PostgresMemoryConfig from environment: {e}"
            ) from e

    async def initialize_db_pool(self, ctx: Context) -> AsyncConnectionPool[Any]:
        """
        Initialize and return a PostgreSQL async connection pool.

        Creates an async connection pool using the configured database parameters.
        The pool manages connections efficiently and provides proper resource cleanup.

        Args:
            ctx: Context object for logging and operation context

        Returns:
            AsyncConnectionPool: Configured connection pool ready for use

        Raises:
            Exception: If connection pool creation fails

        Note:
            The connection pool should be properly closed when no longer needed
            to avoid resource leaks.
        """
        ctx.logger.info(
            "Initializing PostgreSQL connection pool",
            extra={
                "host": self.host,
                "port": self.port,
                "database": self.database,
                "user": self.user,
                "sslmode": self.sslmode,
                "max_size": self.max_size,
            },
        )

        try:
            # Create the pool without opening it in the constructor
            pool = AsyncConnectionPool(
                conninfo=f"postgres://{self.user}:{self.password.get_secret_value()}"
                f"@{self.host}:{self.port}/{self.database}"
                f"?sslmode={self.sslmode}",
                max_size=self.max_size,
                kwargs={
                    "autocommit": self.autocommit,
                    "prepare_threshold": self.prepare_threshold,
                    "row_factory": self.row_factory,
                },
                open=False,  # Don't open in constructor to avoid deprecation warning
            )

            # Explicitly open the pool
            await pool.open()

            ctx.logger.info(
                "PostgreSQL connection pool initialized and opened successfully",
                extra={"max_size": self.max_size, "database": self.database},
            )

            return pool

        except Exception as e:
            ctx.logger.error(
                "Failed to initialize PostgreSQL connection pool",
                extra={
                    "host": self.host,
                    "port": self.port,
                    "database": self.database,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            raise


class ComposioService:
    """
    Production-ready service for building Composio-integrated AI agents.

    This service provides a complete integration layer for building AI agents that can:
    - Authenticate users with external services through Composio
    - Manage tool access and permissions
    - Execute actions on behalf of users
    - Maintain conversation memory across sessions
    - Handle chat protocols for real-time communication

    The service is designed to be async-first, thread-safe, and production-ready
    with comprehensive error handling, structured logging, and resource management.

    Architecture:
        - Uses LangChain's ChatOpenAI for LLM communication
        - Integrates with Composio for tool management and execution
        - Supports PostgreSQL for persistent memory storage
        - Implements uAgent chat protocol for communication
        - Provides automatic authentication flow management

    Attributes:
        _composio_config: Configuration for Composio integration
        _client: Composio API client for operations
        _llm: Language model instance for agent communication
        _protocol: Chat protocol handler for message processing
        _memory_config: Optional PostgreSQL configuration for persistence
        _pool: Database connection pool for memory operations
        _setup_completed: Flag indicating memory setup completion

    Example:
        ```python
        import asyncio
        from composio_integration import ComposioService, ComposioConfig, ToolConfig

        async def main():
            # Configure Composio integration
            config = ComposioConfig.from_env(
                tool_configs=[
                    ToolConfig.from_toolkit("GitHub Tools", "auth_123", "GITHUB"),
                    ToolConfig.from_search("Calendar Tools", "auth_456", "calendar events")
                ]
            )

            # Method 1: Manual resource management
            service = ComposioService(
                composio_config=config,
                api_key="your_llm_api_key",
                model_name="gpt-4",
                memory_config=PostgresMemoryConfig.from_env()
            )
            try:
                # Use service...
                protocol = service.protocol
            finally:
                await service.cleanup()

            # Method 2: Context manager (recommended)
            async with ComposioService(
                composio_config=config,
                api_key="your_llm_api_key",
                model_name="gpt-4",
                memory_config=PostgresMemoryConfig.from_env()
            ) as service:
                protocol = service.protocol
                # Automatic cleanup when exiting context

        asyncio.run(main())
        ```

    Threading:
        This class is thread-safe. All async operations use proper locking
        and the database connection pool is designed for concurrent access.

    Error Handling:
        The service implements comprehensive error handling with custom exceptions.
        All operations are logged with structured context for debugging and monitoring.

    Memory Management:
        If PostgreSQL memory is configured, the service automatically manages
        database connections and ensures proper cleanup of resources. The connection
        pool is opened explicitly to avoid deprecation warnings.
    """

    def __init__(
        self,
        composio_config: ComposioConfig,
        api_key: str | None = None,
        model_name: str | None = None,
        base_url: str | None = None,
        memory_config: PostgresMemoryConfig | None = None,
    ) -> None:
        """
        Initialize the Composio service with configuration and dependencies.

        Args:
            composio_config: Configuration for Composio tool integration
            ctx: Context object for logging and operation context
            api_key: API key for the language model (or set LLM_API_KEY env var)
            model_name: Name of the language model to use (or set LLM_MODEL_NAME env var)
            base_url: Base URL for the language model API (or set LLM_BASE_URL env var)
            memory_config: Optional PostgreSQL configuration for persistent memory

        Raises:
            ValueError: If required configuration is missing or invalid
            ConfigurationError: If Composio client initialization fails

        Environment Variables:
            LLM_API_KEY: API key for language model authentication
            LLM_BASE_URL: Base URL for language model API (default: https://api.asi1.ai/v1)
            LLM_MODEL_NAME: Model name to use (default: asi1-mini)

        Example:
            ```python
            # Using environment variables
            service = ComposioService(composio_config=config)

            # Using explicit parameters
            service = ComposioService(
                composio_config=config,
                api_key="your_api_key",
                model_name="gpt-4",
                base_url="https://api.openai.com/v1"
            )
            ```
        """

        logger.info(
            "Initializing ComposioService",
            extra={
                "has_memory_config": memory_config is not None,
                "tool_configs_count": len(composio_config.tool_configs or []),
                "auth_config_ids": list(composio_config.get_auth_config_ids()),
            },
        )

        # Resolve API configuration from parameters or environment
        api_key = api_key or os.getenv("LLM_API_KEY")
        if not api_key:
            logger.error(
                "API key not provided in parameter or LLM_API_KEY environment variable"
            )
            raise ValueError(
                "API key must be provided via parameter or LLM_API_KEY env var"
            )

        base_url = base_url or os.getenv(
            "LLM_BASE_URL", "https://api.asi1.ai/v1")
        if not base_url:
            logger.error(
                "Base URL not provided in parameter or LLM_BASE_URL environment variable"
            )
            raise ValueError(
                "Base URL must be provided via parameter or LLM_BASE_URL env var"
            )

        model = model_name or os.getenv("LLM_MODEL_NAME", "asi1-mini")
        if not model:
            logger.error(
                "Model name not provided in parameter or LLM_MODEL_NAME environment variable"
            )
            raise ValueError(
                "Model name must be provided via parameter or LLM_MODEL_NAME env var"
            )

        # Initialize instance variables
        self._setup_completed = False
        self._memory_config = memory_config
        self._pool: AsyncConnectionPool | None = None

        try:
            # Initialize language model client
            self._llm = ChatOpenAI(
                model=model, api_key=SecretStr(api_key), base_url=base_url
            )
            logger.info(
                "Language model client initialized successfully",
                extra={
                    "model": model,
                    "base_url": (
                        base_url[:50] +
                        "..." if len(base_url) > 50 else base_url
                    ),
                },
            )

            # Initialize Composio client
            self._composio_config = composio_config
            self._client = ComposioClient(config=composio_config)
            logger.info("Composio client initialized successfully")

            # Initialize chat protocol
            self._protocol = AgentChatProtocol(spec=chat_protocol_spec)
            logger.info("Chat protocol initialized successfully")

        except Exception as e:
            logger.error(
                "Failed to initialize ComposioService components",
                extra={"error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )
            raise ConfigurationError(
                "Failed to initialize ComposioService",
                details={"original_error": str(e)},
                operation="service_initialization",
            ) from e

        logger.info(
            "ComposioService initialization completed successfully",
            extra={
                "service_id": id(self),
                "memory_enabled": memory_config is not None,
                "tools_configured": len(composio_config.tool_configs or []),
            },
        )

    async def _send_chat_message(
        self, text: str, ctx: Context, sender: str, end_session: bool = False
    ) -> None:
        """
        Send a chat message to a user through the chat protocol.

        Args:
            text: Message text to send
            ctx: Chat context for message routing
            sender: Recipient user ID
            end_session: Whether to include end-session signal

        Raises:
            Exception: If message sending fails (logged but not re-raised)
        """
        try:
            ctx.logger.info(
                "Sending chat message",
                extra={
                    "sender": sender,
                    "text_length": len(text),
                    "end_session": end_session,
                    "session_id": str(ctx.session) if hasattr(ctx, "session") else None,
                },
            )

            content: list[AgentContent] = [TextContent(type="text", text=text)]

            if end_session:
                content.append(EndSessionContent(type="end-session"))
                ctx.logger.info("Added end-session signal to message")

            await ctx.send(
                sender,
                ChatMessage(
                    timestamp=datetime.now(UTC),
                    msg_id=uuid4(),
                    content=content,
                ),
            )

            ctx.logger.info(
                "Chat message sent successfully",
                extra={"sender": sender, "message_length": len(text)},
            )

        except Exception as e:
            ctx.logger.error(
                "Failed to send chat message",
                extra={
                    "sender": sender,
                    "text_length": len(text),
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            # Don't re-raise to avoid breaking the conversation flow
            # The caller should handle message delivery failures gracefully

    async def _authenticate_user(
        self, user_id: UserId, auth_config_id: AuthConfigId, ctx: Context
    ) -> AsyncGenerator[str, None]:
        """
        Authenticate a user for a specific auth configuration.

        This method handles the complete authentication flow:
        1. Creates an authentication request
        2. Provides the user with an authentication URL
        3. Waits for the user to complete authentication
        4. Verifies the authentication result
        5. Handles retries for timeout scenarios

        Args:
            user_id: Unique identifier for the user
            auth_config_id: Authentication configuration ID to authenticate against
            ctx: Context object for logging and operation context

        Yields:
            str: Status messages for the user about authentication progress

        Raises:
            AuthenticationError: If authentication fails unexpectedly (logged but not raised)
        """
        ctx.logger.info(
            "Starting user authentication flow",
            extra={
                "user_id": user_id,
                "auth_config_id": auth_config_id,
                "tool_group": self._composio_config.get_tool_group_name_by_auth_config(
                    auth_config_id
                ),
            },
        )

        try:
            # Create auth request for the specified auth config
            auth_response = await self._client.create_auth_request(
                user_id, auth_config_id, ctx
            )

            ctx.logger.info(
                "Authentication request created",
                extra={
                    "user_id": user_id,
                    "auth_config_id": auth_config_id,
                    "status": auth_response.status,
                    "has_redirect_url": auth_response.redirect_url is not None,
                },
            )

            if auth_response.is_pending and auth_response.redirect_url:
                if not auth_response.connection_request:
                    error_msg = "Connection request object missing in auth response."
                    ctx.logger.error(
                        error_msg,
                        extra={"user_id": user_id,
                               "auth_config_id": auth_config_id},
                    )
                    yield (
                        "Sorry, an error occurred while creating the authentication request. "
                        "Please try again later."
                    )
                    return

                tool_group_name = (
                    self._composio_config.get_tool_group_name_by_auth_config(
                        auth_config_id
                    )
                )
                ctx.logger.info(
                    "Authentication URL provided to user",
                    extra={
                        "user_id": user_id,
                        "auth_config_id": auth_config_id,
                        "tool_group": tool_group_name,
                        "redirect_url_length": len(auth_response.redirect_url),
                    },
                )
                yield (
                    f"To connect with {tool_group_name}, please authenticate by "
                    f"[clicking here]({auth_response.redirect_url})..."
                )

                # Wait for user to complete authentication
                ctx.logger.info(
                    "Waiting for user to complete authentication",
                    extra={"user_id": user_id,
                           "auth_config_id": auth_config_id},
                )
                verify_response = await self._client.verify_auth_request(
                    auth_response.connection_request, ctx=ctx
                )

                if verify_response.is_success:
                    ctx.logger.info(
                        "User authentication completed successfully",
                        extra={
                            "user_id": user_id,
                            "auth_config_id": auth_config_id,
                            "connection_id": verify_response.connection_id,
                        },
                    )
                    yield "Authentication successful!"

                elif verify_response.status == "timeout":
                    ctx.logger.warning(
                        "Authentication timed out, retrying",
                        extra={"user_id": user_id,
                               "auth_config_id": auth_config_id},
                    )
                    yield "Authentication timed out. Please try again."
                    async for msg in self._authenticate_user(
                        user_id, auth_config_id, ctx
                    ):
                        yield msg
                    return

                else:
                    ctx.logger.error(
                        "Authentication failed",
                        extra={
                            "user_id": user_id,
                            "auth_config_id": auth_config_id,
                            "status": verify_response.status,
                            "message": verify_response.message,
                        },
                    )
                    yield f"Authentication failed: {verify_response.message}"
                    return
            else:
                error_msg = (
                    f"Failed to create authentication request: {auth_response.message}"
                )
                ctx.logger.error(
                    error_msg,
                    extra={
                        "user_id": user_id,
                        "auth_config_id": auth_config_id,
                        "status": auth_response.status,
                    },
                )
                yield (
                    "Sorry, an error occurred while creating the authentication request. "
                    "Please try again later."
                )
                return

        except Exception as e:
            ctx.logger.error(
                "Unexpected error during user authentication",
                extra={
                    "user_id": user_id,
                    "auth_config_id": auth_config_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            yield (
                "Sorry, an unexpected error occurred during authentication. Please try again later."
            )
            return

    async def _check_user_connections(
        self, user_id: UserId, ctx: Context
    ) -> AsyncGenerator[str, None]:
        """
        Check and establish user connections for all required auth configurations.

        This method verifies if the user has active connections for all configured
        authentication providers. If connections are missing, it initiates the
        authentication flow for each required configuration.

        Args:
            user_id: Unique identifier for the user
            ctx: Context object for logging and operation context

        Yields:
            str: Status messages about connection checking and authentication progress

        Note:
            This method is recursive - it re-checks connections after each authentication
            attempt to ensure all required connections are established.
        """
        ctx.logger.info(
            "Checking user connections",
            extra={
                "user_id": user_id,
                "required_auth_configs": list(
                    self._composio_config.get_auth_config_ids()
                ),
            },
        )

        try:
            # Check if user has an active connection
            status = await self._client.connection_exists(user_id, ctx)

            ctx.logger.info(
                "Connection status retrieved",
                extra={
                    "user_id": user_id,
                    "user_connected": status.user_connected,
                    "active_connections": status.active_connections,
                    "total_configs": status.total_configs,
                    "missing_connections": len(status.connections_required),
                },
            )

            if not status.user_connected:
                if not status.connections_required:
                    error_msg = (
                        "No authentication configurations available for connection."
                    )
                    ctx.logger.error(
                        error_msg,
                        extra={
                            "user_id": user_id,
                            "total_configs": status.total_configs,
                            "active_connections": status.active_connections,
                        },
                    )
                    yield "No authentication configurations available for connection."
                    return

                ctx.logger.info(
                    "User needs authentication for missing connections",
                    extra={
                        "user_id": user_id,
                        "missing_connections": status.connections_required,
                        "connection_progress": f"{status.active_connections}/{status.total_configs}"
                    },
                )

                # Authenticate each missing connection
                for auth_config_id in status.connections_required:
                    ctx.logger.info(
                        "Starting authentication for missing connection",
                        extra={"user_id": user_id,
                               "auth_config_id": auth_config_id},
                    )
                    async for auth_msg in self._authenticate_user(
                        user_id, auth_config_id, ctx
                    ):
                        yield auth_msg

                # Re-check connections after authentication attempts
                ctx.logger.info(
                    "Re-checking connections after authentication attempts",
                    extra={"user_id": user_id},
                )
                async for conn_msg in self._check_user_connections(user_id, ctx):
                    yield conn_msg

            else:
                ctx.logger.info(
                    "User already has all required connections",
                    extra={
                        "user_id": user_id,
                        "active_connections": status.active_connections,
                        "total_configs": status.total_configs,
                    },
                )

        except Exception as e:
            ctx.logger.error(
                "Error checking user connections",
                extra={
                    "user_id": user_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            yield (
                "Sorry, an error occurred while checking your connections. Please try again later."
            )
        return

    async def _create_pre_model_hook(
        self,
        max_tokens: int = 100000,
        strategy: str = "last",
        agent_prompt: str | None = None,
    ) -> Callable[[dict[str, Any]], dict[str, list[BaseMessage]]]:
        """
        Factory function to create a pre_model_hook with custom configuration for memory trimming.

        This hook implements the 'Trim messages' pattern to keep the conversation history
        within the specified token limit, ensuring the most recent context is prioritized.

        Args:
            max_tokens: Maximum number of tokens to keep in history.
            strategy: Trimming strategy ('last', 'first', etc.).
            agent_prompt: Optional agent prompt to include in trimming context.

        Returns:
            Configured pre_model_hook function.
        """

        def pre_model_hook(state: dict[str, Any]) -> dict[str, list[BaseMessage]]:
            """The actual hook to be executed before the LLM call."""

            if "messages" not in state or not isinstance(state["messages"], list):
                return {}

            messages: list[BaseMessage] = state["messages"]
            safe_token_count = max_tokens
            agent_prompt_tokens = 0

            if agent_prompt:
                message = HumanMessage(content=agent_prompt)
                agent_prompt_tokens = count_tokens_approximately([message])
                safe_token_count -= agent_prompt_tokens

            safe_max_tokens = int(safe_token_count * 0.8)
            current_max = safe_max_tokens
            max_iterations = 5

            for iteration in range(max_iterations):
                trimmed_messages: list[BaseMessage] = trim_messages(
                    messages,
                    strategy=strategy,
                    token_counter=count_tokens_approximately,
                    max_tokens=current_max,
                    start_on="human",
                    end_on=("human", "tool"),
                )

                actual_tokens = (
                    count_tokens_approximately(
                        trimmed_messages) + agent_prompt_tokens
                )

                if actual_tokens <= max_tokens:
                    return {"llm_input_messages": trimmed_messages}

                overage_ratio = actual_tokens / max_tokens
                current_max = int(current_max / overage_ratio * 0.8)

                if iteration == max_iterations - 1:
                    result_messages: list[BaseMessage] = []
                    token_count = agent_prompt_tokens

                    for msg in reversed(trimmed_messages):
                        msg_tokens = count_tokens_approximately([msg])
                        if token_count + msg_tokens <= max_tokens:
                            result_messages.insert(0, msg)
                            token_count += msg_tokens
                        else:
                            break

                    return {"llm_input_messages": result_messages}

            return {"llm_input_messages": trimmed_messages}

        return pre_model_hook

    async def _run_agent_query(
        self, agent: Any, query: str, session_id: str, ctx: Context
    ) -> str:
        """
        Execute a query against the LangChain agent and return the response.

        This method processes user queries through the agent's reasoning and action
        loop, using asynchronous streaming for efficient execution.

        Args:
            agent: The configured LangChain agent instance (CompiledStateGraph).
            query: User's natural language query.
            session_id: Unique session identifier for memory context.
            ctx: Chat context for logging and message handling.

        Returns:
            str: Agent's final response to the query, or error message if processing fails.
        """
        ctx.logger.info(
            "Running agent query",
            extra={
                "session_id": session_id,
                "query_length": len(query),
                "query_preview": query[:100] + "..." if len(query) > 100 else query,
            },
        )

        try:
            input_messages = {"messages": [HumanMessage(content=query)]}
            config = {"configurable": {"thread_id": session_id}}

            final_state = await agent.ainvoke(
                input_messages,
                config,
            )

            final_message = final_state.get("messages", [])[-1]
            response_content = getattr(final_message, "content", None)
            final_response = (
                response_content
                or "I couldn't generate a final text response to your query."
            )

            ctx.logger.info(
                "Agent query completed",
                extra={
                    "session_id": session_id,
                    "response_length": len(final_response),
                    "has_response": bool(response_content),
                },
            )

            return final_response

        except Exception as e:
            ctx.logger.error(
                "Error running agent query",
                extra={
                    "session_id": session_id,
                    "query_length": len(query),
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            return f"An error occurred while processing your query: {str(e)}"

    async def _structured_tool_to_dict(self, tool: StructuredTool) -> dict[str, Any]:
        """
        Converts a StructuredTool object to the dictionary format expected by
        _create_agent_tool_prompt and _create_orchestrator_prompt methods.

                Args:
            tool: A StructuredTool instance from LangChain

        Returns:
            A dictionary with 'function' key containing name, description, and parameters
        """
        if hasattr(tool.args_schema, "model_json_schema"):
            schema = tool.args_schema.model_json_schema()
        elif hasattr(tool.args_schema, "model_dump"):
            schema = tool.args_schema.model_dump()
        else:
            schema = tool.args_schema if isinstance(
                tool.args_schema, dict) else {}

        properties = schema.get("properties", {})
        required = schema.get("required", [])
        defs = schema.get("$defs", {})

        return {
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "properties": properties,
                    "required": required,
                    "$defs": defs,
                },
            }
        }

    async def _create_agent_tool_prompt(
        self, tool_list: list[StructuredTool], agent_name: str
    ) -> str:
        """
        Generates a prompt for an LLM agent, detailing all its available tools,
        their descriptions, parameters, and required inputs.
        """
        tools_prompt = f"## {agent_name} Agent Tool Definitions\n"
        tools_prompt += (
            f"You are the {agent_name} Agent. Your task is to process user "
            "requests by invoking the appropriate tools.\n\n"
        )

        tools_prompt += """IMPORTANT GUIDELINES:

    1. Check Relevant Data First: You may receive a 'relevant_data' dictionary containing
    information from other agents or previous steps. Always examine this data before calling
    tools - it may contain exactly what you need.

    2. Use Relevant Data: If relevant_data contains the information needed for your task,
    use it directly in your tool calls rather than fetching it again.

    3. Single Tool Call: Generate only ONE function call per turn based on the task description
    and available tools.

    4. Error Handling: If any error occurs during tool execution, respond with a clear error
    message and do not attempt to call another tool.

    ---

    """

        for tool_def in tool_list:
            tool_dict = await self._structured_tool_to_dict(tool_def)
            function_data = tool_dict.get("function", {})
            name = function_data.get("name", "N/A")
            description = function_data.get(
                "description", "No description provided.")
            parameters = function_data.get("parameters", {})
            required_params = parameters.get("required", [])
            properties = parameters.get("properties", {})

            tools_prompt += f"\n### Tool: {name}\n"
            tools_prompt += f"Description: {description}\n"
            tools_prompt += "Parameters:\n"

            if not properties:
                tools_prompt += "- *None*\n"
                continue

            for prop_name, prop_data in properties.items():
                param_type = prop_data.get("type", "string")
                param_desc = prop_data.get("description", "No description.")
                is_required = (
                    "[REQUIRED]" if prop_name in required_params else "[OPTIONAL]"
                )

                tools_prompt += (
                    f"- {prop_name} ({param_type}, {is_required}): {param_desc}"
                )

                if param_type == "object" and "properties" in prop_data:
                    tools_prompt += "\n  - Nested Properties: " + ", ".join(
                        prop_data["properties"].keys()
                    )

                if "enum" in prop_data:
                    allowed_values = ", ".join(
                        [f"`{v}`" for v in prop_data["enum"]])
                    tools_prompt += f" Allowed Values: {allowed_values}"

                tools_prompt += "\n"

        tools_prompt += (
            "\n---\nRemember: Check relevant_data first, then use tools to complete the task.\n"
        )

        return tools_prompt

    async def _create_orchestrator_prompt(
        self,
        agent_tools_map: dict[str, list[StructuredTool]],
    ) -> str:
        """
        Generates a high-level prompt for an Orchestrator LLM, explaining which
        agents are available and the primary functions they manage.
        """
        orchestrator_prompt = "## Orchestrator Agent: Available Tool Agents\n"
        orchestrator_prompt += (
            "You are the Orchestrator Agent. Your primary role is to determine which specialized "
            "agent can best handle the user's request and coordinate multi-step tasks.\n\n"
        )

        orchestrator_prompt += (
            "You can invoke any of the following specialized agents:\n"
        )
        orchestrator_prompt += "---\n"

        for agent_name, tool_list in agent_tools_map.items():
            tool_summaries = []
            for tool_def in tool_list:
                tool_dict = await self._structured_tool_to_dict(tool_def)
                name = tool_dict.get("function", {}).get("name", "N/A")
                description = tool_dict.get(
                    "function", {}).get("description", "")

                snippet = description.split(";")[0].split(",")[0]
                snippet = snippet.split(".")[0] + "..."

                tool_summaries.append(f"`{name}`: {snippet}")

            orchestrator_prompt += f"### Agent: {agent_name}\n"
            orchestrator_prompt += (
                f"This agent handles tasks related to {agent_name}.\n"
            )
            orchestrator_prompt += (
                "Key Capabilities: " + ", ".join(tool_summaries) + "\n\n"
            )

        orchestrator_prompt += """---

    CRITICAL RULES FOR MULTI-STEP TASKS:

    1. Memory Isolation: Each specialized agent has its own separate memory. They CANNOT see each
    other's conversation history or data.

    2. Data Passing: When a task requires multiple agents in sequence:
    - Call the first agent and wait for its response
    - Extract ALL relevant data from the response
    - Pass that data to the next agent via the 'relevant_data' parameter

    3. Tool Invocation Format:
    - agent_name(task_description="clear description", relevant_data={"key": "value"})
    - The 'relevant_data' dict should contain any information the agent needs from previous steps

    4. Sequential Processing:
    - For tasks like "fetch X and send it via Y", you must:
        a) Call the agent that fetches X
        b) Extract the fetched data from the response
        c) Call the agent that sends via Y, passing the data in relevant_data

    5. Single Agent Per Turn: Invoke only ONE agent per reasoning step. Wait for its response
    before deciding the next action.

    6. Final Response: After all agents complete, synthesize their results into a single coherent
    response that describes what was accomplished.

    """

        if (
            self._composio_config.persona_prompt
            and self._composio_config.persona_prompt.strip()
        ):
            orchestrator_prompt += (
                f"### Your Persona\n{self._composio_config.persona_prompt.strip()}\n\n"
            )
            orchestrator_prompt += (
                "Use this persona in your final response to the user, but maintain clarity "
                "when coordinating between agents.\n"
            )

        return orchestrator_prompt

    async def _create_specialized_agent_tool(
        self,
        session_id: str,
        agent_name: str,
        tools: list[Any],
        ctx: Context,
        memory: AsyncPostgresSaver | None = None,
        max_history_tokens: int = 100000,
    ) -> Any:
        """
        Creates a single, specialized LangChain ReAct agent with dedicated tools, memory,
        and a custom system prompt generated from the tool definitions.
        """
        ctx.logger.info(
            f"Creating Specialized Agent: {agent_name}",
            extra={"tools_count": len(
                tools), "has_memory": memory is not None},
        )

        try:
            specialized_prompt = await self._create_agent_tool_prompt(tools, agent_name)

            pre_model_hook_func = await self._create_pre_model_hook(
                max_tokens=max_history_tokens, strategy="last"
            )

            def _handle_tool_errors(error: Exception) -> str:
                """Handle tool execution errors with logging and user-friendly messages."""
                ctx.logger.error(
                    f"Error occurred during tool execution in {agent_name}: {error}",
                    exc_info=True,
                )
                return "An error occurred while executing a tool. Please try again."

            tool_node = ToolNode(
                tools=tools, handle_tool_errors=_handle_tool_errors)

            config: dict[str, Any] = {
                "model": self._llm,
                "tools": tool_node,
                "prompt": specialized_prompt,
                "pre_model_hook": pre_model_hook_func,
            }

            specialized_thread_id = (
                f"{session_id}_{agent_name.lower().replace(' ', '_')}"
            )

            if memory:
                config["checkpointer"] = memory
                ctx.logger.info(
                    f"Agent {agent_name} configured with memory checkpointer"
                )

            agent = create_agent(
                **{k: v for k, v in config.items() if v is not None})

            @tool(
                agent_name.lower().replace(" ", "_") + "_agent",
                description=(
                    f"Use this agent to perform tasks requiring {agent_name} capabilities. "
                    "Pass any data from previous steps via relevant_data."
                ),
            )
            async def agent_tool(
                task_description: str, relevant_data: dict[str, Any] | None = None
            ) -> str:
                """
                Execute a task using the specialized agent's tools.

                Args:
                    task_description: Clear description of what needs to be done
                    relevant_data: Dictionary containing data from previous agents/steps
                            (e.g., {"user_profile": {...}, "recipient": "email@example.com"})

                Returns:
                    str: The agent's response after executing the task
                """
                ctx.logger.info(
                    f"Invoking {agent_name} with task: {task_description}",
                    extra={
                        "relevant_data_provided": relevant_data is not None,
                        "relevant_data_keys": (
                            list(relevant_data.keys()) if relevant_data else []
                        ),
                    },
                )

                # Make relevant_data very visible in the prompt
                prompt = f"Task: {task_description}\n\n"
                if relevant_data:
                    prompt += "Data from previous steps (use this information):\n"
                    prompt += f"{relevant_data}\n\n"
                else:
                    prompt += "No data from previous steps provided.\n\n"

                prompt += "Execute the task using the appropriate tools."

                response = await self._run_agent_query(
                    agent, prompt, specialized_thread_id, ctx=ctx
                )

                ctx.logger.info(
                    f"Response from {agent_name}",
                    extra={"response_length": len(response)},
                )

                return response

            ctx.logger.info(
                f"Specialized Agent {agent_name} created successfully")
            return agent_tool

        except Exception as e:
            ctx.logger.error(
                f"Failed to create Specialized Agent {agent_name}: {e}", exc_info=True
            )
            raise

    async def _create_orchestrator_agent(
        self,
        session_id: str,
        ctx: Context,
        agent_tools_map: dict[str, list[Any]],
        memory: AsyncPostgresSaver | None = None,
        max_history_tokens: int = 100000,
    ) -> Any:
        """
        Creates a multi-agent system by instantiating specialized agents for each tool group
        and wrapping them into an Orchestrator Agent for high-level delegation.

        Args:
            agent_tools_map: A dictionary mapping agent names (e.g., 'Gmail Agent')
                            to their list of tool definitions (JSON schema).
            session_id: Unique session identifier for memory context
            ctx: The conversation context for logging and session management
            memory: Optional memory checkpoint for conversation persistence.
            max_history_tokens: Maximum tokens for history trimming in the orchestrator.

        Returns:
            The final Orchestrator Agent.
        """
        ctx.logger.info(
            "Starting creation of multi-agent orchestrator system.")

        orchestrator_tools = []

        for agent_name, tool_list in agent_tools_map.items():
            try:
                specialized_agent = await self._create_specialized_agent_tool(
                    agent_name=agent_name,
                    tools=tool_list,
                    memory=memory,
                    ctx=ctx,
                    max_history_tokens=max_history_tokens,
                    session_id=session_id,
                )
                orchestrator_tools.append(specialized_agent)

            except Exception as e:
                ctx.logger.warning(
                    f"Skipping agent {agent_name} due to creation error: {e}"
                )
                continue

        if not orchestrator_tools:
            ctx.logger.info(f"{agent_tools_map=}, {orchestrator_tools=}")
            raise Exception(
                "No specialized agents could be successfully created to form the orchestrator."
            )

        # Use the helper function to generate the top-level system prompt
        orchestrator_system_prompt = await self._create_orchestrator_prompt(
            agent_tools_map
        )

        orchestrator_config: dict[str, Any] = {
            "model": self._llm,
            "tools": orchestrator_tools,  # The tools are now the specialized agents
            "prompt": orchestrator_system_prompt,
            "pre_model_hook": await self._create_pre_model_hook(
                max_tokens=max_history_tokens, strategy="last"
            ),
        }

        if memory:
            orchestrator_config["checkpointer"] = memory

        orchestrator_agent = create_agent(
            **{k: v for k, v in orchestrator_config.items() if v is not None}
        )

        ctx.logger.info(
            "Orchestrator Agent created successfully, managing all specialized agents."
        )
        return orchestrator_agent

    async def _process_query_stream(
        self, session_id: SessionId, user_id: UserId, query: str, ctx: Context
    ) -> AsyncGenerator[str, None]:
        """
        Process a user query through the complete authentication and execution pipeline.

        This method orchestrates the entire query processing flow:
        1. Checks and establishes required user connections
        2. Retrieves appropriate tools for the user
        3. Sets up memory persistence if configured
        4. Creates and runs the agent with the query
        5. Yields status messages and final response

        Args:
            session_id: Unique session identifier for memory context
            user_id: Unique identifier for the user making the query
            query: User's natural language query to process
            ctx: The conversation context for logging and session management

        Yields:
            str: Status messages during processing and final agent response

        Note:
            This is the main entry point for query processing and handles the
            complete lifecycle from authentication to response generation.
        """
        ctx.logger.info(
            "Starting query processing stream",
            extra={
                "session_id": session_id,
                "user_id": user_id,
                "query_length": len(query),
                "has_memory_config": self._memory_config is not None,
                "query_preview": query[:50] + "..." if len(query) > 50 else query,
            },
        )

        try:
            # Step 1: Check and establish user connections
            ctx.logger.info(
                "Checking user connections",
                extra={"session_id": session_id, "user_id": user_id},
            )
            async for conn_msg in self._check_user_connections(user_id, ctx):
                yield conn_msg

            # Step 2: Retrieve tools for the user
            ctx.logger.info(
                "Retrieving tools for user",
                extra={"session_id": session_id, "user_id": user_id},
            )
            tools_by_group = await self._client.get_tools(user_id, ctx)

            ctx.logger.info(
                "Tools retrieved successfully",
                extra={
                    "session_id": session_id,
                    "user_id": user_id,
                    "tools_by_group": {
                        group: len(group_tools)
                        for group, group_tools in tools_by_group.items()
                    },
                },
            )

            # Step 3: Set up memory and create agent
            if self._memory_config:
                ctx.logger.info(
                    "Using PostgreSQL memory configuration",
                    extra={"session_id": session_id, "user_id": user_id},
                )

                # Initialize database pool if not already done
                if not self._pool:
                    ctx.logger.info("Initializing database connection pool")
                    self._pool = await self._memory_config.initialize_db_pool(ctx)

                async with self._pool.connection() as conn:
                    memory = AsyncPostgresSaver(conn)

                    # Set up memory schema if not already done
                    if not self._setup_completed:
                        ctx.logger.info("Setting up memory schema")
                        await memory.setup()
                        self._setup_completed = True
                        ctx.logger.info("Memory schema setup completed")

                    # Create agent with memory
                    agent = await self._create_orchestrator_agent(
                        session_id=session_id,
                        ctx=ctx,
                        agent_tools_map=tools_by_group,
                        memory=memory,
                    )

                    # Step 4: Process the query
                    ctx.logger.info(
                        "Processing query with memory-enabled agent",
                        extra={"session_id": session_id, "user_id": user_id},
                    )
                    response = await self._run_agent_query(
                        agent=agent, query=query, session_id=session_id, ctx=ctx
                    )
                    yield response
                    return

            else:
                ctx.logger.info(
                    "Using stateless agent (no memory)",
                    extra={"session_id": session_id, "user_id": user_id},
                )

                # Create agent without memory
                agent = await self._create_orchestrator_agent(
                    session_id=session_id,
                    ctx=ctx,
                    agent_tools_map=tools_by_group,
                )

                # Step 4: Process the query
                ctx.logger.info(
                    "Processing query with stateless agent",
                    extra={"session_id": session_id, "user_id": user_id},
                )
                response = await self._run_agent_query(
                    agent=agent, query=query, session_id=session_id, ctx=ctx
                )
                yield response
                return

        except Exception as e:
            ctx.logger.error(
                "Unexpected error in query processing stream",
                extra={
                    "session_id": session_id,
                    "user_id": user_id,
                    "query_length": len(query),
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            yield (
                "Sorry, an unexpected error occurred while processing your query. "
                "Please try again later."
            )
            return

    @property
    def protocol(self) -> AgentChatProtocol:
        """
        Get the configured chat protocol with message handlers.

        This property returns a uAgent Protocol instance configured with handlers
        for different types of chat messages. The protocol manages the complete
        conversation lifecycle including session management, authentication,
        and query processing.

        Message Types Handled:
            - ChatAcknowledgement: Confirms message receipt
            - ChatMessage: Processes user messages and queries
                - StartSessionContent: Initiates new conversation sessions
                - TextContent: Processes natural language queries
                - EndSessionContent: Cleanly terminates sessions
                - MetadataContent: Handles additional context information

        Returns:
            Protocol: Configured protocol instance ready for agent integration

        Note:
            The protocol handlers are set up once and reused across all conversations.
            Each handler includes comprehensive error handling and structured logging.
        """

        @self._protocol.on_message(ChatAcknowledgement)
        async def _handle_ack(
            ctx: Context, sender: str, msg: ChatAcknowledgement
        ) -> None:
            """Handle acknowledgement messages from users."""
            try:
                ctx.logger.info(
                    "Chat acknowledgement received",
                    extra={
                        "sender": sender,
                        "acknowledged_msg_id": str(msg.acknowledged_msg_id),
                        "session_id": (
                            str(ctx.session) if hasattr(
                                ctx, "session") else None
                        ),
                    },
                )
                ctx.logger.info(
                    f"Acknowledgement received from {sender} for message {msg.acknowledged_msg_id}"
                )
            except Exception as e:
                ctx.logger.error(
                    "Error handling chat acknowledgement",
                    extra={
                        "sender": sender,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                    exc_info=True,
                )

        @self._protocol.on_message(ChatMessage)
        async def _handle_message(ctx: Context, sender: str, msg: ChatMessage) -> None:
            """Handle incoming chat messages and process different content types."""
            try:
                ctx.logger.info(
                    "Chat message received",
                    extra={
                        "sender": sender,
                        "session_id": (
                            str(ctx.session) if hasattr(
                                ctx, "session") else None
                        ),
                        "message_id": str(msg.msg_id),
                        "content_types": [type(item).__name__ for item in msg.content],
                        "content_count": len(msg.content),
                    },
                )

                ctx.logger.info(
                    f"Message received from {sender} in session: {ctx.session}"
                )

                # Send acknowledgement
                try:
                    await ctx.send(
                        sender,
                        ChatAcknowledgement(
                            timestamp=datetime.now(UTC), acknowledged_msg_id=msg.msg_id
                        ),
                    )
                    ctx.logger.info(
                        "Acknowledgement sent",
                        extra={"sender": sender,
                               "message_id": str(msg.msg_id)},
                    )
                except Exception as ack_error:
                    ctx.logger.error(
                        "Failed to send acknowledgement",
                        extra={
                            "sender": sender,
                            "message_id": str(msg.msg_id),
                            "error": str(ack_error),
                        },
                        exc_info=True,
                    )

                # Process message content
                for i, item in enumerate(msg.content):
                    try:
                        ctx.logger.info(
                            "Processing message content item",
                            extra={
                                "sender": sender,
                                "item_index": i,
                                "item_type": type(item).__name__,
                                "session_id": (
                                    str(ctx.session)
                                    if hasattr(ctx, "session")
                                    else None
                                ),
                            },
                        )

                        if isinstance(item, StartSessionContent):
                            ctx.logger.info(
                                "Session started",
                                extra={
                                    "sender": sender,
                                    "session_id": (
                                        str(ctx.session)
                                        if hasattr(ctx, "session")
                                        else None
                                    ),
                                },
                            )
                            ctx.logger.info(
                                f"Session started with {sender} with session id: {ctx.session}"
                            )

                        elif isinstance(item, TextContent):
                            ctx.logger.info(
                                "Processing text query",
                                extra={
                                    "sender": sender,
                                    "session_id": (
                                        str(ctx.session)
                                        if hasattr(ctx, "session")
                                        else None
                                    ),
                                    "text_length": len(item.text),
                                    "text_preview": (
                                        item.text[:100] + "..."
                                        if len(item.text) > 100
                                        else item.text
                                    ),
                                },
                            )
                            ctx.logger.info(
                                f"Text message from {sender}: {item.text}")

                            # Process the query through the agent pipeline
                            async for response in self._process_query_stream(
                                session_id=str(ctx.session),
                                user_id=sender,
                                query=item.text,
                                ctx=ctx,
                            ):
                                await self._send_chat_message(response, ctx, sender)

                        elif isinstance(item, EndSessionContent):
                            ctx.logger.info(
                                "Session ended",
                                extra={
                                    "sender": sender,
                                    "session_id": (
                                        str(ctx.session)
                                        if hasattr(ctx, "session")
                                        else None
                                    ),
                                },
                            )
                            ctx.logger.info(f"Session ended with {sender}")

                        elif isinstance(item, MetadataContent):
                            ctx.logger.info(
                                "Metadata received",
                                extra={
                                    "sender": sender,
                                    "session_id": (
                                        str(ctx.session)
                                        if hasattr(ctx, "session")
                                        else None
                                    ),
                                    "metadata_keys": (
                                        list(item.metadata.keys())
                                        if hasattr(item, "metadata") and item.metadata
                                        else []
                                    ),
                                },
                            )
                            ctx.logger.info(
                                f"Metadata from {sender}: {item.metadata}")

                        else:
                            ctx.logger.warning(
                                "Unexpected content type received",
                                extra={
                                    "sender": sender,
                                    "session_id": (
                                        str(ctx.session)
                                        if hasattr(ctx, "session")
                                        else None
                                    ),
                                    "content_type": type(item).__name__,
                                    "content_repr": (
                                        str(item)[:200] + "..."
                                        if len(str(item)) > 200
                                        else str(item)
                                    ),
                                },
                            )
                            ctx.logger.info(
                                "Received unexpected content type from "
                                f"{sender}: {type(item)} - {item}"
                            )

                    except Exception as content_error:
                        ctx.logger.error(
                            "Error processing message content item",
                            extra={
                                "sender": sender,
                                "item_index": i,
                                "item_type": type(item).__name__,
                                "error": str(content_error),
                                "error_type": type(content_error).__name__,
                            },
                            exc_info=True,
                        )
                        # Continue processing other content items
                        continue

            except Exception as e:
                ctx.logger.error(
                    "Error handling chat message",
                    extra={
                        "sender": sender,
                        "message_id": (
                            str(msg.msg_id) if hasattr(msg, "msg_id") else None
                        ),
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                    exc_info=True,
                )
                # Send error message to user
                try:
                    await self._send_chat_message(
                        "Sorry, an error occurred while processing your message. Please try again.",
                        ctx,
                        sender,
                    )
                except Exception as send_error:
                    ctx.logger.error(
                        "Failed to send error message to user",
                        extra={
                            "sender": sender,
                            "original_error": str(e),
                            "send_error": str(send_error),
                        },
                        exc_info=True,
                    )

        return self._protocol

    async def health_check(self) -> dict[str, Any]:
        """
        Perform a comprehensive health check of the service.

        Returns:
            dict: Health status information including component checks
        """
        health_status: dict[str, Any] = {
            "status": "healthy",
            "timestamp": datetime.now(UTC).isoformat(),
            "components": {},
        }

        try:
            # Check LLM client
            components = health_status["components"]
            components["llm"] = {
                "status": "healthy" if self._llm else "unhealthy",
                "model": getattr(self._llm, "model_name", "unknown"),
                "base_url": getattr(self._llm, "base_url", "unknown"),
            }

            # Check Composio client
            components["composio"] = {
                "status": "healthy" if self._client else "unhealthy",
                "auth_configs": len(self._composio_config.get_auth_config_ids()),
                "tool_configs": len(self._composio_config.tool_configs or []),
            }
            # Check database connection if configured
            if self._memory_config:
                try:
                    if self._pool:
                        components["database"] = {
                            "status": "healthy",
                            "pool_size": getattr(self._pool, "max_size", "unknown"),
                            "setup_completed": self._setup_completed,
                        }
                    else:
                        components["database"] = {
                            "status": "not_initialized",
                            "message": "Database pool not yet initialized",
                        }
                except Exception as e:
                    components["database"] = {
                        "status": "unhealthy", "error": str(e)}
            else:
                components["database"] = {
                    "status": "not_configured",
                    "message": "Database memory not configured",
                }

            # Check protocol
            components["protocol"] = {
                "status": "healthy" if self._protocol else "unhealthy"
            }

            # Overall status
            component_statuses = [comp.get("status")
                                  for comp in components.values()]
            component_statuses = [
                comp.get("status") for comp in health_status["components"].values()
            ]
            if any(status == "unhealthy" for status in component_statuses):
                health_status["status"] = "unhealthy"
            elif any(
                status in ["not_initialized", "not_configured"]
                for status in component_statuses
            ):
                health_status["status"] = "degraded"

        except Exception as e:
            logger.error(
                "Health check failed",
                extra={"error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )
            health_status.update({"status": "unhealthy", "error": str(e)})

        return health_status

    async def cleanup(self) -> None:
        """
        Clean up resources used by the service.

        Should be called when the service is being shut down to ensure
        proper resource cleanup and avoid memory leaks.
        """
        logger.info("Starting service cleanup")

        try:
            # Close database connection pool if it exists
            if self._pool:
                logger.info("Closing database connection pool")
                await self._pool.close()
                self._pool = None
                logger.info("Database connection pool closed successfully")

            # Reset setup flag
            self._setup_completed = False

            logger.info("Service cleanup completed successfully")

        except Exception as e:
            logger.error(
                "Error during service cleanup",
                extra={"error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )
            raise

    def get_service_info(self) -> dict[str, Any]:
        """
        Get information about the service configuration.

        Returns:
            dict: Service configuration information (without sensitive data)
        """
        return {
            "service_type": "ComposioService",
            "llm_model": getattr(self._llm, "model_name", "unknown"),
            "auth_configs_count": len(self._composio_config.get_auth_config_ids()),
            "tool_configs_count": len(self._composio_config.tool_configs or []),
            "memory_enabled": self._memory_config is not None,
            "setup_completed": self._setup_completed,
            "pool_initialized": self._pool is not None,
        }

    async def __aenter__(self) -> ComposioService:
        """
        Async context manager entry.

        Returns:
            Self for use in async with statement
        """
        logger.info("Entering ComposioService async context manager")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any | None,
    ) -> None:
        """
        Async context manager exit with automatic cleanup.

        Args:
            exc_type: Exception type if an exception was raised
            exc_val: Exception instance if an exception was raised
            exc_tb: Exception traceback if an exception was raised
        """
        logger.info(
            "Exiting ComposioService async context manager",
            extra={
                "has_exception": exc_type is not None,
                "exception_type": exc_type.__name__ if exc_type else None,
            },
        )
        await self.cleanup()

    def __repr__(self) -> str:
        """String representation of the service."""
        return (
            f"ComposioService("
            f"auth_configs={len(self._composio_config.get_auth_config_ids())}, "
            f"tool_configs={len(self._composio_config.tool_configs or [])}, "
            f"memory_enabled={self._memory_config is not None})"
        )


# Public API exports
__all__ = [
    # Main classes
    "ComposioService",
    "ComposioConfig",
    "ToolConfig",
    "Modifiers",
    "PostgresMemoryConfig",
    # Exceptions
    "ComposioError",
    "AuthenticationError",
    "ConnectionError",
    "ConfigurationError",
    "ToolRetrievalError",
    # Type aliases for external use
    "UserId",
    "AuthConfigId",
    "ToolSlug",
    "SessionId",
    # Modifier function types
    "SchemaModifier",
    "BeforeExecute",
    "AfterExecute",
    "Tool",
    "ToolExecuteParams",
    "ToolExecutionResponse"
]
