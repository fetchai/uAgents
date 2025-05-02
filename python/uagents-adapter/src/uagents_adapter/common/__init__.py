"""Common functionality and utilities for uAgent adapters."""

import asyncio
import atexit
import os
import socket
from datetime import datetime
from threading import Event, Lock
from typing import Any, Dict, Optional, Type
from uuid import uuid4

import requests
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from uagents import Agent, Model
from uagents_core.contrib.protocols.chat import (
    ChatMessage,
    EndSessionContent,
    TextContent,
)

# Dictionary to keep track of all running uAgents
RUNNING_UAGENTS: Dict[str, Dict[str, Any]] = {}
RUNNING_UAGENTS_LOCK = Lock()

# Event for signaling when an agent is ready
AGENT_READY_EVENT = Event()


# Define message model for responses
class ResponseMessage(Model):
    """Standard response message for uAgents."""

    response: str


# Chat helper functions
def create_text_chat(text: str, end_session: bool = True) -> ChatMessage:
    """Create a text chat message with optional end session marker."""
    content = [TextContent(type="text", text=text)]
    if end_session:
        content.append(EndSessionContent(type="end-session"))
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=content,
    )


# Agent cleanup functions
def cleanup_uagent(agent_name: str) -> bool:
    """Stop a specific uAgent."""
    with RUNNING_UAGENTS_LOCK:
        if agent_name in RUNNING_UAGENTS:
            print(f"Marked agent '{agent_name}' for cleanup")
            del RUNNING_UAGENTS[agent_name]
            return True
    return False


def cleanup_all_uagents() -> None:
    """Stop all uAgents."""
    with RUNNING_UAGENTS_LOCK:
        for agent_name in list(RUNNING_UAGENTS.keys()):
            cleanup_uagent(agent_name)


# Register the cleanup handler
atexit.register(cleanup_all_uagents)


class BaseRegisterToolInput(BaseModel):
    """Base input schema for register tools."""

    name: str = Field(..., description="Name of the agent")
    port: int = Field(
        ..., description="Port to run on (defaults to a random port between 8000-9000)"
    )
    description: str = Field(..., description="Description of the agent")
    api_token: Optional[str] = Field(None, description="API token for agentverse.ai")
    ai_agent_address: Optional[str] = Field(
        None, description="Address of the AI agent to forward messages to"
    )
    mailbox: bool = Field(
        True,
        description="Whether to use mailbox (True) or endpoint (False) for agent configuration",
    )


