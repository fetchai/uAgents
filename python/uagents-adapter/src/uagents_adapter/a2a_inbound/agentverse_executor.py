import asyncio
import logging
import os
import secrets
import threading
import time
from datetime import datetime, timezone
from uuid import uuid4

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    InternalError,
    InvalidParamsError,
    Part,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import (
    new_agent_text_message,
    new_task,
)
from a2a.utils.errors import ServerError
from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

logger = logging.getLogger(__name__)


class AgentverseAgentExecutor(AgentExecutor):
    """Generic AgentExecutor that bridges to any Agentverse uAgent via chat protocol."""

    def __init__(
        self,
        target_agent_address: str,
        bridge_name: str = "a2a_bridge",
        bridge_port: int = 8082,
    ):
        """
        Initialize the bridge to a specific Agentverse agent.

        Args:
            target_agent_address: The address of the target uAgent on Agentverse
            bridge_name: Name for the bridge agent (default: "a2a_bridge")
            bridge_port: Port for the bridge agent (default: 8082)
        """
        self.target_agent_address = target_agent_address
        self.bridge_name = bridge_name
        self.bridge_port = bridge_port
        self.response_cache = {}
        self.bridge_running = False
        self.pending_requests = {}

        # Create bridge agent with mailbox to communicate via Agentverse
        # Use user-provided seed or generate secure fallback
        bridge_seed = self._get_bridge_seed(bridge_name, bridge_port)
        self.bridge_agent = Agent(
            name=bridge_name,
            port=bridge_port,
            seed=bridge_seed,
            mailbox=True,  # Enable mailbox for Agentverse communication
        )

        # Setup chat protocol
        self.chat_proto = Protocol(spec=chat_protocol_spec)
        self._setup_bridge()
        self._start_bridge()

    def _get_bridge_seed(self, bridge_name: str, bridge_port: int) -> str:
        """Get bridge agent seed from environment or generate secure fallback.

        Priority:
        1. UAGENTS_BRIDGE_SEED environment variable (user-provided)
        2. Secure random generation with warning

        Args:
            bridge_name: Name of the bridge agent
            bridge_port: Port of the bridge agent

        Returns:
            Bridge agent seed string
        """
        # Check for user-provided seed in environment variables
        user_seed = os.getenv("UAGENTS_BRIDGE_SEED")

        if user_seed:
            logger.info("🔐 Using user-provided bridge seed from environment")
            return user_seed

        # Generate secure random seed as fallback
        secure_seed = f"a2a_bridge_{secrets.token_hex(16)}_{bridge_port}"

        logger.warning("⚠️  No UAGENTS_BRIDGE_SEED provided - using random seed")
        logger.warning("⚠️  Bridge agent address will change on restart")
        logger.warning("⚠️  Set UAGENTS_BRIDGE_SEED env var for consistent addresses:")
        logger.warning("⚠️  export UAGENTS_BRIDGE_SEED='your_unique_seed_here'")

        return secure_seed

    def _setup_bridge(self):
        """Setup bridge agent message handlers."""

        @self.bridge_agent.on_event("startup")
        async def bridge_startup(ctx: Context):
            self.bridge_running = True
            logger.info(f"A2A Bridge agent started with address: {ctx.agent.address}")
            logger.info(f"Target Agentverse agent: {self.target_agent_address}")

        @self.chat_proto.on_message(ChatMessage)
        async def handle_chat_response(ctx: Context, sender: str, msg: ChatMessage):
            """Handle chat message responses from target agent."""
            # Extract text content from chat message
            response_text = ""
            for content in msg.content:
                if isinstance(content, TextContent):
                    response_text += content.text

            logger.debug(f"🔍 DEBUG: Received response from sender: {sender}")
            logger.debug(
                f"🔍 DEBUG: Pending requests: {list(self.pending_requests.keys())}"
            )
            for req_id, req_info in self.pending_requests.items():
                logger.debug(
                    f"🔍 DEBUG: Request {req_id} target: {req_info.get('target')}"
                )

            # Match with pending request - if sender is the target agent we sent to
            matched = False
            for request_id, _request_info in list(self.pending_requests.items()):
                # Fix: Check if sender matches the target we sent the request to
                if sender == self.target_agent_address:
                    self.response_cache[request_id] = response_text
                    del self.pending_requests[request_id]
                    logger.info(
                        f"✅ Matched and cached response from {sender}: {response_text[:100]}..."
                    )
                    matched = True

                    # Send acknowledgment
                    ack_msg = ChatAcknowledgement(
                        timestamp=datetime.now(timezone.utc),
                        acknowledged_msg_id=msg.msg_id,
                    )
                    await ctx.send(sender, ack_msg)
                    break

            if not matched:
                logger.warning(f"❌ No matching request found for sender {sender}")

        @self.chat_proto.on_message(ChatAcknowledgement)
        async def handle_chat_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
            """Handle chat acknowledgments."""
            logger.info(f"Chat message acknowledged by {sender}")

        # Add periodic task to process pending requests
        @self.bridge_agent.on_interval(period=0.1)
        async def process_pending_requests(ctx: Context):
            # Process any pending requests
            for request_id, request_info in list(self.pending_requests.items()):
                if not request_info.get("sent", False):
                    # Pass user context for per-user authentication
                    # Format: [USER_CONTEXT:context_id] actual_query
                    context_id = request_info.get(
                        "contextId", request_info.get("context_id", "unknown")
                    )
                    contextual_query = (
                        f"[USER_CONTEXT:{context_id}] {request_info['query']}"
                    )

                    # Create chat message with user context
                    chat_msg = ChatMessage(
                        timestamp=datetime.now(timezone.utc),
                        msg_id=uuid4(),
                        content=[TextContent(type="text", text=contextual_query)],
                    )

                    # Send to target agent
                    await ctx.send(self.target_agent_address, chat_msg)
                    self.pending_requests[request_id]["sent"] = True
                    self.pending_requests[request_id]["target"] = (
                        self.target_agent_address
                    )
                    logger.info(f"Sent chat message to {self.target_agent_address}")

        # Include chat protocol
        self.bridge_agent.include(self.chat_proto)

    def _start_bridge(self):
        """Start bridge agent in background thread."""

        def run_bridge():
            self.bridge_agent.run()

        thread = threading.Thread(target=run_bridge, daemon=True)
        thread.start()

        # Wait for bridge to start
        max_wait = 20
        wait_count = 0
        while not self.bridge_running and wait_count < max_wait:
            time.sleep(0.5)
            wait_count += 1

        if self.bridge_running:
            logger.info("✅ A2A Bridge to Agentverse started successfully")
        else:
            logger.error("❌ Failed to start A2A bridge")

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute A2A request by bridging to Agentverse agent."""
        error = self._validate_request(context)
        if error:
            raise ServerError(error=InvalidParamsError())

        query = context.get_user_input()
        task = context.current_task

        if not task:
            task = new_task(context.message)  # type: ignore
            await event_queue.enqueue_event(task)

        updater = TaskUpdater(event_queue, task.id, task.contextId)

        try:
            logger.info("Starting async iteration over Agentverse bridge responses")
            async for item in self._stream_via_agentverse(query, task.contextId):
                logger.info(f"Received item from bridge: {item}")
                is_task_complete = item["is_task_complete"]
                require_user_input = item["require_user_input"]

                if not is_task_complete and not require_user_input:
                    logger.info("Updating status to working")
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(
                            item["content"],
                            task.contextId,
                            task.id,
                        ),
                    )
                elif require_user_input:
                    logger.info("Updating status to input_required")
                    await updater.update_status(
                        TaskState.input_required,
                        new_agent_text_message(
                            item["content"],
                            task.contextId,
                            task.id,
                        ),
                        final=True,
                    )
                    break
                else:
                    logger.info("Adding artifact and completing task")
                    await updater.add_artifact(
                        [Part(root=TextPart(text=item["content"]))],
                        name="agentverse_result",
                    )
                    await updater.complete()
                    logger.info("Task completed successfully")
                    break
            logger.info("Finished async iteration")
        except Exception as e:
            logger.error(f"An error occurred while streaming the response: {e}")
            raise ServerError(error=InternalError()) from e

    async def _stream_via_agentverse(self, query: str, context_id: str):
        """
        Bridge method that communicates with Agentverse agent via chat protocol.
        Maintains same interface as direct agent execution.
        """
        try:
            logger.info(f"Processing query via Agentverse bridge: {query}")

            # Send working status first
            yield {
                "is_task_complete": False,
                "require_user_input": False,
                "content": "Connecting to Agentverse agent...",
            }

            # Create unique request ID
            request_id = f"req_{context_id}_{int(time.time())}"

            # Add request to pending queue
            self.pending_requests[request_id] = {
                "query": query,
                "contextId": context_id,
                "sent": False,
                "target": None,
            }

            # Wait for response with timeout
            timeout = 120  # 2 minutes timeout
            wait_count = 0

            while request_id not in self.response_cache and wait_count < timeout:
                await asyncio.sleep(0.5)
                wait_count += 1

            if request_id in self.response_cache:
                response = self.response_cache.pop(request_id)
                logger.info("Successfully received response from Agentverse agent")

                # Check if response indicates need for more input
                if any(
                    phrase in response.lower()
                    for phrase in [
                        "need more",
                        "specify",
                        "unclear",
                        "provide more details",
                        "can you provide",
                        "please provide",
                        "which",
                        "what",
                        "how",
                    ]
                ):
                    logger.info("Yielding input_required response")
                    yield {
                        "is_task_complete": False,
                        "require_user_input": True,
                        "content": response,
                    }
                else:
                    # Successful completion
                    logger.info("Yielding completed response")
                    yield {
                        "is_task_complete": True,
                        "require_user_input": False,
                        "content": response,
                    }
                logger.info("Response yielded successfully")
                return  # Explicitly return to end the generator
            else:
                # Timeout occurred
                logger.error("Agentverse communication timed out")
                # Clean up pending request
                if request_id in self.pending_requests:
                    del self.pending_requests[request_id]
                yield {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": "Request timed out. Please try again.",
                }

        except Exception as e:
            logger.error(f"Error in Agentverse bridge communication: {e}")
            yield {
                "is_task_complete": False,
                "require_user_input": True,
                "content": f"Error communicating with Agentverse agent: {str(e)}",
            }

    def _validate_request(self, context: RequestContext) -> bool:
        """Validate the incoming request."""
        return False

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel operation - not supported."""
        raise ServerError(error=UnsupportedOperationError())
