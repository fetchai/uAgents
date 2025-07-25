"""
This module contains the protocol specification for the agent chat protocol,
plus a ready‐to‐use Protocol instance and message‐building helpers.
"""

from datetime import datetime
from datetime import timezone as _timezone
from typing import Literal, TypedDict, Union
from uuid import uuid4

from pydantic.v1 import UUID4

from uagents_core.models import Model
from uagents_core.protocol import ProtocolSpecification

# --- Original content models & spec ---------------------------------------


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


class MetadataContent(Model):
    type: Literal["metadata"]

    # the set of metadata for this content, for more detailed description of the set of
    # fields see `docs/metadata.md`
    metadata: dict[str, str]


class StartSessionContent(Model):
    type: Literal["start-session"]


class EndSessionContent(Model):
    type: Literal["end-session"]


class StartStreamContent(Model):
    type: Literal["start-stream"]

    stream_id: UUID4


class EndStreamContent(Model):
    type: Literal["end-stream"]

    stream_id: UUID4


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


class ChatAcknowledgement(Model):
    # the timestamp for the message, should be in UTC
    timestamp: datetime

    # the msg id that is being acknowledged
    acknowledged_msg_id: UUID4

    # optional acknowledgement metadata
    metadata: dict[str, str] | None = None


chat_protocol_spec = ProtocolSpecification(
    name="AgentChatProtocol",
    version="0.3.0",
    interactions={
        ChatMessage: {ChatAcknowledgement},
        ChatAcknowledgement: set(),
    },
)


# --- Helper Class for simplifying Chat Protocol -----------------------------


class ChatObjects:
    """
    Utility class for constructing ChatMessage objects with common content types.
    """

    @classmethod
    def text(cls, text: str, end_session: bool = False) -> ChatMessage:
        """
        Create a ChatMessage with TextContent.
        Pass end_session=True to append an EndSessionContent.
        """
        contents: list[AgentContent] = [TextContent(type="text", text=text)]
        if end_session:
            contents.append(EndSessionContent(type="end-session"))
        return ChatMessage(
            timestamp=datetime.now(_timezone.utc),
            msg_id=uuid4(),
            content=contents,
        )

    @classmethod
    def end_session(cls) -> ChatMessage:
        """
        Create a ChatMessage that signals end of session.
        """
        return ChatMessage(
            timestamp=datetime.now(_timezone.utc),
            msg_id=uuid4(),
            content=[EndSessionContent(type="end-session")],
        )

    @classmethod
    def resource(
        cls,
        asset_id: Union[str, UUID4],
        uri: str,
        mime_type: str = "image/png",
        role: str = "generated-resource",
    ) -> ChatMessage:
        """
        Create a ChatMessage carrying a ResourceContent (e.g. image/file).
        """
        res_id = UUID4(asset_id) if isinstance(asset_id, str) else asset_id
        rc = ResourceContent(
            type="resource",
            resource_id=res_id,
            resource=Resource(uri=uri, metadata={"mime_type": mime_type, "role": role}),
        )
        return ChatMessage(
            timestamp=datetime.now(_timezone.utc),
            msg_id=uuid4(),
            content=[rc],
        )
