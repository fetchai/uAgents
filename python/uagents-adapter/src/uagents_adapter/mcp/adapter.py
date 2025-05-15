"""MCP Adapter for uAgents."""

import json
import logging
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

import requests
from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)

from .protocol import (
    CallTool,
    CallToolResponse,
    ListTools,
    ListToolsResponse,
    mcp_protocol_spec,
)


def serialize_messages(messages: List[Dict[str, Any]]) -> str:
    """Serialize messages to JSON string."""
    return json.dumps(messages, default=str)


def deserialize_messages(messages_str: str) -> List[Dict[str, Any]]:
    """Deserialize messages from JSON string."""
    if not messages_str:
        return []
    return json.loads(messages_str)


class MCPServerAdapter:
    """Adapter for integrating uAgents with Model Control Protocol (MCP) servers."""

    def __init__(
        self,
        mcp_server,
        asi1_api_key: str,
        model: str,
        asi1_base_url: str = "https://api.asi1.ai/v1",
    ):
        """
        Initialize the MCP adapter.

        Args:
            mcp_server: The MCP server instance
            asi1_api_key: API key for ASI1 service
            model: Model name to use for ASI1 service
            asi1_base_url: Base URL for ASI1 API (default: "https://api.asi1.ai/v1")
        """
        self.mcp = mcp_server
        self.api_key = asi1_api_key
        self.model = model
        self.asi1_base_url = asi1_base_url

        self.mcp_proto = Protocol(spec=mcp_protocol_spec, role="server")
        self.chat_proto = Protocol(
            name="AgentChatProtocol", version="0.3.0", spec=chat_protocol_spec
        )

        self._setup_mcp_protocol_handlers()
        self._setup_chat_protocol_handlers()

    @property
    def protocols(self) -> list[Protocol]:
        """Get the protocols supported by this adapter."""
        return [self.mcp_proto, self.chat_proto]

    def _setup_mcp_protocol_handlers(self):
        """Set up handlers for MCP protocol messages."""

        @self.mcp_proto.on_message(model=ListTools)
        async def list_tools(ctx: Context, sender: str, msg: ListTools):
            ctx.logger.info("Received ListTools request")
            try:
                tools = await self.mcp.list_tools()
                for tool in tools:
                    ctx.logger.info(f"Tool Name: {tool.name}")
                    ctx.logger.info(f"Description: {tool.description}")
                    ctx.logger.info(
                        f"Parameters: {json.dumps(tool.inputSchema, indent=2)}"
                    )

                raw_tools = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema,
                    }
                    for tool in tools
                ]
                await ctx.send(sender, ListToolsResponse(tools=raw_tools, error=None))
            except Exception as e:
                error_msg = "Error: Failed to retrieve tools from MCP Server"
                ctx.logger.error(f"{error_msg}: {str(e)}")
                await ctx.send(sender, ListToolsResponse(tools=None, error=error_msg))

        @self.mcp_proto.on_message(model=CallTool)
        async def call_tool(ctx: Context, sender: str, msg: CallTool):
            ctx.logger.info(f"Calling tool: {msg.tool} with args: {msg.args}")
            try:
                output = await self.mcp.call_tool(msg.tool, msg.args)
                result = (
                    "\n".join(str(r) for r in output)
                    if isinstance(output, list)
                    else str(output)
                )
                await ctx.send(sender, CallToolResponse(result=result, error=None))
            except Exception as e:
                error = f"Error: Failed to call tool {msg.tool}"
                ctx.logger.error(f"{error}: {str(e)}")
                await ctx.send(sender, CallToolResponse(result=None, error=error))

    def _setup_chat_protocol_handlers(self):
        """Set up handlers for chat protocol messages."""

        @self.chat_proto.on_message(model=ChatMessage)
        async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
            ack = ChatAcknowledgement(
                timestamp=datetime.now(timezone.utc), acknowledged_msg_id=msg.msg_id
            )
            await ctx.send(sender, ack)

            for item in msg.content:
                if isinstance(item, StartSessionContent):
                    ctx.logger.info(f"Got a start session message from {sender}")
                    continue
                elif isinstance(item, TextContent):
                    ctx.logger.info(f"Got a message from {sender}: {item.text}")
                    try:
                        messages_key = f"messages-{str(ctx.session)}"
                        try:
                            messages_serialized = ctx.storage.get(messages_key)
                            messages = (
                                json.loads(messages_serialized)
                                if messages_serialized
                                else []
                            )
                        except Exception as e:
                            ctx.logger.error(f"Error loading message history: {str(e)}")
                            messages = []

                        system_prompt = {
                            "role": "system",
                            "content": (
                                "You are a helpful and intelligent assistant that can only respond"
                                " by using the tools provided to you. "
                                "For every user request, choose the most relevant tool available"
                                " to generate your response. "
                                "If no tool is suitable for answering the question, kindly reply"
                                " with something like "
                                "'I'm sorry, I can't help with that right now.' or "
                                "'That's outside what I can assist with.' "
                                "Always keep your tone polite, concise, and friendly."
                            ),
                        }

                        messages = [m for m in messages if m.get("role") != "system"]
                        messages.insert(0, system_prompt)

                        user_message = {"role": "user", "content": item.text.strip()}
                        messages.append(user_message)

                        ctx.logger.info(
                            f"Sending message to ASI1: {json.dumps(user_message, indent=2)}"
                        )

                        # Get tools from MCP server
                        try:
                            tools = await self.mcp.list_tools()
                            available_tools = []
                            for tool in tools:
                                ctx.logger.info(f"Tool Name: {tool.name}")
                                ctx.logger.info(f"Description: {tool.description}")
                                ctx.logger.info(
                                    f"Parameters: {json.dumps(tool.inputSchema, indent=2)}"
                                )

                            available_tools = [
                                {
                                    "type": "function",
                                    "function": {
                                        "name": tool.name,
                                        "description": tool.description,
                                        "parameters": tool.inputSchema,
                                    },
                                }
                                for tool in tools
                            ]
                        except Exception as e:
                            ctx.logger.error(
                                f"Error: Failed to retrieve tools from MCP Server: {str(e)}"
                            )
                            available_tools = []

                        ctx.logger.info(
                            f"Available tools for ASI1: {json.dumps(available_tools, indent=2)}"
                        )

                        payload = {
                            "model": self.model,
                            "messages": messages,
                            "tools": available_tools,
                            "tool_choice": "required",
                            "temperature": 0.7,
                            "max_tokens": 1024,
                        }

                        headers = {
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        }

                        # Make API call to ASI1
                        try:
                            response = requests.post(
                                f"{self.asi1_base_url}/chat/completions",
                                headers=headers,
                                json=payload,
                            )
                            response_json = response.json()
                        except Exception as e:
                            ctx.logger.error(f"Error calling ASI1 API: {str(e)}")
                            error_msg = (
                                "I'm having trouble connecting to the AI service. "
                                "Please try again in a moment."
                            )
                            await ctx.send(
                                sender,
                                ChatMessage(
                                    timestamp=datetime.now(timezone.utc),
                                    msg_id=uuid4(),
                                    content=[TextContent(type="text", text=error_msg)],
                                ),
                            )
                            continue

                        ctx.logger.info(
                            f"Raw LLM response: {json.dumps(response_json, indent=2)}"
                        )

                        if response_json.get("choices"):
                            assistant_message = response_json["choices"][0]["message"]

                            assistant_msg = {
                                "role": "assistant",
                                "content": assistant_message.get("content", ""),
                            }

                            if assistant_message.get("tool_calls"):
                                assistant_msg["tool_calls"] = assistant_message[
                                    "tool_calls"
                                ]

                            messages.append(assistant_msg)

                            if assistant_message.get("tool_calls"):
                                for tool_call in assistant_message["tool_calls"]:
                                    selected_tool = tool_call["function"]["name"]
                                    try:
                                        tool_args = json.loads(
                                            tool_call["function"]["arguments"]
                                        )
                                    except Exception as e:
                                        ctx.logger.error(
                                            f"Error parsing tool arguments: {str(e)}"
                                        )
                                        error_msg = (
                                            f"There was an issue processing the tool "
                                            f"arguments for {selected_tool}"
                                        )
                                        messages.append(
                                            {
                                                "role": "tool",
                                                "tool_call_id": tool_call["id"],
                                                "content": error_msg,
                                            }
                                        )
                                        continue

                                    ctx.logger.info(
                                        f"Calling tool '{selected_tool}' with arguments: "
                                        f"{json.dumps(tool_args, indent=2)}"
                                    )

                                    try:
                                        tool_results = await self.mcp.call_tool(
                                            selected_tool, tool_args
                                        )
                                        response_text = "\n".join(
                                            str(r) for r in tool_results
                                        )
                                        ctx.logger.info(
                                            f"Tool '{selected_tool}' response: {response_text}"
                                        )
                                    except Exception as e:
                                        response_text = (
                                            f"I encountered an issue while using "
                                            f"the {selected_tool} tool."
                                        )
                                        ctx.logger.error(
                                            f"Error calling tool {selected_tool}: {str(e)}"
                                        )

                                    ctx.logger.info(
                                        f"Tool '{selected_tool}' response: {response_text}"
                                    )

                                    messages.append(
                                        {
                                            "role": "tool",
                                            "tool_call_id": tool_call["id"],
                                            "content": response_text,
                                        }
                                    )

                                # Get final response after tool calls
                                try:
                                    follow_up_payload = {
                                        "model": self.model,
                                        "messages": messages,
                                        "temperature": 0.7,
                                        "max_tokens": 1024,
                                    }

                                    follow_up_response = requests.post(
                                        f"{self.asi1_base_url}/chat/completions",
                                        headers=headers,
                                        json=follow_up_payload,
                                    )
                                    follow_up_json = follow_up_response.json()
                                    final_response = (
                                        follow_up_json.get("choices", [{}])[0]
                                        .get("message", {})
                                        .get(
                                            "content",
                                            "I've processed your request and gathered the info. "
                                            "Let me know if you need anything else!",
                                        )
                                    )
                                except Exception as e:
                                    ctx.logger.error(
                                        f"Error getting final response from ASI1: {str(e)}"
                                    )
                                    final_response = (
                                        "I'm having trouble connecting to the AI service. "
                                        "Please try again in a moment."
                                    )
                            else:
                                final_response = assistant_message.get(
                                    "content",
                                    "I'm having trouble connecting to the AI service. "
                                    "Please try again in a moment!",
                                )
                        else:
                            ctx.logger.error(
                                "Invalid response format from ASI1: missing 'choices'"
                            )
                            final_response = (
                                "I'm experiencing some technical difficulties. "
                                "Please try again in a moment."
                            )

                        # Save updated message history
                        try:
                            ctx.storage.set(messages_key, json.dumps(messages))
                        except Exception as e:
                            ctx.logger.error(f"Error saving message history: {str(e)}")

                        await ctx.send(
                            sender,
                            ChatMessage(
                                timestamp=datetime.now(timezone.utc),
                                msg_id=uuid4(),
                                content=[TextContent(type="text", text=final_response)],
                            ),
                        )

                    except Exception as e:
                        error_msg = (
                            "I'm experiencing some technical difficulties. "
                            "Please try again in a moment."
                        )
                        ctx.logger.error(f"Unexpected error in chat handler: {str(e)}")
                        await ctx.send(
                            sender,
                            ChatMessage(
                                timestamp=datetime.now(timezone.utc),
                                msg_id=uuid4(),
                                content=[TextContent(type="text", text=error_msg)],
                            ),
                        )
                else:
                    ctx.logger.info(f"Got unexpected content from {sender}")

        @self.chat_proto.on_message(model=ChatAcknowledgement)
        async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
            ctx.logger.info(
                f"Received acknowledgement from {sender} for message {msg.acknowledged_msg_id}"
            )
            if msg.metadata:
                ctx.logger.info(f"Metadata: {msg.metadata}")

    def run(self, agent: Agent):
        """
        Run the MCP adapter with the given agent.

        Args:
            agent: The uAgent instance to run
        """
        try:
            logging.info("Starting MCP Server and Agent...")
            agent_thread = threading.Thread(target=agent.run, daemon=True)
            agent_thread.start()
            self.mcp.run(transport="stdio")
        except Exception as e:
            logging.error(f"Error running agent or MCP: {str(e)}")
