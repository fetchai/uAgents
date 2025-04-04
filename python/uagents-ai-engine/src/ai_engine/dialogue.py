from typing import Literal

from pydantic import BaseModel

from uagents.experimental.dialogues import Edge, Node

# Extending dialogues with metadata for AI Engine support.
# This will move to the uagents.experimental.dialogues module in the future.


class EdgeMetadata(BaseModel):
    """Metadata for the edges"""

    # what is the target of this transition, user means direct message to the user,
    # ai, system involves AI Engine processing
    target: Literal["user", "ai", "system", "agent"]

    # can the AI Engine observe this transition, and process the information
    observable: bool


class EdgeDescription(BaseModel):
    """Temporary type to add structure to the edge description"""

    # the original description of the edge
    description: str

    # the metadata of the edge
    metadata: EdgeMetadata


def create_edge(
    name: str,
    description: str,
    target: Literal["user", "ai", "system", "agent"],
    observable: bool,
    parent: Node,
    child: Node,
) -> Edge:
    """Create an edge with metadata"""

    # create the metadata
    metadata = EdgeMetadata(target=target, observable=observable)

    # description of the edge
    structured_description = EdgeDescription(description=description, metadata=metadata)

    # create a new edge
    return Edge(
        name=name,
        description=structured_description.json(),
        parent=parent,
        child=child,
    )
