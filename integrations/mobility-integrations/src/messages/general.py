from enum import Enum
from typing import List, Optional

from uagents import Model


class UAgentResponseType(Enum):
    """
    Enumeration representing different types of responses from the User Agent.

    Attributes:
        ERROR (str): Represents an error response type.
        SELECT_FROM_OPTIONS (str): Represents a response type where the user needs to select from given options.
        FINAL_OPTIONS (str): Represents a response type where the user has selected the final option.
    """

    ERROR = "error"
    SELECT_FROM_OPTIONS = "select_from_options"
    FINAL_OPTIONS = "final_options"


class KeyValue(Model):
    """
    Represents a key-value pair.

    Attributes:
        key (str): The key of the pair.
        value (str): The value associated with the key.
    """

    key: str
    value: str


class UAgentResponse(Model):
    """
    Represents a User Agent Response.

    Attributes:
        type (UAgentResponseType): The type of the response.
        agent_address (str, optional): The address of the agent to which the response is directed.
        message (str, optional): A message related to the response.
        options (List[KeyValue], optional): A list of key-value pairs representing response options.
        request_id (str, optional): An optional identifier for the corresponding request.
    """

    type: UAgentResponseType
    agent_address: Optional[str]
    message: Optional[str]
    options: Optional[List[KeyValue]]
    request_id: Optional[str]
