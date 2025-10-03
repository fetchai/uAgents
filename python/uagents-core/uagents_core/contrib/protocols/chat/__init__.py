"""
This module contains the protocol specification for the agent chat protocol.
"""

from datetime import datetime, timezone
from typing import Literal, TypedDict
from uuid import uuid4

from pydantic.v1 import UUID4

from uagents_core.models import Model
from uagents_core.protocol import ProtocolSpecification


class Metadata(TypedDict):
    # primarily used with the `Resource` model. This field specifies the mime_type of
    # resource that is being referenced. A full list can be found at `docs/mime_types.md`
    mime_type: str

    # the role of the resource
    role: str


class TextContent(Model):
    type: Literal["text"]

    # The text of the content. The format of this field is UTF-8 encoded strings. Additionally,
    # markdown based formatting can be used and will be supported by most clients
    text: str

    def __init__(self, text: str, type: str = "text"):
        super().__init__(type=type, text=text)


class Resource(Model):
    # the uri of the resource
    uri: str

    # the set of metadata for this resource, for more detailed description of the set of
    # fields see `docs/metadata.md`
    metadata: dict[str, str]


class ResourceContent(Model):
    type: Literal["resource"]

    # The resource id
    resource_id: UUID4

    # The resource or list of resource for this content. typically only a single
    # resource will be sent, however, if there are accompanying resources like
    # thumbnails and audio tracks these can be additionally referenced
    #
    # In the case of the a list of resources, the first element of the list is always
    # considered the primary resource
    resource: Resource | list[Resource]

    def __init__(
        self,
        resource_id: UUID4,
        resource: Resource | list[Resource],
        type: str = "resource",
    ):
        super().__init__(type=type, resource_id=resource_id, resource=resource)


class MetadataContent(Model):
    type: Literal["metadata"]

    # the set of metadata for this content, for more detailed description of the set of
    # fields see `docs/metadata.md`
    metadata: dict[str, str]

    def __init__(self, metadata: dict[str, str], type: str = "metadata"):
        super().__init__(type=type, metadata=metadata)


class StartSessionContent(Model):
    type: Literal["start-session"]

    def __init__(self, type: str = "start-session"):
        super().__init__(type=type)


class EndSessionContent(Model):
    type: Literal["end-session"]

    def __init__(self, type: str = "end-session"):
        super().__init__(type=type)


class StartStreamContent(Model):
    type: Literal["start-stream"]

    stream_id: UUID4

    def __init__(self, stream_id: UUID4, type: str = "start-stream"):
        super().__init__(type=type, stream_id=stream_id)


class EndStreamContent(Model):
    type: Literal["end-stream"]

    stream_id: UUID4

    def __init__(self, stream_id: UUID4, type: str = "end-stream"):
        super().__init__(type=type, stream_id=stream_id)


# The combined agent content types
AgentContent = (
    TextContent
    | ResourceContent
    | MetadataContent
    | StartSessionContent
    | EndSessionContent
    | StartStreamContent
    | EndStreamContent
)


class ChatMessage(Model):
    # the timestamp for the message, should be in UTC
    timestamp: datetime

    # a unique message id that is generated from the message instigator
    msg_id: UUID4

    # the list of content elements in the chat
    content: list[AgentContent]

    def __init__(
        self,
        content: list[AgentContent],
        msg_id: UUID4 | None = None,
        timestamp: datetime | None = None,
    ):
        msg_id = msg_id or uuid4()
        timestamp = timestamp or datetime.now(timezone.utc)
        super().__init__(timestamp=timestamp, msg_id=msg_id, content=content)

    def text(self) -> str:
        """
        Collect all text content from this ChatMessage.

        Returns:
            str: The concatenated text content.
        """
        text = ""
        for content in self.content:
            if isinstance(content, TextContent):
                text += content.text
        return text


class ChatAcknowledgement(Model):
    # the timestamp for the message, should be in UTC
    timestamp: datetime

    # the msg id that is being acknowledged
    acknowledged_msg_id: UUID4

    # optional acknowledgement metadata
    metadata: dict[str, str] | None = None

    def __init__(
        self,
        acknowledged_msg_id: UUID4,
        metadata: dict[str, str] | None = None,
        timestamp: datetime | None = None,
    ):
        timestamp = timestamp or datetime.now(timezone.utc)
        super().__init__(
            timestamp=timestamp,
            acknowledged_msg_id=acknowledged_msg_id,
            metadata=metadata,
        )


chat_protocol_spec = ProtocolSpecification(
    name="AgentChatProtocol",
    version="0.3.0",
    interactions={
        ChatMessage: {ChatAcknowledgement},
        ChatAcknowledgement: set(),
    },
)
