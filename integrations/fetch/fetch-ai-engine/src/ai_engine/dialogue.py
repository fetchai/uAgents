from pydantic import BaseModel
from typing import Literal

from uagents.experimental.dialogues import Edge, Node


# Extending dialogues with metadata for AI Engine support.
# This will move to the uagents.experimental.dialogues module in the future.


class NodeMetadata(BaseModel):
    """Metadata for the nodes"""

    # is the node an initial node
    initial: bool = False

    # is the node a terminal node
    terminal: bool = False


class EdgeMetadata(BaseModel):
    """Metadata for the edges"""

    # what is the target of this transition, user means direct message to the user, ai, system involves AI Engine processing
    target: Literal["user", "ai", "system", "agent"]

    # can the AI Engine observe this transition, and process the information
    observable: bool


class NodeDescription(BaseModel):
    """Temporary type to add structure to the node description"""

    # the original description of the node
    description: str

    # the metadata of the node
    metadata: NodeMetadata


class EdgeDescription(BaseModel):
    """Temporary type to add structure to the edge description"""

    # the original description of the edge
    description: str

    # the metadata of the edge
    metadata: EdgeMetadata


def create_node(
    name: str,
    description: str,
    initial: bool = False,
    terminal: bool = False,
):
    """Create a node with metadata"""

    # create the metadata
    metadata = NodeMetadata(initial=initial, terminal=terminal)

    # description of the node
    description = NodeDescription(
        description=description,
        metadata=metadata,
    )

    # create a new node
    return Node(
        name=name,
        description=description.json(),
    )


def create_edge(
    name: str,
    description: str,
    target: Literal["user", "ai", "system", "agent"],
    observable: bool,
    parent: Node,
    child: Node,
):
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
