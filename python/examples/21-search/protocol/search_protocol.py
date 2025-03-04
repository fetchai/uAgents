from typing import Any, Dict, List
from uuid import UUID

from pydantic.v1 import confloat

from uagents import Model


class Location(Model):
    latitude: confloat(strict=True, ge=-90, le=90, allow_inf_nan=False)
    longitude: confloat(strict=True, ge=-180, le=180, allow_inf_nan=False)
    radius: confloat(
        gt=0, allow_inf_nan=False
    )  # This is used for compatibility with uagents message model


class SearchRequest(Model):
    """
    Request model to specify any combination of search attributes (at least 1 must be set).
    In addition to the search engine attributes `query`, `tags`, `geolocation` and
    `protocol_digest`, agent specific attributes can be given in `attribute_filter`, which will
    be considerd by the search agent.
    """

    query: str | None = None
    tags: List[str] | None = None
    geolocation: Location | None = None
    protocol_digest: str | None = None
    # attributes and their target values to be filtered for / aggregate function to be applied?
    # e.g., attribute_filter = {"price": "<100"} or attribute_filter = {"price": "min"}
    attribute_filter: Dict[str, Any] | None = None


class SearchResponse(Model):
    """
    Response to a search request either providing the result list or an error message.
    """

    error: str | None = None
    result_list: List[str] | None = None  # for now only agent addresses


# this model should be supported by any "searchable" agent -> include in base protocol?
class AttributeQuery(Model):
    search_id: (
        UUID  # id to let the search agent map individual responses to search requests
    )
    attributes: List[str]  # attributes to be returned if available


class AttributeResponse(Model):
    search_id: UUID  # must be copied from the incoming AttributeQuery
    attributes: Dict[str, str]  # requested attributes and their value


# ev specific example
class AvailabilityRequest(Model):
    time: str
    duration: int
    charger_specs: Dict[str, Any]


class AvailabilityResponse(Model):
    status: bool
    price: float


# Booking?
