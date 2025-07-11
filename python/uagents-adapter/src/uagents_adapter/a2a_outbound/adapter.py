import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import httpx
import uvicorn
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from a2a.utils import new_agent_text_message
from pydantic import BaseModel
from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)


@dataclass
class A2AAgentConfig:
    """Configuration for an A2A agent."""

    name: str
    description: str
    url: str
    port: int
    specialties: list[str]
    skills: list[str] | None = None
    examples: list[str] | None = None
    keywords: list[str] | None = None
    priority: int = 1

    def __post_init__(self):
        """Auto-generate missing fields if not provided."""
        if self.skills is None:
            self.skills = [
                specialty.replace(" ", "_").lower() for specialty in self.specialties
            ]
        if self.examples is None:
            self.examples = [
                f"Help with {specialty.lower()}" for specialty in self.specialties[:3]
            ]
        if self.keywords is None:
            self.keywords = self._generate_keywords_from_specialties()

    def _generate_keywords_from_specialties(self) -> list[str]:
        """Generate keywords dynamically from specialties."""
        keywords = []
        keywords.extend([specialty.lower() for specialty in self.specialties])
        for specialty in self.specialties:
            words = specialty.lower().replace("-", " ").replace("_", " ").split()
            keywords.extend(words)

        return list(set(keywords))


class QueryMessage(BaseModel):
    """Input message model for A2A agent."""

    query: str


class ResponseMessage(BaseModel):
    """Output message model for A2A agent."""

    response: str


