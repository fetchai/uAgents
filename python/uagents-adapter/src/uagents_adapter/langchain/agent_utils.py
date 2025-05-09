"""
Agent utilities for managing Langchain agents in uAgents.
This module provides the AgentManager class for handling async execution of Langchain agents.
"""

import asyncio
import threading
import time
from typing import Any, Callable


class AgentManager:
    """
    A manager class for handling async execution of Langchain agents.

    This class provides utilities for:
    - Creating agent wrappers that handle async execution
    - Starting agents in background threads
    - Managing agent lifecycle
    """

    def __init__(self):
        """Initialize the AgentManager with empty event loop and thread."""
        self._event_loop = None
        self._agent_thread = None

    def create_agent_wrapper(self, agent_func: Callable) -> Callable:
        """
        Creates a wrapper function for the agent that handles async execution.

        Args:
            agent_func: The async function that implements the agent's logic

        Returns:
            A synchronous wrapper function that can be used with uAgents
        """

        def wrapper(query: Any) -> str:
            if isinstance(query, dict) and "input" in query:
                query = query["input"]

            if not self._event_loop:
                return "Error: Agent not initialized"

            future = asyncio.run_coroutine_threadsafe(
                agent_func(query), self._event_loop
            )

            try:
                response = future.result(timeout=15)
                return response
            except Exception as e:
                return f"Error: {str(e)}"

        return wrapper

    def start_agent(self, setup_func: Callable, timeout: int = 10) -> None:
        """
        Starts the agent in a background thread and waits for initialization.

        Args:
            setup_func: The async function that sets up the agent
            timeout: Timeout in seconds for initialization
        """
        self._event_loop = asyncio.new_event_loop()

        # Start the agent in background
        self._agent_thread = threading.Thread(
            target=lambda: self._event_loop.run_until_complete(setup_func()),
            daemon=True,
        )
        self._agent_thread.start()

        # Wait for initialization
        print("Initializing agent...")
        time.sleep(2)  # Give it a moment to start

    def run_forever(self) -> None:
        """Keeps the agent running until interrupted."""
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("🛑 Shutting down...")
            print("✅ Agent stopped.")
