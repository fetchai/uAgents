"""A2A Adapter Tool - Following uagents-adapter pattern."""

import logging
from typing import Any, Dict, List

from pydantic import BaseModel


class A2ARegisterTool(BaseModel):
    """Tool to register a uAgent as an A2A HTTP endpoint."""

    def invoke(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a uAgent as an A2A HTTP endpoint.

        Args:
            params: Dictionary containing:
                - agent_address (str): Required - The uAgent address to bridge to
                - name (str): Optional - Agent name (default: "A2A Agent")
                - description (str): Optional - Agent description
                - host (str): Optional - Host to bind to (default: "localhost")
                - port (int): Optional - Port to bind to (default: 10000)
                - bridge_port (int): Optional - Bridge port (default: auto-derived from port)
                - skill_tags (List[str]): Optional - List of skill tags
                - skill_examples (List[str]): Optional - List of skill examples
                - return_dict (bool): Optional - Return dict instead of string (default: True)

        Returns:
            Dict containing agent details and success status
        """
        try:
            # Extract required parameter
            agent_address = params.get("agent_address")
            if not agent_address:
                raise ValueError("agent_address is required")

            # Extract optional parameters with defaults
            name = params.get("name", "A2A Agent")
            description = params.get(
                "description", "uAgent bridged to A2A HTTP endpoint"
            )
            host = params.get("host", "localhost")
            port = params.get("port", 10000)
            bridge_port = params.get(
                "bridge_port"
            )  # Optional - will auto-derive if None
            skill_tags = params.get("skill_tags", ["general", "assistance"])
            skill_examples = params.get("skill_examples", ["Help me with my query"])
            # return_dict = params.get("return_dict", True)  # Currently unused

            # Ensure skill_tags and skill_examples are lists
            if isinstance(skill_tags, str):
                skill_tags = [tag.strip() for tag in skill_tags.split(",")]
            if isinstance(skill_examples, str):
                skill_examples = [ex.strip() for ex in skill_examples.split(",")]

            # Start the A2A server
            result = self._start_a2a_server(
                agent_address=agent_address,
                name=name,
                description=description,
                host=host,
                port=port,
                bridge_port=bridge_port,
                skill_tags=skill_tags,
                skill_examples=skill_examples,
            )

            # Return the result from _start_a2a_server (already a proper dict)
            return result

        except Exception as e:
            error_msg = f"Failed to start A2A server: {str(e)}"
            return {"success": False, "error": error_msg}

    def _start_a2a_server(
        self,
        agent_address: str,
        name: str,
        description: str,
        host: str,
        port: int,
        bridge_port: int = None,
        skill_tags: List[str] = None,
        skill_examples: List[str] = None,
    ) -> Dict[str, Any]:
        """Start the A2A server with the given parameters."""

        import uvicorn
        from a2a.server.apps import A2AStarletteApplication
        from a2a.server.request_handlers import DefaultRequestHandler
        from a2a.server.tasks import (
            InMemoryPushNotificationConfigStore,
            InMemoryTaskStore,
        )
        from a2a.types import AgentCapabilities, AgentCard, AgentSkill

        from .agentverse_executor import AgentverseAgentExecutor

        try:
            # Create agent capabilities
            capabilities = AgentCapabilities(streaming=True, pushNotifications=True)

            # Create agent skill
            skill = AgentSkill(
                id="agentverse_bridge",
                name=f"{name} Bridge",
                description=description,
                tags=skill_tags,
                examples=skill_examples,
            )

            # Create agent card
            agent_card = AgentCard(
                name=name,
                description=description,
                url=f"http://{host}:{port}/",
                version="1.0.0",
                defaultInputModes=["text", "text/plain"],
                defaultOutputModes=["text", "text/plain"],
                capabilities=capabilities,
                skills=[skill],
            )

            # Handle bridge port - use provided or auto-derive
            if bridge_port is None:
                # Auto-derive bridge port (main_port - 1000) to avoid conflicts
                bridge_port = port - 1000
                # Ensure bridge port is in valid range
                if bridge_port < 1024:
                    bridge_port = port + 1000
                logging.info(f"🔗 Auto-derived bridge port: {bridge_port}")
            else:
                logging.info(f"🔗 Using provided bridge port: {bridge_port}")

            # Create the bridge executor with the target agent address
            bridge_executor = AgentverseAgentExecutor(
                target_agent_address=agent_address,
                bridge_name="a2a_agentverse_bridge",
                bridge_port=bridge_port,
            )

            # Create request handler
            request_handler = DefaultRequestHandler(
                agent_executor=bridge_executor,
                task_store=InMemoryTaskStore(),
                push_config_store=InMemoryPushNotificationConfigStore(),
            )

            # Create and run server
            server = A2AStarletteApplication(
                agent_card=agent_card, http_handler=request_handler
            )

            logging.info(f"🚀 A2A server starting on {host}:{port}")
            logging.info(f"🔗 Bridging to Agentverse agent: {agent_address}")
            logging.info(f"📋 Agent name: {name}")
            logging.info(f"🏷️  Tags: {', '.join(skill_tags)}")

            # Start server in background thread with proper shutdown handling
            # Run server directly in main thread (blocks like CLI)

            try:
                uvicorn.run(server.build(), host=host, port=port)
                return {
                    "success": True,
                    "agent_address": agent_address,
                    "endpoint": f"http://{host}:{port}",
                    "agent_name": name,
                }
            except KeyboardInterrupt:
                logging.info("👋 Server shutting down...")
                return {"success": True, "message": "Server stopped"}
            except Exception as e:
                logging.error(f"Server error: {e}")
                raise

        except Exception as e:
            logging.error(f"Failed to start A2A server: {e}")
            raise