class SingleA2AAdapter:
    """Original A2A Adapter for backward compatibility."""

    def __init__(
        self,
        agent_executor: AgentExecutor,
        name: str,
        description: str,
        port: int = 8000,
        a2a_port: int = 9999,
        mailbox: bool = True,
        seed: str | None = None,
        agent_ports: list[int] | None = None,
    ):
        self.agent_executor = agent_executor
        self.name = name
        self.description = description
        self.port = port
        self.a2a_port = a2a_port
        self.mailbox = mailbox
        self.seed = seed or f"{name}_seed"
        self.a2a_server = None
        self.server_thread = None
        self.agent_ports = agent_ports or []
        # Create uAgent
        self.uagent = Agent(name=name, port=port, seed=self.seed, mailbox=mailbox)

        # Create chat protocol
        self.chat_proto = Protocol(spec=chat_protocol_spec)
        self._setup_protocols()

    def _setup_protocols(self):
        """Setup uAgent protocols."""

        @self.chat_proto.on_message(ChatMessage)
        async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
            for item in msg.content:
                if isinstance(item, TextContent):
                    ctx.logger.info(f"📩 Received message from {sender}: {item.text}")
                    try:
                        # Send to A2A agent and get response
                        response = await self._send_to_a2a_agent(
                            item.text, f"http://localhost:{self.a2a_port}"
                        )
                        ctx.logger.info(f"🤖 A2A Response: {response[:100]}...")

                        # Send response back to sender
                        response_msg = ChatMessage(
                            timestamp=datetime.now(timezone.utc),
                            msg_id=uuid4(),
                            content=[TextContent(type="text", text=response)],
                        )
                        await ctx.send(sender, response_msg)
                        ctx.logger.info(f"📤 Sent response back to {sender}")

                        # Send acknowledgment for the original message
                        ack_msg = ChatAcknowledgement(
                            timestamp=datetime.now(timezone.utc),
                            acknowledged_msg_id=msg.msg_id,
                        )
                        await ctx.send(sender, ack_msg)
                        ctx.logger.info(
                            f"✅ Sent acknowledgment for message {msg.msg_id}"
                        )

                    except Exception as e:
                        ctx.logger.error(f"❌ Error processing message: {str(e)}")
                        # Send error response
                        error_response = ChatMessage(
                            timestamp=datetime.now(timezone.utc),
                            msg_id=uuid4(),
                            content=[
                                TextContent(type="text", text=f"❌ Error: {str(e)}")
                            ],
                        )
                        await ctx.send(sender, error_response)

        @self.chat_proto.on_message(ChatAcknowledgement)
        async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
            ctx.logger.info(
                f"✅ Message acknowledged: {msg.acknowledged_msg_id} from {sender}"
            )

        @self.uagent.on_event("startup")
        async def on_start(ctx: Context):
            ctx.logger.info(f"🚀 A2A uAgent started at address: {self.uagent.address}")
            ctx.logger.info(f"🔗 A2A Server running on port: {self.a2a_port}")

        # Include the chat protocol
        self.uagent.include(self.chat_proto, publish_manifest=True)

    async def _send_to_a2a_agent(self, message: str, a2a_url: str) -> str:
        """Send message to A2A agent and get response."""
        async with httpx.AsyncClient() as httpx_client:
            try:
                # Try the correct A2A endpoint format
                payload = {
                    "id": uuid4().hex,
                    "params": {
                        "message": {
                            "role": "user",
                            "parts": [
                                {
                                    "type": "text",
                                    "text": message,
                                }
                            ],
                            "messageId": uuid4().hex,
                        },
                    },
                }

                # Send to A2A agent endpoint
                try:
                    response = await httpx_client.post(
                        f"{a2a_url}/",
                        json=payload,
                        headers={"Content-Type": "application/json"},
                    )

                    if response.status_code == 200:
                        result = response.json()
                        if "result" in result:
                            result_data = result["result"]
                            if "artifacts" in result_data:
                                artifacts = result_data["artifacts"]
                                full_text = ""
                                for artifact in artifacts:
                                    if "parts" in artifact:
                                        for part in artifact["parts"]:
                                            if part.get("kind") == "text":
                                                full_text += part.get("text", "")
                                if full_text.strip():
                                    return full_text.strip()
                            elif (
                                "parts" in result_data and len(result_data["parts"]) > 0
                            ):
                                response_text = result_data["parts"][0].get("text", "")
                                if response_text:
                                    return response_text.strip()
                            return "✅ Response received from A2A agent"
                    else:
                        return f"A2A agent returned HTTP {response.status_code}"
                except Exception as e:
                    return f"❌ Error communicating with A2A agent: {str(e)}"

                return await self._call_executor_directly(message)

            except Exception as e:
                return f"❌ Error communicating with A2A agent: {str(e)}"

    async def _call_executor_directly(self, message: str) -> str:
        """Call the agent executor directly as fallback."""
        try:
            agent_message = new_agent_text_message(message)

            context = RequestContext(
                message=agent_message, context_id=uuid4().hex, task_id=uuid4().hex
            )
            event_queue = EventQueue()

            # Execute the agent
            await self.agent_executor.execute(context, event_queue)

            events = []
            while not event_queue.empty():
                event = await event_queue.dequeue_event()
                if event:
                    events.append(event)

            if events:
                last_event = events[-1]
                if hasattr(last_event, "parts") and last_event.parts:
                    return last_event.parts[0].text
                elif hasattr(last_event, "text"):
                    return last_event.text
                else:
                    return str(last_event)

            return "✅ Task completed successfully"

        except Exception as e:
            return f"❌ Direct executor call failed: {str(e)}"

    def _start_a2a_server(self):
        """Start the A2A server in a separate thread."""

        def run_server():
            # Create A2A server components
            skill = AgentSkill(
                id=f"{self.name.lower()}_skill",
                name=self.name,
                description=self.description,
                tags=[self.name],
                examples=["hi", "hello", "help"],
            )

            agent_card = AgentCard(
                name=self.name,
                description=self.description,
                url=f"http://localhost:{self.a2a_port}/",
                version="1.0.0",
                defaultInputModes=["text"],
                defaultOutputModes=["text"],
                capabilities=AgentCapabilities(),
                skills=[skill],
            )

            request_handler = DefaultRequestHandler(
                agent_executor=self.agent_executor,
                task_store=InMemoryTaskStore(),
            )

            server = A2AStarletteApplication(
                agent_card=agent_card, http_handler=request_handler
            )

            uvicorn.run(
                server.build(),
                host="0.0.0.0",
                port=self.a2a_port,
                timeout_keep_alive=10,
                log_level="info",
            )

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        time.sleep(2)

    def run(self):
        """Run both A2A server and uAgent."""
        print(f"🚀 Starting A2A Adapter for '{self.name}'")
        print(f"📡 A2A Server will run on port {self.a2a_port}")
        print(f"🤖 uAgent will run on port {self.port}")

        # Start A2A server
        self._start_a2a_server()

        # Run uAgent (this will block)
        self.uagent.run()


