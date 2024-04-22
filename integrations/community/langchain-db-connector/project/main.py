"""
Dynamic / intelligent database connector and query builder

This agent integration will provide you with the means to configure databases
and query them using a natural language prompt. In addition to the normal
agent to agent communication the agent will also be accessible to other agents
via the AI Engine or DeltaV.
The LLM (Language Learning Model) is used to process the natural language
and 1. decide which database to query and 2. how to build the actual query.
The response will be formatted in a way that is suitable for the user.

For service registration use the following description:
    "This agent will give you results of the Agentverse database
    based on a given prompt. The result is given as a text response."

What to do:
    - Add the databases you want to query to the databases.json file
    - Start the agent
    - optional: integrate the agent with the AI Engine or DeltaV
"""

import json
import os

from dotenv import load_dotenv
from uagents import Agent, Context, Protocol

from project.llm import init_db_objects, query_langchain
from project.models.agent_com import LlmResponse, RequestData
from project.models.deltav import DatabasePrompt, UAgentResponse, UAgentResponseType

load_dotenv()

AGENT_SEED = os.environ["AGENT_SEED"]
if not AGENT_SEED:
    raise ValueError("AGENT_SEED not set in .env file")

MAILBOX_KEY = os.environ["MAILBOX_KEY"]

agent = Agent(
    name="project",
    seed=AGENT_SEED,
    mailbox=f"{MAILBOX_KEY}@https://agentverse.ai",
)


@agent.on_event("startup")
async def startup_routine(ctx: Context):
    """This function is called when the agent starts.
    It loads the databases from the databases.json file and stores them in
    the agent's storage. This allows the developer to add databases to the
    agent without changing the code.

    required structure of the databases.json file:
    [
        {
            "host": "host",
            "name": "database_name",
            "description": "description"
        },
        ...
    ]
    """

    ctx.logger.info(f"Agent started: {agent.address}")
    databases = []
    with open("project/databases.json", encoding="UTF-8") as f:
        databases = json.load(f)

    if not databases:
        raise ValueError("No databases found in {db_path}. Please add a database file.")

    ctx.storage.set("databases", databases)
    ctx.logger.info(f"Databases loaded: {len(databases)}")
    ctx.logger.info("Initialising databases...")
    try:
        for db in databases:
            init_db_objects(db["host"], db["name"], db["description"])
    except Exception as e:
        ctx.logger.error(f"Error initialising databases: {e}")
        raise e
    finally:
        ctx.logger.info("Databases initialised.")


@agent.on_message(RequestData, replies={LlmResponse})
async def handle_agent_message(ctx: Context, sender: str, msg: RequestData):
    """Message handler for the agent to agent communication."""
    ctx.logger.info(
        f"Received message from other agent (...{sender[:10]}): {msg.prompt}"
    )
    if msg.prompt:
        res = query_langchain(msg.prompt)
        ctx.logger.info(f"Sending response to other agent: {res}")
        await ctx.send(sender, LlmResponse(message=res))


db_deltav_protocol = Protocol(name="deltav", version="0.1.0")


@db_deltav_protocol.on_message(DatabasePrompt, replies=UAgentResponse)
async def handle_deltav_message(ctx: Context, sender: str, msg: DatabasePrompt):
    """Message handler for DeltaV communication."""
    ctx.logger.info(f"Received message from DeltaV: {msg.prompt}")
    if msg.prompt:
        res = query_langchain(msg.prompt)
        ctx.logger.info(f"Sending response to DeltaV: {res}")
        await ctx.send(
            sender,
            UAgentResponse(message=res, type=UAgentResponseType.FINAL),
        )


if __name__ == "__main__":
    agent.include(db_deltav_protocol, publish_manifest=True)
    agent.run()
