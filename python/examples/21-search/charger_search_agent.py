import uuid
from datetime import datetime, timedelta

from protocol.search_protocol import (
    AttributeQuery,
    SearchRequest,
    SearchResponse,
)

# from fetchai import fetch
from uagents import Agent, Context, Model, Protocol
from uagents.experimental import search

# search scenarios (beyond basic search engine search)
# find agents where attribute == value
# find agents where attribute in range(min, max) / [val_1, ..., val_n]
# find agent where attribute is highest/lowest limit num_of_choices


STORAGE = {}

agent = Agent(
    name="Search Agent for EV Chargers",
    # seed = "<put unique seed>",
    port=8100,
    endpoint="http://localhost:8100/submit",
    agentverse="https://staging.agentverse.ai",
)

search_proto = Protocol(name="agent-search-protocol", version="0.1.0")


@search_proto.on_message(SearchRequest)
async def handle_search_request(ctx: Context, sender: str, msg: SearchRequest):
    ctx.logger.info(f"Received search request from {sender}")
    # create a new session to eventually link incoming responses to the original caller
    search_session = uuid.uuid4()
    storage_dict = {
        str(search_session): {
            "searcher": sender,
            "timeout": datetime.now() + timedelta(seconds=5),
            "request": msg,
            "responses": {},
        }
    }
    # sessions = ctx.storage.get("sessions") or {}
    # sessions.update(storage_dict)
    # ctx.storage.set("sessions", sessions)

    STORAGE.update(storage_dict)

    ctx.logger.info(f"starting new session {search_session} for agent {sender}")

    agents = search.geosearch_agents_by_text(
        latitude=msg.geolocation.latitude,
        longitude=msg.geolocation.longitude,
        radius=msg.geolocation.radius,
        search_text=msg.query,
    )

    query = AttributeQuery(attributes=list(msg.attribute_filter))

    for agent in agents:
        ctx.logger.info(f"querying agent: {agent.address}")
        ctx.send(agent.address, query)

    ## broadcast currently doesn't allow for additional filters, so it might reach agents
    ## that wouldn't be returned by the search engine (e.g., outside of geo search area)
    # ctx.broadcast(msg.protocol_digest, query)
    ## this could be a convenience function to wrap the above internally
    # ctx.broadcast(msg.protocol_digest, query, msg.query, msg.geolocation, msg.tags)


@agent.on_interval(10)
async def check_queries(ctx: Context):
    # sessions = ctx.storage.get("sessions") or {}
    sessions = STORAGE.copy()
    ctx.logger.info(f"active sessions: {len(sessions)}")
    if len(sessions) > 0:
        for session, session_info in sessions.items():
            if session_info["timeout"] < datetime.now():
                ctx.logger.info(f"finish session {session}")
                await finish_query(ctx, session)


async def finish_query(ctx: Context, session: str):
    # session_info = ctx.storage.get("sessions").pop(session)
    session_info = STORAGE.pop(session)
    # evaluate all replies given the initial query
    matching_agents = []
    for agent, response in session_info["responses"].items():
        # for a first test simply check attribute equality
        for attribute, value in session_info["request"].attribute_filter.items():
            if response.attributes[attribute] == value:
                matching_agents.append(agent)
    await ctx.send(
        session_info["searcher"], SearchResponse(result_list=matching_agents)
    )


@agent.on_event("startup")
async def start(ctx: Context):
    ctx.logger.info(Model.build_schema_digest(SearchRequest))


agent.include(search_proto)

if __name__ == "__main__":
    agent.run()

# mermaid sequence diagram
# title General Search Agent Flow

# participant "User Agent" as U
# participant "Search Agent" as S
# participant "Search Engine" as E
# participant "Positive Result Agent" as RP
# participant "Negative Result Agent" as RN

# note over RP, RN: Assuming all agents representing \n
# the desired information / entities \nare supporting the same protocol

# U->S: search for agents with filters
# note over S: check cache here or only after search engine?
# S->E: query general agent group
# S<-E: list of agents
# group broadcast
# S->RP: query attributes
# S->RN: query attributes
# end
# alt agent not fitting
# S<-RN: return attributes or false?
# else
# S<-RP: return attributes or true?
# S->S: add to cache
# S->S: add to result list
# end
# U<-S: result list
# U->RP: consume