class BaseRegisterTool(BaseTool):
    """Base class for tools that register agents on Agentverse."""

    name: str = "base_register"
    description: str = "Base class for registering agents on Agentverse"
    args_schema: Type[BaseModel] = BaseRegisterToolInput

    # Track current agent info for easier access
    _current_agent_info: Optional[Dict[str, Any]] = None

    def _find_available_port(
        self,
        preferred_port: Optional[int] = None,
        start_range: int = 8000,
        end_range: int = 9000,
    ) -> int:
        """Find an available port to use for the agent."""
        # Try the preferred port first
        if preferred_port is not None and preferred_port != 0:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("", preferred_port))
                    return preferred_port
            except OSError:
                print(
                    f"Preferred port {preferred_port} is in use, searching for alternative..."
                )

        # Search for an available port in the range
        for port in range(start_range, end_range):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("", port))
                    return port
            except OSError:
                continue

        # If we can't find an available port, raise an exception
        raise RuntimeError(
            f"Could not find an available port in range {start_range}-{end_range}"
        )

    def _create_agent(self, name: str, port: int, mailbox: bool = True) -> Agent:
        """Create a uAgent with consistent configuration."""
        seed = f"uagent_seed_{name}_{port}"

        if mailbox:
            return Agent(name=name, port=port, seed=seed, mailbox=True)
        else:
            return Agent(
                name=name,
                port=port,
                seed=seed,
                endpoint=[f"http://localhost:{port}/submit"],
            )

    def _get_ai_agent_address(self, ai_agent_address: Optional[str] = None) -> str:
        """Get AI agent address with fallback to environment variable."""
        if ai_agent_address:
            return ai_agent_address

        env_address = os.getenv("AI_AGENT_ADDRESS")
        if env_address:
            return env_address

        # Default fallback address
        return "agent1qtlpfshtlcxekgrfcpmv7m9zpajuwu7d5jfyachvpa4u3dkt6k0uwwp2lct"

    async def _start_agent_async(self, uagent: Agent) -> None:
        """Start an agent using asyncio."""
        await uagent.run()

    def _start_uagent_with_asyncio(self, agent_info: Dict[str, Any]) -> None:
        """Start a uAgent using asyncio in its own thread."""
        uagent = agent_info["uagent"]

        # Create and set up a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Start the agent in the loop
        try:
            loop.run_until_complete(self._start_agent_async(uagent))
        except Exception as e:
            print(f"Error running uAgent: {e}")
        finally:
            loop.close()

    def _register_with_agentverse(
        self, agent_info: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Register agent with Agentverse API."""
        # Get API token from agent_info or environment
        api_token = agent_info.get("api_token")
        if not api_token:
            api_token = os.getenv("AGENTVERSE_API_TOKEN")

        if not api_token:
            print("No API token provided for Agentverse registration")
            return None

        # Get agent information
        name = agent_info["name"]
        description = agent_info.get("description", f"Agent: {name}")
        address = agent_info["uagent"].address

        # Set up the API request
        endpoint = "https://agentverse.ai/api/v1/register-agent"
        headers = {"Authorization": f"Bearer {api_token}"}
        data = {
            "name": name,
            "description": description,
            "address": address,
        }

        # Make the API request
        try:
            response = requests.post(endpoint, json=data, headers=headers)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to register agent: {response.text}")
                return None
        except Exception as e:
            print(f"Error registering agent with Agentverse: {e}")
            return None

    def get_agent_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the current agent."""
        return self._current_agent_info

    def _run_base(
        self,
        name: str,
        port: int,
        description: str,
        agent_info: Dict[str, Any],
        api_token: Optional[str] = None,
        return_dict: bool = False,
    ) -> Dict[str, Any] | str:
        """Common run implementation to be used by derived classes."""
        # Reset ready event
        AGENT_READY_EVENT.clear()

        # Add additional information to agent_info
        if description:
            agent_info["description"] = description
        if api_token:
            agent_info["api_token"] = api_token

        # Store in module-level registry and instance variable
        with RUNNING_UAGENTS_LOCK:
            RUNNING_UAGENTS[name] = agent_info
        self._current_agent_info = agent_info

        # Start the agent in a separate thread using asyncio
        import threading

        agent_thread = threading.Thread(
            target=self._start_uagent_with_asyncio,
            args=(agent_info,),
            daemon=True,
        )
        agent_thread.start()

        # Wait for agent to be ready (or timeout)
        AGENT_READY_EVENT.wait(timeout=15)

        # Register with Agentverse if we have an API token
        if api_token and agent_info.get("mailbox", True):
            registration_result = self._register_with_agentverse(agent_info)
            agent_info["registration_result"] = registration_result

        # Return as requested format
        if return_dict:
            return agent_info

        # Format a nice output message
        address = agent_info.get("address", "unknown")
        result = f"Created uAgent '{name}' with address {address} on port {port}"

        if agent_info.get("registration_result"):
            result += "\nRegistered with Agentverse successfully"

        return result

    async def _arun(
        self,
        name: str,
        port: int,
        description: str,
        api_token: Optional[str] = None,
        ai_agent_address: Optional[str] = None,
        mailbox: bool = True,
        *,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Async implementation to be overridden by subclasses."""
        raise NotImplementedError("Subclasses must implement this method")