class MultiA2AAdapter:
    def __init__(
        self,
        name: str,
        description: str,
        *,
        llm_api_key: str,
        port: int = 8000,
        mailbox: bool = True,
        seed: str | None = None,
        agent_configs: list[A2AAgentConfig] | None = None,
        fallback_executor: AgentExecutor | None = None,
        routing_strategy: str = "keyword_match",
        model: str = "asi1-mini",
        base_url: str = "https://api.asi1.ai/v1/chat/completions",
    ):
        self.name = name
        self.description = description
        self.llm_api_key = llm_api_key
        self.port = port
        self.mailbox = mailbox
        self.seed = seed or f"{name}_seed"
        self.agent_configs = agent_configs or []
        self.fallback_executor = fallback_executor
        self.routing_strategy = routing_strategy
        self.model = model
        self.base_url = base_url

        # Runtime agent discovery
        self.discovered_agents: dict[str, dict[str, Any]] = {}
        self.agent_health: dict[str, bool] = {}

        # Create uAgent
        self.uagent = Agent(name=name, port=port, seed=self.seed, mailbox=mailbox)

        # Create chat protocol
        self.chat_proto = Protocol(spec=chat_protocol_spec)
        self._setup_protocols()

    def add_agent_config(self, config: A2AAgentConfig):
        """Add a new agent configuration."""
        self.agent_configs.append(config)
        print(f"✅ Added agent config: {config.name}")
        print(f"   - Specialties: {', '.join(config.specialties or [])}")
        print(f"   - Keywords: {', '.join(config.keywords or [])}")

    def _setup_protocols(self):
        """Setup uAgent protocols."""

        @self.chat_proto.on_message(ChatMessage)
        async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
            for item in msg.content:
                if isinstance(item, TextContent):
                    ctx.logger.info(f"📩 Received message from {sender}: {item.text}")
                    try:
                        # Find the best agent for the query
                        best_agent = await self._route_query(item.text, ctx)

                        if not best_agent:
                            if self.fallback_executor:
                                response = await self._call_fallback_executor(item.text)
                            else:
                                response = "❌ No suitable agent found for this query."
                        else:
                            # Send to the best A2A agent and get response
                            response = await self._send_to_a2a_agent(
                                item.text,
                                best_agent.get("url", best_agent.get("endpoint")),
                            )
                            ctx.logger.info(
                                f"A2A Response from {best_agent.get('name', 'unknown agent')}: "
                                f"{response[:100]}..."
                            )

                        # Send response back to sender
                        response_msg = ChatMessage(
                            timestamp=datetime.now(timezone.utc),
                            msg_id=uuid4(),
                            content=[TextContent(type="text", text=response)],
                        )
                        await ctx.send(sender, response_msg)
                        ctx.logger.info(f"📤 Sent response back to {sender}")

                        # Send acknowledgment for the original message
                        ack_msg = ChatAcknowledgement(
                            timestamp=datetime.now(timezone.utc),
                            acknowledged_msg_id=msg.msg_id,
                        )
                        await ctx.send(sender, ack_msg)
                        ctx.logger.info(
                            f"✅ Sent acknowledgment for message {msg.msg_id}"
                        )

                    except Exception as e:
                        ctx.logger.error(f"❌ Error processing message: {str(e)}")
                        # Send error response
                        error_response = ChatMessage(
                            timestamp=datetime.now(timezone.utc),
                            msg_id=uuid4(),
                            content=[
                                TextContent(type="text", text=f"❌ Error: {str(e)}")
                            ],
                        )
                        await ctx.send(sender, error_response)

        @self.chat_proto.on_message(ChatAcknowledgement)
        async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
            ctx.logger.info(
                f"✅ Message acknowledged: {msg.acknowledged_msg_id} from {sender}"
            )

        @self.uagent.on_event("startup")
        async def on_start(ctx: Context):
            ctx.logger.info(f"🚀 A2A uAgent started at address: {self.uagent.address}")
            ctx.logger.info(f"🔗 Managing {len(self.agent_configs)} configured agents")

            # Discover and health check all agents on startup
            await self._discover_and_health_check_agents(ctx)

        # Include the chat protocol
        self.uagent.include(self.chat_proto, publish_manifest=True)

    async def _discover_and_health_check_agents(self, ctx: Context = None):
        """Discover available A2A agents and perform health checks."""
        self.discovered_agents = {}
        self.agent_health = {}

        async with httpx.AsyncClient() as client:
            for config in self.agent_configs:
                try:
                    card_url = f"{config.url}/.well-known/agent.json"
                    response = await client.get(card_url)

                    if response.status_code == 200:
                        agent_card = response.json()
                        agent_info = {
                            "name": config.name,
                            "url": config.url,
                            "endpoint": config.url,
                            "specialties": config.specialties,
                            "skills": config.skills,
                            "keywords": config.keywords,
                            "examples": config.examples,
                            "priority": config.priority,
                            "card": agent_card,
                            "config": config,
                        }
                        self.discovered_agents[config.name] = agent_info
                        self.agent_health[config.name] = True

                        if ctx:
                            ctx.logger.info(
                                f"✅ Discovered agent: {config.name} at {config.url}"
                            )
                        else:
                            print(f"✅ Discovered agent: {config.name} at {config.url}")
                    else:
                        self.agent_health[config.name] = False
                        if ctx:
                            ctx.logger.warning(
                                f"Agent {config.name} health check failed: "
                                f"HTTP {response.status_code}"
                            )
                        else:
                            print(
                                f"{config.name} health failed: HTTP {response.status_code}"
                            )

                except Exception as e:
                    self.agent_health[config.name] = False
                    if ctx:
                        ctx.logger.warning(
                            f"❌ Could not discover agent {config.name}: {str(e)}"
                        )
                    else:
                        print(f"❌ Could not discover agent {config.name}: {str(e)}")

    async def _route_query(self, query: str, ctx: Context) -> dict[str, Any] | None:
        """Route query to the most suitable agent based on routing strategy."""
        if not self.discovered_agents:
            await self._discover_and_health_check_agents(ctx)

        # Filter healthy agents
        healthy_agents = [
            agent
            for name, agent in self.discovered_agents.items()
            if self.agent_health.get(name, False)
        ]

        if not healthy_agents:
            ctx.logger.warning("No healthy agents available")
            return None

        if self.routing_strategy == "keyword_match":
            return await self._route_by_keywords(query, healthy_agents, ctx)
        elif self.routing_strategy == "round_robin":
            return await self._route_round_robin(healthy_agents, ctx)
        else:
            # Default to keyword matching
            return await self._route_by_keywords(query, healthy_agents, ctx)

    async def _route_by_keywords(
        self, query: str, agents: list[dict], ctx: Context
    ) -> dict[str, Any] | None:
        """Route query based on keyword matching and scoring."""
        query_lower = query.lower()
        best_agent = None
        best_score = 0

        ctx.logger.info(f"🔍 Routing query: '{query}' among {len(agents)} agents")
        llm_selected_agent = await self._llm_route_query(query, agents, ctx)
        if llm_selected_agent:
            return llm_selected_agent
        ctx.logger.info("🔄 LLM routing failed, falling back to keyword matching")

        query_words = set(query_lower.split())

        for agent in agents:
            score = 0
            agent_name = agent.get("name", "unknown")

            # Check keywords (highest priority)
            keywords = agent.get("keywords", [])
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    score += 15  # High score for exact keyword match
                    ctx.logger.info(
                        f"   🎯 {agent_name}: keyword '{keyword}' matched (+15)"
                    )

            # Check specialties (high priority)
            specialties = agent.get("specialties", [])
            for specialty in specialties:
                specialty_lower = specialty.lower()
                # Check for exact specialty match
                if specialty_lower in query_lower:
                    score += 12
                    ctx.logger.info(
                        f"   🎯 {agent_name}: specialty '{specialty}' matched (+12)"
                    )

                # Check for word overlap in specialties
                specialty_words = set(specialty_lower.split())
                common_words = query_words.intersection(specialty_words)
                if common_words:
                    word_score = len(common_words) * 8
                    score += word_score
                    ctx.logger.info(
                        f" {agent_name}: specialty words {common_words} matched (+{word_score})"
                    )

            # Check skills (medium priority)
            skills = agent.get("skills", [])
            for skill in skills:
                skill_lower = skill.lower().replace("_", " ")
                if skill_lower in query_lower:
                    score += 8
                    ctx.logger.info(f"   🎯 {agent_name}: skill '{skill}' matched (+8)")

                # Check for word overlap in skills
                skill_words = set(skill_lower.split())
                common_words = query_words.intersection(skill_words)
                if common_words:
                    word_score = len(common_words) * 4
                    score += word_score
                    ctx.logger.info(
                        f" {agent_name}: skill words {common_words} matched (+{word_score})"
                    )

            # Apply priority multiplier
            priority = agent.get("priority", 1)
            if priority > 1:
                score = int(score * priority)
                ctx.logger.info(f"   🎯 {agent_name}: priority multiplier x{priority}")

            ctx.logger.info(f"   📊 {agent_name}: final score = {score}")

            if score > best_score:
                best_score = score
                best_agent = agent

        if best_agent and best_score > 0:
            ctx.logger.info(
                f"🎯 Selected agent: {best_agent.get('name')} (score: {best_score})"
            )
            return best_agent
        else:
            ctx.logger.info(f"🤷 No suitable agent found (best score: {best_score})")
            # Return the first agent as fallback if no good match
            if agents:
                fallback_agent = agents[0]
                ctx.logger.info(
                    f"🔄 Using fallback agent: {fallback_agent.get('name')}"
                )
                return fallback_agent

        return None

    async def _llm_route_query(
        self, query: str, agents: list[dict], ctx: Context
    ) -> dict[str, Any] | None:
        """Use LLM to intelligently route the query to the most suitable agent."""
        try:
            # Create agent descriptions for the LLM
            agent_descriptions = []
            for i, agent in enumerate(agents):
                agent_desc = (
                    f"{i + 1}. {agent.get('name', 'Unknown')}: "
                    f"{agent.get('description', 'No description')} - Specializes in: "
                    f"{', '.join(agent.get('specialties', []))}"
                )
                agent_descriptions.append(agent_desc)

            agents_text = "\n".join(agent_descriptions)

            prompt = (
                f"You are an intelligent query router. "
                f"Given a user query and a list of available AI agents, "
                f"select the most suitable agent to handle the query."
                f"Available Agents: {agents_text}"
                f"User Query: {query}"
                f"Instructions: "
                f"1. Analyze the query to understand what type of task it requires"
                f"2. Match the query requirements with the agent specialties"
                f"3. Return ONLY the number (1, 2, 3, or 4) of the best agent"
                f"Response format: Just return the number (e.g., '2')"
            )

            # Call ASI API
            url = self.base_url
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "stream": False,
                "max_tokens": 10,
            }

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.llm_api_key}",
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, headers=headers, json=payload, timeout=10
                )

            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    llm_response = result["choices"][0]["message"]["content"].strip()
                    ctx.logger.info(f"🤖 LLM routing response: '{llm_response}'")

                    # Parse the LLM response to get agent index
                    try:
                        agent_index = int(llm_response) - 1  # Convert to 0-based index
                        if 0 <= agent_index < len(agents):
                            selected_agent = agents[agent_index]
                            ctx.logger.info(
                                f"Selected agent: {selected_agent.get('name')}"
                            )
                            return selected_agent
                        else:
                            ctx.logger.warning(
                                f"🚨 LLM returned invalid agent index: {agent_index + 1}"
                            )
                    except ValueError:
                        ctx.logger.warning(
                            f"🚨 LLM returned non-numeric response: '{llm_response}'"
                        )
                else:
                    ctx.logger.warning("🚨 LLM response missing choices")
            else:
                ctx.logger.warning(
                    f"🚨 LLM API call failed: {response.status_code} - {response.text}"
                )

        except Exception as e:
            ctx.logger.warning(f"🚨 LLM routing error: {str(e)}")

        return None

    async def _route_round_robin(
        self, agents: list[dict], ctx: Context
    ) -> dict[str, Any] | None:
        """Route query using round-robin strategy."""
        if not hasattr(self, "_round_robin_index"):
            self._round_robin_index = 0

        if agents:
            selected_agent = agents[self._round_robin_index % len(agents)]
            self._round_robin_index += 1
            ctx.logger.info(f"🔄 Round-robin selected: {selected_agent.get('name')}")
            return selected_agent

        return None

    async def _send_to_a2a_agent(self, message: str, a2a_url: str) -> str:
        """Send message to a specific A2A agent and get response."""
        async with httpx.AsyncClient() as httpx_client:
            try:
                # Prepare A2A message payload
                payload = {
                    "id": uuid4().hex,
                    "params": {
                        "message": {
                            "role": "user",
                            "parts": [
                                {
                                    "type": "text",
                                    "text": message,
                                }
                            ],
                            "messageId": uuid4().hex,
                        },
                    },
                }

                # Send to A2A agent endpoint
                try:
                    response = await httpx_client.post(
                        f"{a2a_url}/",
                        json=payload,
                        headers={"Content-Type": "application/json"},
                        timeout=60,
                    )

                    if response.status_code == 200:
                        result = response.json()
                        # Extract the response content from A2A format
                        if "result" in result:
                            result_data = result["result"]
                            # Handle artifacts format (streaming responses)
                            if "artifacts" in result_data:
                                artifacts = result_data["artifacts"]
                                full_text = ""
                                for artifact in artifacts:
                                    if "parts" in artifact:
                                        for part in artifact["parts"]:
                                            if part.get("kind") == "text":
                                                full_text += part.get("text", "")
                                if full_text.strip():
                                    return full_text.strip()
                            # Handle standard parts format
                            elif (
                                "parts" in result_data and len(result_data["parts"]) > 0
                            ):
                                response_text = result_data["parts"][0].get("text", "")
                                if response_text:
                                    return response_text.strip()
                            # Fallback: return success message
                            return "✅ Response received from A2A agent"
                    else:
                        return f"A2A agent returned HTTP {response.status_code}"
                except Exception as e:
                    return f"❌ Error communicating with A2A agent: {str(e)}"

                # If endpoint failed
                return f"❌ Could not communicate with A2A agent at {a2a_url}"

            except Exception as e:
                return f"❌ Error communicating with A2A agent: {str(e)}"

    async def _call_fallback_executor(self, message: str) -> str:
        """Call the fallback executor if no suitable agent is found."""
        try:
            # Create a mock request context
            agent_message = new_agent_text_message(message)

            context = RequestContext(
                message=agent_message, context_id=uuid4().hex, task_id=uuid4().hex
            )

            # Create event queue to capture responses
            event_queue = EventQueue()

            # Execute the fallback agent
            if self.fallback_executor is not None:
                await self.fallback_executor.execute(context, event_queue)
            else:
                return "❌ No fallback executor is configured."

            # Get the response from the event queue
            events = []
            while not event_queue.empty():
                event = await event_queue.dequeue_event()
                if event:
                    events.append(event)

            if events:
                # Get the last event which should be the response
                last_event = events[-1]
                if hasattr(last_event, "parts") and last_event.parts:
                    return last_event.parts[0].text
                elif hasattr(last_event, "text"):
                    return last_event.text
                else:
                    return str(last_event)

            return "✅ Task completed successfully"

        except Exception as e:
            return f"❌ Fallback executor call failed: {str(e)}"

    def run(self):
        """Run the multi-agent uAgent."""
        print(f"🚀 Starting A2A Multi-Agent Adapter: '{self.name}'")
        print(f"🤖 uAgent will run on port {self.port}")
        print(f"📊 Managing {len(self.agent_configs)} agents")
        print(f"🎯 Routing strategy: {self.routing_strategy}")

        # Print agent summary
        for config in self.agent_configs:
            print(f"   • {config.name}: {', '.join(config.specialties or [])}")
        self.uagent.run()


