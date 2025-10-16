"""
uAgents Composio Adapter

A production-ready Composio integration module for LangChain-based AI agents with multi-agent
orchestrator built on uAgents framework.

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
"""

from importlib import metadata

from .adapter import (
    AfterExecute,
    AfterExecuteParam,
    AuthConfigId,
    AuthenticationError,
    AuthResponse,
    BeforeExecute,
    BeforeExecuteParam,
    ComposioConfig,
    ComposioError,
    ComposioService,
    ConfigurationError,
    ConnectionError,
    ConnectionStatus,
    Modifiers,
    PostgresMemoryConfig,
    SchemaModifier,
    SchemaModifierParam,
    SessionId,
    ToolConfig,
    ToolRetrievalError,
    ToolSlug,
    UserId,
)

try:
    __version__ = metadata.version(
        __package__.split(".")[0] if __package__ else "uagents-adapter"
    )
except metadata.PackageNotFoundError:
    # Case where package metadata is not available.
    __version__ = ""
del metadata  # optional, avoids polluting the results of dir(__package__)

__all__ = [
    # Main classes
    "ComposioService",
    "ComposioConfig",
    "ToolConfig",
    "Modifiers",
    "PostgresMemoryConfig",
    # Response models
    "ConnectionStatus",
    "AuthResponse",
    # Exceptions
    "ComposioError",
    "AuthenticationError",
    "ConnectionError",
    "ConfigurationError",
    "ToolRetrievalError",
    # Type aliases
    "UserId",
    "AuthConfigId",
    "ToolSlug",
    "SessionId",
    # Modifier function types
    "SchemaModifier",
    "BeforeExecute",
    "AfterExecute",
    "SchemaModifierParam",
    "BeforeExecuteParam",
    "AfterExecuteParam",
    # Version
    "__version__",
]
