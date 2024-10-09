from datetime import datetime
from typing import List

import requests
from pydantic import BaseModel, Field, Literal

from uagents import Protocol

# from uagents.config import SEARCH_API_URL
from uagents.types import AgentGeoLocation

SEARCH_API_URL = "https://staging.agentverse.ai/v1/search/agents"

StatusType = Literal["active", "inactive"]
AgentType = Literal["hosted", "local", "mailbox"]
AgentCategory = Literal["fetch-ai", "verified", "community"]


class Agent(BaseModel):
    # the address of the agent (this should be used as the id of the agent)
    address: str

    # the public name of the agent
    name: str

    # the contents of the readme file
    readme: str

    # the list of protocols supported by the agent
    protocols: list[Protocol]

    # the href for the avatar image for the agent
    avatar_href: str | None

    # the total interactions for this agent
    total_interactions: int

    # the number of interactions in the last 90 days
    recent_interactions: int

    # agent rating a number between 0 and 5
    rating: float | None

    # the status of the agent
    status: StatusType

    # the type of agent
    type: AgentType

    # the creator of the agent
    category: AgentCategory

    # signaled if the agent is featured or not
    featured: bool = False

    # the time at which the agent was last updated at
    last_updated: datetime

    # the time at which the agent was first visible or created
    created_at: datetime


class AgentFilters(BaseModel):
    """
    The set of filters that should be applied to the agent search entries
    """

    # The state of the agent, i.e. is it alive or not
    state: List[StatusType] = Field(default_factory=list)

    # The category of the creator of the agent
    category: List[AgentCategory] = Field(default_factory=list)

    # The category of how the agent is hosted
    agent_type: List[AgentType] = Field(default_factory=list)

    # The geolocation to limit the search to
    geolocation: AgentGeoLocation = None


SortType = Literal["relevancy", "created-at", "last-modified", "interactions"]
SortDirection = Literal["asc", "desc"]


class AgentSearchCriteria(BaseModel):
    """
    The search criteria that can be set for the agent search
    """

    # The set of filters that should be applied to the search
    filters: AgentFilters = AgentFilters()

    # The type of sorting that should be applied to the search results, relevancy is the default
    sort: SortType = "relevancy"

    # The direction of the sorting, ascending or descending
    direction: SortDirection = "asc"

    # The optional search text that should be included. This should not be a filter mechanism but
    # entries that are closer to the search text should be ranked higher
    search_text: str | None = None

    # The offset of the search results for pagination
    offset: int = 0

    # The limit of the search results for pagination
    limit: int = 30


def _geosearch_agents(
    lat: float, lng: float, radius: float, criteria: AgentSearchCriteria
):
    response = requests.post(
        url=SEARCH_API_URL + "/geo",
        json={"req": criteria},
    )
    if response.status_code == 200:
        data = response.json()
        agents = [Agent.model_validate_json(agent) for agent in data["agents"]]
        return agents
    return []


def _search_agents(criteria: AgentSearchCriteria):
    response = requests.post(
        url=SEARCH_API_URL,
        json={"req": criteria},
    )
    if response.status_code == 200:
        data = response.json()
        agents = [Agent.model_validate_json(agent) for agent in data["agents"]]
        return agents
    return []


def geosearch_agents_by_protocol(
    lat: float, lng: float, radius: float, protocol_digest: str, limit: int = 30
):
    """
    Return all agents in a circle around the given coordinates that match the given search criteria
    """
    criteria = AgentSearchCriteria(
        filters=AgentFilters(
            state="active",
            geolocation=AgentGeoLocation(lat=lat, lng=lng, radius=radius),
        ),
        search_text=protocol_digest,
        limit=limit,
    )
    return _geosearch_agents(lat, lng, radius, criteria)


def geosearch_agents_by_text(
    lat: float, lng: float, radius: float, search_text: str, limit: int = 30
):
    """
    Return all agents in a circle around the given coordinates that match the given search_text
    """
    criteria = AgentSearchCriteria(
        filters=AgentFilters(
            state="active",
            geolocation=AgentGeoLocation(lat=lat, lng=lng, radius=radius),
        ),
        search_text=search_text,
        limit=limit,
    )
    return _geosearch_agents(lat, lng, radius, criteria)


def search_agents_by_protocol(protocol_digest: str, limit: int = 30):
    """
    Return all agents ithat match the given search criteria
    """
    criteria = AgentSearchCriteria(
        filters=AgentFilters(state="active"),
        search_text=protocol_digest,
        limit=limit,
    )
    return _search_agents(criteria)


def search_agents_by_text(search_text: str, limit: int = 30):
    """
    Return all agents that match the given search_text
    """
    criteria = AgentSearchCriteria(
        filters=AgentFilters(state="active"),
        search_text=search_text,
        limit=limit,
    )
    return _search_agents(criteria)