def a2a_servers(
    agent_configs: list[A2AAgentConfig], executors: dict[str, AgentExecutor]
):
    """
    Start individual A2A servers for each agent config and executor.
    Each server runs in a separate thread.
    Args:
        agent_configs: List of A2AAgentConfig objects.
        executors: Dict mapping agent name to its AgentExecutor instance.
    """

    def start_server(config: A2AAgentConfig, executor: AgentExecutor):
        try:
            skill = AgentSkill(
                id=f"{config.name}_skill",
                name=config.name.title(),
                description=config.description,
                tags=config.specialties,
                examples=[f"Help with {s.lower()}" for s in config.specialties[:3]],
            )
            agent_card = AgentCard(
                name=config.name.title(),
                description=config.description,
                url=f"http://localhost:{config.port}/",
                version="1.0.0",
                defaultInputModes=["text"],
                defaultOutputModes=["text"],
                capabilities=AgentCapabilities(),
                skills=[skill],
            )
            server = A2AStarletteApplication(
                agent_card=agent_card,
                http_handler=DefaultRequestHandler(
                    agent_executor=executor, task_store=InMemoryTaskStore()
                ),
            )
            print(f"🚀 Starting {config.name} on port {config.port}")
            uvicorn.run(
                server.build(),
                host="0.0.0.0",
                port=config.port,
                timeout_keep_alive=10,
                log_level="info",
            )
        except Exception as e:
            print(f"❌ Error starting {config.name}: {e}")

    for config in agent_configs:
        executor = executors[config.name]
        threading.Thread(
            target=start_server, args=(config, executor), daemon=True
        ).start()
        time.sleep(1)
    print("⏳ Initializing servers...")
    time.sleep(5)
    print("✅ All A2A servers started!")
