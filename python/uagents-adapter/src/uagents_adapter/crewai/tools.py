"""Tool for converting a CrewAI agent into a uAgent and registering it on Agentverse."""

import json
import os
import socket
import threading
import time
from datetime import datetime
from typing import Any, Dict, List

import requests
from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic import BaseModel, Field
from uagents import Agent, Context, Model, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)

try:
    from openai import OpenAI

    has_openai = True
except ImportError:
    has_openai = False

from ..common import (
    RUNNING_UAGENTS,
    RUNNING_UAGENTS_LOCK,
    BaseRegisterTool,
    BaseRegisterToolInput,
    ResponseMessage,
    cleanup_uagent,
    create_text_chat,
)

# Initialize protocols
chat_proto = Protocol(spec=chat_protocol_spec)


# Helper function to extract parameters from text using OpenAI's GPT-4o model
def extract_params_from_text(text: str, param_keys: List[str]) -> Dict[str, str]:
    """Extract parameters from text using OpenAI's GPT-4o model."""
    if not has_openai:
        print("OpenAI package not installed. Parameter extraction will not work.")
        return {key: "" for key in param_keys}

    # Initialize the client with your API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found in environment.")
        return {key: "" for key in param_keys}

    client = OpenAI(api_key=api_key)

    # Create system message with instructions for parameter extraction
    system_message = (
        f"Extract the following parameters from text: {', '.join(param_keys)}. "
        "Return only a JSON object with these parameters as keys. "
        "If a parameter isn't mentioned, use an empty string as its value."
    )

    try:
        # Make the API call
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": text},
            ],
            response_format={"type": "json_object"},
        )

        # Get the JSON response from the model
        result_text = response.choices[0].message.content

        if not result_text:
            print("Empty response from OpenAI API")
            return {key: "" for key in param_keys}

        try:
            result = json.loads(result_text)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON response: {result_text}")
            print(f"JSON parse error: {e}")
            return {key: "" for key in param_keys}

        # Ensure all required parameters are included
        for key in param_keys:
            if key not in result:
                result[key] = ""

        return result
    except Exception as e:
        print(f"Error extracting parameters: {e}")
        return {key: "" for key in param_keys}


class CrewaiRegisterToolInput(BaseRegisterToolInput):
    """Input schema for Crewai register tool."""

    crew_obj: Any = Field(
        ..., description="The CrewAI crew object that will be converted to a uAgent"
    )
    query_params: Dict[str, Any] | None = Field(
        None, description="Parameters to dynamically create the QueryMessage model"
    )
    example_query: str | None = Field(
        None, description="Optional example query to show in the agent documentation"
    )


