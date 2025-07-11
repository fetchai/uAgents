import logging
import os
import sys
import urllib.parse

import click
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryPushNotificationConfigStore, InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Route

# Import the generic agent executor
from .agentverse_executor import AgentverseAgentExecutor

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option("--host", "host", default="localhost", help="Host to bind the server to")
@click.option("--port", "port", default=10000, help="Port to bind the server to")
@click.option(
    "--agent-address",
    "agent_address",
    required=True,
    help="Agentverse agent address to bridge to",
)
@click.option(
    "--agent-name",
    "agent_name",
    default="Agentverse Agent",
    help="Name for the A2A agent",
)
@click.option(
    "--agent-description",
    "agent_description",
    default="Agent bridged from Agentverse",
    help="Description for the A2A agent",
)
@click.option(
    "--skill-tags",
    "skill_tags",
    default="general,assistance",
    help="Comma-separated skill tags",
)
@click.option(
    "--skill-examples",
    "skill_examples",
    default="Help me with my query",
    help="Comma-separated skill examples",
)
@click.option(
    "--bridge-port",
    "bridge_port",
    default=None,
    help="Port for the internal uAgent bridge (auto-derived if not specified)",
)
@click.option(
    "--bridge-seed",
    "bridge_seed",
    default=None,
    help="Seed for bridge agent (overrides UAGENTS_BRIDGE_SEED env var)",
)
def main(
    host,
    port,
    agent_address,
    agent_name,
    agent_description,
    skill_tags,
    skill_examples,
    bridge_port,
    bridge_seed,
):
    """Starts the Agentverse Bridge A2A server.

    SECURITY NOTE: Set UAGENTS_BRIDGE_SEED environment variable for consistent
    bridge agent addresses across restarts. Without this, a random seed will be
    generated on each startup.

    Example:
        export UAGENTS_BRIDGE_SEED="your_unique_secure_seed_here"
        python -m uagents_adapter.a2a_inbound.cli --agent-address agent1...
    """
    try:
        logger.info(f"Starting A2A server bridged to Agentverse agent: {agent_address}")

        # Auto-derive bridge port if not specified (main_port - 1000)
        # This ensures each A2A server gets a unique bridge port
        if bridge_port is None:
            bridge_port = port - 1000
            # Ensure bridge port is in valid range
            if bridge_port < 1024:
                bridge_port = port + 1000

        logger.info(f"Using bridge port: {bridge_port}")

        # Handle bridge seed (CLI option overrides environment)
        if bridge_seed:
            os.environ["UAGENTS_BRIDGE_SEED"] = bridge_seed
            logger.info("🔐 Using bridge seed from CLI option")
        elif not os.getenv("UAGENTS_BRIDGE_SEED") and not os.getenv("A2A_BRIDGE_SEED"):
            logger.warning(
                "⚠️  No bridge seed provided - address will be random on each restart"
            )
            logger.warning(
                "⚠️  Consider setting: export UAGENTS_BRIDGE_SEED='your_seed'"
            )

        # Parse comma-separated values
        tags = [tag.strip() for tag in skill_tags.split(",")]
        examples = [example.strip() for example in skill_examples.split(",")]

        # Create agent capabilities
        capabilities = AgentCapabilities(streaming=True, pushNotifications=True)

        # Create agent skill
        skill = AgentSkill(
            id="agentverse_bridge",
            name=f"{agent_name} Bridge",
            description=agent_description,
            tags=tags,
            examples=examples,
        )

        # Create agent card
        agent_card = AgentCard(
            name=agent_name,
            description=agent_description,
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=["text", "text/plain"],
            defaultOutputModes=["text", "text/plain"],
            capabilities=capabilities,
            skills=[skill],
        )

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

        # Build the Starlette app
        app = server.build()

        # Add CORS middleware to allow frontend requests
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # In production, specify exact origins
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Add custom endpoint for bridge agent information
        async def get_bridge_info(request):
            """Endpoint to expose bridge agent address and inspector link.

            For frontend integration purposes.
            """
            try:
                # Construct the inspector link
                bridge_address = bridge_executor.bridge_agent.address
                encoded_uri = urllib.parse.quote(
                    f"http://{host}:{bridge_port}", safe=""
                )
                inspector_link = f"https://agentverse.ai/inspect/?uri={encoded_uri}&address={bridge_address}"

                return JSONResponse(
                    {
                        "bridge_agent_address": bridge_address,
                        "inspector_link": inspector_link,
                        "bridge_port": bridge_port,
                        "mailbox_enabled": True,
                        "target_agent_address": agent_address,
                        "status": "running",
                    }
                )
            except Exception as e:
                logger.error(f"Error in bridge info endpoint: {e}")
                return JSONResponse(
                    {"error": f"Failed to get bridge info: {str(e)}"}, status_code=500
                )

        # Add the route to the app
        app.routes.append(Route("/bridge-info", get_bridge_info, methods=["GET"]))

        logger.info(f"🚀 A2A server starting on {host}:{port}")
        logger.info(f"🔗 Bridging to Agentverse agent: {agent_address}")
        logger.info(f"📋 Agent name: {agent_name}")
        logger.info(f"🏷️  Tags: {', '.join(tags)}")
        logger.info(f"📊 Bridge info endpoint: http://{host}:{port}/bridge-info")

        uvicorn.run(app, host=host, port=port)

    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
