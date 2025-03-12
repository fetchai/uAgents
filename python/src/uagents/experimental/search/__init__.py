from datetime import datetime
from typing import Annotated, Literal

import requests
from pydantic import BaseModel, Field

from uagents.config import AGENTVERSE_URL

SEARCH_API_URL = AGENTVERSE_URL + "/v1/search/agents"

StatusType = Literal["active", "inactive"]
AgentType = Literal["hosted", "local", "mailbox", "proxy", "custom"]
AgentCategory = Literal["fetch-ai", "verified", "community"]


class ProtocolRepresentation(BaseModel):
    # the name of the protocol
    name: str

    # the version of the protocol
    version: str

    # the digest of the protocol
    digest: str


class AgentGeoLocation(BaseModel):
    # the latitude of the agent
    latitude: float

    # the longitude of the agent
    longitude: float

    # the radius in meters defining the area of effect of the agent
    radius: float = 0


class Agent(BaseModel):
    # the address of the agent (this should be used as the id of the agent)
    address: str

    # the public name of the agent
    name: str

    # the contents of the readme file
    readme: str

    # the list of protocols supported by the agent
    protocols: list[ProtocolRepresentation]

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

    # the geolocation of the agent
    geo_location: AgentGeoLocation | None

    # the time at which the agent was last updated at
    last_updated: datetime

    # the time at which the agent was first visible or created
    created_at: datetime


class AgentFilters(BaseModel):
    """The set of filters that should be applied to the agent search entries"""

    # The state of the agent, i.e. is it alive or not
    state: list[StatusType] = Field(default_factory=list)

    # The category of the creator of the agent
    category: list[AgentCategory] = Field(default_factory=list)

    # The category of how the agent is hosted
    agent_type: list[AgentType] = Field(default_factory=list)


SortType = Literal["relevancy", "created-at", "last-modified", "interactions"]
SortDirection = Literal["asc", "desc"]


class AgentSearchCriteria(BaseModel):
    """The search criteria that can be set for the agent search"""

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


class AgentGeoFilter(BaseModel):
    """The geo filter that can be applied to the agent search"""

    # The latitude of the location
    latitude: Annotated[float, Field(ge=-90, le=90)]

    # The longitude of the location
    longitude: Annotated[float, Field(ge=-180, le=180)]

    # The radius of the search in meters
    radius: Annotated[float, Field(gt=0)]


class AgentGeoSearchCriteria(AgentSearchCriteria):
    """The search criteria that can be set for the agent search"""

    # The geo filter that can be applied to the search
    geo_filter: AgentGeoFilter


def _geosearch_agents(criteria: AgentGeoSearchCriteria) -> list[Agent]:
    # NOTE: currently results will be returned based on radius overlap, i.e., results can
    # include agents that are farther away then the specified radius.

    # filter only for active agents
    criteria.filters = AgentFilters(state=["active"])
    response = requests.post(
        url=SEARCH_API_URL + "/geo",
        json=criteria.model_dump(),
        timeout=5,
    )
    if response.status_code == 200:
        data = response.json()
        agents = [Agent.model_validate(agent) for agent in data["agents"]]
        return agents
    return []


def _search_agents(criteria: AgentSearchCriteria) -> list[Agent]:
    response = requests.post(
        url=SEARCH_API_URL,
        json=criteria.model_dump(),
        timeout=5,
    )
    if response.status_code == 200:
        data = response.json()
        agents = [Agent.model_validate(agent) for agent in data["agents"]]
        return agents
    return []


def geosearch_agents_by_proximity(
    latitude: float,
    longitude: float,
    radius: float,
    limit: int = 30,
) -> list[Agent]:
    """
    Return all agents in a circle around the given coordinates that match the given search criteria
    """
    criteria = AgentGeoSearchCriteria(
        geo_filter=AgentGeoFilter(
            latitude=latitude, longitude=longitude, radius=radius
        ),
        limit=limit,
    )
    return _geosearch_agents(criteria)


def geosearch_agents_by_protocol(
    latitude: float,
    longitude: float,
    radius: float,
    protocol_digest: str,
    limit: int = 30,
) -> list[Agent]:
    """
    Return all agents in a circle around the given coordinates that match the given search criteria
    """
    criteria = AgentGeoSearchCriteria(
        geo_filter=AgentGeoFilter(
            latitude=latitude, longitude=longitude, radius=radius
        ),
        limit=limit,
    )
    unfiltered_geoagents = _geosearch_agents(criteria)
    filtered_agents = [
        agent
        for agent in unfiltered_geoagents
        if protocol_digest in [protocol.digest for protocol in agent.protocols]
    ]
    return filtered_agents


def geosearch_agents_by_text(
    latitude: float, longitude: float, radius: float, search_text: str, limit: int = 30
) -> list[Agent]:
    """
    Return all agents in a circle around the given coordinates that match the given search_text
    """
    criteria = AgentGeoSearchCriteria(
        geo_filter=AgentGeoFilter(
            latitude=latitude, longitude=longitude, radius=radius
        ),
        limit=limit,
        search_text=search_text,
    )
    return _geosearch_agents(criteria)


def search_agents_by_protocol(protocol_digest: str, limit: int = 30) -> list[Agent]:
    """Return all agents that match the given search criteria"""
    criteria = AgentSearchCriteria(
        filters=AgentFilters(state=["active"]),
        search_text=protocol_digest,
        limit=limit,
    )
    unfiltered_geoagents = _search_agents(criteria)
    filtered_agents = [
        agent
        for agent in unfiltered_geoagents
        if protocol_digest in [protocol.digest for protocol in agent.protocols]
    ]
    return filtered_agents


def search_agents_by_text(search_text: str, limit: int = 30) -> list[Agent]:
    """Return all agents that match the given search_text"""
    criteria = AgentSearchCriteria(
        filters=AgentFilters(state=["active"]),
        search_text=search_text,
        limit=limit,
    )
    return _search_agents(criteria)