class CrewaiRegisterTool(BaseRegisterTool):
    """Tool for converting a CrewAI crew into a uAgent and registering it on Agentverse.

    This tool takes a CrewAI crew and transforms it into a uAgent, which can
    interact with other agents in the Agentverse ecosystem. The uAgent will
    expose the CrewAI crew's functionality through HTTP endpoints and
    automatically register with Agentverse for discovery and access.
    """

    name: str = "crewai_register"
    description: str = "Register a CrewAI crew as a uAgent on Agentverse"
    args_schema: type[BaseModel] = CrewaiRegisterToolInput

    # Track current agent info for easier access
    _current_agent_info: dict[str, Any] | None = None

    def __init__(self, **kwargs):
        """Initialize the tool and register the cleanup handler."""
        super().__init__(**kwargs)
        # Cleanup handler is already registered at module level

    def _find_available_port(
        self, preferred_port=None, start_range=8000, end_range=9000
    ):
        """Find an available port to use for the agent."""
        # Try the preferred port first
        if preferred_port is not None:
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

    def _crewai_to_uagent(
        self,
        crew_obj,
        agent_name,
        port,
        description=None,
        ai_agent_address=None,
        mailbox=True,
        query_params=None,
        example_query=None,
    ):
        """Convert a CrewAI crew to a uAgent."""
        # Create the agent
        if mailbox:
            uagent = Agent(
                name=agent_name,
                port=port,
                seed=f"uagent_seed_{agent_name} and {port}",
                mailbox=True,
            )
        else:
            uagent = Agent(
                name=agent_name,
                port=port,
                seed=f"uagent_seed_{agent_name} and {port}",
                endpoint=[f"http://localhost:{port}/submit"],
            )

        # Get AI agent address from environment if not provided
        if ai_agent_address is None:
            ai_agent_address = os.getenv("AI_AGENT_ADDRESS")
            if not ai_agent_address:
                ai_agent_address = (
                    "agent1q0h70caed8ax769shpemapzkyk65uscw4xwk6dc4t3emvp5jdcvqs9xs32y"
                )

        # Store the agent for later cleanup
        agent_info = {
            "name": agent_name,
            "uagent": uagent,
            "port": port,
            "crew_obj": crew_obj,
            "ai_agent_address": ai_agent_address,
            "mailbox": mailbox,
            "query_params": query_params,
            "example_query": example_query,
        }

        if description is not None:
            agent_info["description"] = description

        with RUNNING_UAGENTS_LOCK:
            RUNNING_UAGENTS[agent_name] = agent_info

        # Define startup handler to show agent address
        @uagent.on_event("startup")
        async def startup(ctx: Context):
            agent_address = ctx.agent.address
            agent_info["address"] = agent_address
            ctx.logger.info(
                f"Agent '{agent_name}' started with address: {agent_address}"
            )

        # Define a message handler for direct parameter passing
        # Create a generic handler for structured messages
        class ParameterMessage(Model):
            """A generic message to receive parameters for the crew."""

            # This is just a placeholder - we'll handle any fields dynamically

        @uagent.on_message(model=ParameterMessage)
        async def handle_parameters(ctx: Context, sender: str, msg: ParameterMessage):
            try:
                # Get the CrewAI crew from our stored reference
                crew = agent_info["crew_obj"]

                try:
                    # Extract all attributes from the message as a dict
                    inputs = {}
                    for field_name in dir(msg):
                        # Skip private/special attributes
                        if not field_name.startswith("_") and not callable(
                            getattr(msg, field_name)
                        ):
                            try:
                                value = getattr(msg, field_name)
                                # Only include serializable fields
                                if isinstance(
                                    value, (str, int, float, bool, list, dict)
                                ):
                                    inputs[field_name] = value
                            except Exception:
                                pass

                    # If query_params is defined, filter to only include those params
                    if query_params:
                        filtered_inputs = {}
                        for param in query_params:
                            if param in inputs:
                                filtered_inputs[param] = inputs[param]

                        # Use filtered inputs if we found any matching parameters
                        if filtered_inputs:
                            inputs = filtered_inputs

                    # Run the CrewAI crew with the extracted parameters
                    ctx.logger.info(f"Running crew with inputs: {inputs}")
                    result = crew.kickoff(inputs=inputs)
                    final_response = str(result)
                except Exception as e:
                    final_response = f"Error running crew: {str(e)}"

                # Send response back
                await ctx.send(sender, ResponseMessage(response=final_response))

            except Exception as e:
                error_msg = f"Error processing parameters: {str(e)}"
                await ctx.send(sender, ResponseMessage(response=f"Error: {error_msg}"))

        # Chat protocol handlers
        @chat_proto.on_message(ChatMessage)
        async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
            try:
                ctx.logger.info(f"Got a message from {sender}")
                # Print model digest for the received message
                try:
                    ctx.logger.info(f"Received message model digest: {msg}")
                except Exception as digest_error:
                    ctx.logger.error(
                        f"Error calculating model digest: {str(digest_error)}"
                    )

                ctx.storage.set(str(ctx.session), sender)
                # Immediately acknowledge the message
                await ctx.send(
                    sender,
                    ChatAcknowledgement(
                        timestamp=datetime.utcnow(), acknowledged_msg_id=msg.msg_id
                    ),
                )

                for item in msg.content:
                    if isinstance(item, StartSessionContent):
                        ctx.logger.info(f"Got a start session message from {sender}")
                        continue
                    elif isinstance(item, TextContent):
                        ctx.logger.info(
                            f"Got a text message from {sender}: {item.text}"
                        )
                        ctx.storage.set(str(ctx.session), sender)

                        # Process the message directly using parameter extraction
                        try:
                            # Get the crew from agent_info
                            crew = agent_info["crew_obj"]
                            ctx.logger.info(f"Using crew object: {crew}")

                            # Try to extract parameters from the text message
                            # if query_params is defined
                            if query_params:
                                ctx.logger.info(
                                    f"Extracting parameters using keys: {list(query_params.keys())}"
                                )
                                extracted_params = extract_params_from_text(
                                    item.text, list(query_params.keys())
                                )
                                ctx.logger.info(
                                    f"Extracted parameters: {extracted_params}"
                                )

                                # Ensure OpenAI API key is available
                                if not os.environ.get("OPENAI_API_KEY"):
                                    error_msg = (
                                        "OPENAI_API_KEY environment variable not set. "
                                        "CrewAI requires this to function."
                                    )
                                    ctx.logger.error(error_msg)
                                    await ctx.send(sender, create_text_chat(error_msg))
                                    return

                                # Ensure we have some non-empty parameters
                                if all(not val for val in extracted_params.values()):
                                    ctx.logger.warning(
                                        "All extracted parameters are empty, using text as input"
                                    )
                                    result = crew.kickoff(inputs={"input": item.text})
                                else:
                                    ctx.logger.info(
                                        "Running crew with extracted parameters"
                                    )
                                    result = crew.kickoff(inputs=extracted_params)
                            else:
                                # Otherwise just use the text as input
                                ctx.logger.info(
                                    "No query_params defined, using text as input"
                                )

                                # Ensure OpenAI API key is available
                                if not os.environ.get("OPENAI_API_KEY"):
                                    error_msg = (
                                        "OPENAI_API_KEY environment variable not set. "
                                        "CrewAI requires this to function."
                                    )
                                    ctx.logger.error(error_msg)
                                    await ctx.send(sender, create_text_chat(error_msg))
                                    return

                                result = crew.kickoff(inputs={"input": item.text})

                            # Send the response
                            ctx.logger.info(f"Sending response: {str(result)[:100]}...")
                            response_chat = create_text_chat(str(result))
                            await ctx.send(sender, response_chat)

                        except Exception as e:
                            ctx.logger.error(f"Error running crew: {str(e)}")
                            error_message = f"Error: {str(e)}"
                            await ctx.send(sender, create_text_chat(error_message))
                    elif isinstance(item, EndSessionContent):
                        ctx.logger.info(f"Got an end session message from {sender}")
                        continue
                    else:
                        ctx.logger.info(
                            f"Got unexpected content type from {sender}: {type(item).__name__}"
                        )
            except Exception as e:
                ctx.logger.error(f"Error handling message: {str(e)}")
                # Try to send an error message
                try:
                    await ctx.send(
                        sender, create_text_chat(f"Error processing message: {str(e)}")
                    )
                except Exception as send_error:
                    ctx.logger.error(f"Failed to send error message: {str(send_error)}")

        # Acknowledgement handler
        @chat_proto.on_message(ChatAcknowledgement)
        async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
            ctx.logger.info(
                f"Got an acknowledgement from {sender} for {msg.acknowledged_msg_id}"
            )

        # Register protocols
        uagent.include(chat_proto)

        return agent_info

    def _start_uagent_in_thread(self, agent_info):
        """Start the uAgent in a separate thread."""

        def run_agent():
            try:
                uagent = agent_info["uagent"]
                # Start the agent
                uagent.run()
            except Exception as e:
                print(f"Error running uAgent: {str(e)}")

        # Start the agent in a thread
        thread = threading.Thread(target=run_agent, daemon=True)
        thread.start()
        agent_info["thread"] = thread

        # Give the agent a moment to start
        time.sleep(0.5)

        return agent_info

    def _register_agent_with_agentverse(self, agent_info):
        """Register agent with Agentverse API and update README."""
        try:
            # Only proceed with registration if mailbox is True
            if not agent_info.get("mailbox", True):
                print(
                    f"Agent '{agent_info.get('name')}' using endpoint configuration, "
                    "skipping Agentverse registration"
                )
                return

            # Wait for agent to be ready
            time.sleep(8)

            agent_address = agent_info.get("address")
            bearer_token = agent_info.get("api_token")
            port = agent_info.get("port")
            name = agent_info.get("name")
            description = agent_info.get("description", "")
            query_params = agent_info.get("query_params")
            example_query = agent_info.get("example_query")

            if not agent_address or not bearer_token:
                print("Missing agent address or API token, skipping API calls")
                return

            print(f"Connecting agent '{name}' to Agentverse...")

            # Setup headers
            headers = {
                "Authorization": f"Bearer {bearer_token}",
                "Content-Type": "application/json",
            }

            # 1. POST request to connect
            connect_url = f"http://127.0.0.1:{port}/connect"
            connect_payload = {"agent_type": "mailbox", "user_token": bearer_token}

            try:
                connect_response = requests.post(
                    connect_url, json=connect_payload, headers=headers
                )
                if connect_response.status_code == 200:
                    print(f"Successfully connected agent '{name}' to Agentverse")
                else:
                    print(
                        f"Failed to connect agent '{name}' to Agentverse: "
                        f"{connect_response.status_code} - {connect_response.text}"
                    )
            except Exception as e:
                print(f"Error connecting agent '{name}' to Agentverse: {str(e)}")

            # 2. PUT request to update agent info on agentverse.ai
            print(f"Updating agent '{name}' README on Agentverse...")
            update_url = f"https://agentverse.ai/v1/agents/{agent_address}"

            # Create input model description based on query_params
            input_model = ""
            if query_params:
                # Handle the case when query_params is a dictionary
                if isinstance(query_params, dict):
                    input_model = "class ParameterMessage(Model):\n"
                    for param_name, param_info in query_params.items():
                        # Handle case where param_info is a simple string (type)
                        if isinstance(param_info, str):
                            param_type = param_info
                            input_model += f"    {param_name}: {param_type}\n"
                        # Handle case where param_info is a dict with detailed spec
                        elif isinstance(param_info, dict) and param_info.get("type"):
                            param_type = param_info.get("type", "str")
                            # Convert JSON-schema types to Python types
                            if param_type == "string":
                                param_type = "str"
                            elif param_type == "number":
                                param_type = "float"
                            elif param_type == "integer":
                                param_type = "int"
                            elif param_type == "boolean":
                                param_type = "bool"

                            required = param_info.get("required", True)
                            if required:
                                input_model += f"    {param_name}: {param_type}\n"
                            else:
                                input_model += (
                                    f"    {param_name}: {param_type} | None = None\n"
                                )
                        else:
                            # Default to string if structure is unknown
                            input_model += f"    {param_name}: str\n"
                else:
                    # Handle the case when query_params is not a dictionary
                    input_model = "class QueryMessage(Model):\n    query: str"
            else:
                input_model = "class QueryMessage(Model):\n    query: str"

            # Create README content with badges and input model
            readme_content = f"""# {name}
![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)<br />

{description}

**Input Data Model**
```
{input_model}
```

**Output Data Model**
```
class ResponseMessage(Model):
    response: str
```
"""

            # Add example query if provided
            if example_query:
                readme_content += f"""
**Example Query**
```
{example_query}
```
"""

            update_payload = {
                "name": name,
                "readme": readme_content,
                "short_description": description,
            }

            try:
                update_response = requests.put(
                    update_url, json=update_payload, headers=headers
                )
                if update_response.status_code == 200:
                    print(f"Successfully updated agent '{name}' README on Agentverse")
                else:
                    print(
                        f"Failed to update agent '{name}' README on Agentverse: "
                        f"{update_response.status_code} - {update_response.text}"
                    )
            except Exception as e:
                print(f"Error updating agent '{name}' README on Agentverse: {str(e)}")

        except Exception as e:
            print(f"Error registering agent with Agentverse: {str(e)}")

    def get_agent_info(self):
        """Get information about the current agent."""
        return self._current_agent_info

    def _run(
        self,
        crew_obj: Any,
        name: str,
        port: int,
        description: str,
        api_token: str | None = None,
        ai_agent_address: str | None = None,
        mailbox: bool = True,
        query_params: Dict[str, Any] | None = None,
        example_query: str | None = None,
        *,
        run_manager: CallbackManagerForToolRun | None = None,
        return_dict: bool = False,
    ) -> dict[str, Any]:
        """Create a uAgent for a CrewAI crew and return its address."""
        try:
            # Find a port if one wasn't specified
            if port <= 0:
                port = self._find_available_port()

            # Ensure we have a port
            if port <= 0:
                raise ValueError("Invalid port specified")

            # Convert CrewAI crew to uAgent
            agent_info = self._crewai_to_uagent(
                crew_obj=crew_obj,
                agent_name=name,
                port=port,
                description=description,
                ai_agent_address=ai_agent_address,
                mailbox=mailbox,
                query_params=query_params,
                example_query=example_query,
            )

            # Add API token if provided
            if api_token:
                agent_info["api_token"] = api_token

            # Start the uAgent in a thread
            self._start_uagent_in_thread(agent_info)

            # Register with Agentverse if API token is provided
            if api_token:
                self._register_agent_with_agentverse(agent_info)

            # Store the current agent info
            self._current_agent_info = agent_info

            # Prepare the result
            address = agent_info.get("address", "")
            url = (
                f"http://localhost:{port}/submit"
                if not agent_info.get("mailbox", True)
                else None
            )

            # Create result object with basic agent info
            result = {
                "agent_name": name,
                "agent_address": address,
                "agent_port": port,
                "agent_description": description,
                "agent_url": url,
                "agent_mailbox": agent_info.get("mailbox", True),
                "agent_ai_address": agent_info.get("ai_agent_address", ""),
            }

            # Add parameter information if provided
            if query_params:
                result["agent_query_params"] = query_params

            if example_query:
                result["agent_example_query"] = example_query

            if return_dict:
                # Return full information
                return result
            else:
                # Return formatted string
                mailbox_txt = (
                    "with mailbox" if agent_info.get("mailbox", True) else f"at {url}"
                )
                param_txt = ""
                if query_params:
                    param_names = ", ".join(query_params.keys())
                    param_txt = f" (Parameters: {param_names})"
                return f"Agent '{name}' registered with address: {address} {mailbox_txt}{param_txt}"

        except Exception as e:
            # Clean up any partial agent creation
            if name in RUNNING_UAGENTS:
                cleanup_uagent(name)
            raise RuntimeError(f"Failed to register agent: {str(e)}") from e

    async def _arun(
        self,
        crew_obj: Any,
        name: str,
        port: int,
        description: str,
        api_token: str | None = None,
        ai_agent_address: str | None = None,
        mailbox: bool = True,
        query_params: Dict[str, Any] | None = None,
        example_query: str | None = None,
        *,
        run_manager: CallbackManagerForToolRun | None = None,
    ) -> dict[str, Any]:
        """Create a uAgent for a CrewAI crew and return its address (async version)."""
        return self._run(
            crew_obj=crew_obj,
            name=name,
            port=port,
            description=description,
            api_token=api_token,
            ai_agent_address=ai_agent_address,
            mailbox=mailbox,
            query_params=query_params,
            example_query=example_query,
            run_manager=run_manager,
        )
