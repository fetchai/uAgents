"""Conversion and inspection of A2A types for Agentverse chat.

Contains:
- parts_to_agent_content: converts A2A Part objects to AgentContent
- extract_content: converts A2A streaming Event objects to AgentContent
- is_task_complete: checks whether an Event signals the end of a task
"""

from __future__ import annotations

import json
from uuid import uuid4

from a2a.server.events.event_queue import Event
from a2a.types import (
    DataPart,
    FilePart,
    FileWithBytes,
    FileWithUri,
    Message,
    Part,
    Task,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)
from uagents_core.contrib.protocols.chat import (
    AgentContent,
    Resource,
    ResourceContent,
    TextContent,
)


def parts_to_agent_content(parts: list[Part]) -> list[AgentContent]:
    """Convert a list of A2A ``Part`` objects to chat protocol ``AgentContent``.

    Handles TextPart, FilePart (both URI and base64-bytes variants), and
    DataPart.

    FileWithUri maps directly to ResourceContent — the URI is passed through
    and name/mimeType are forwarded into Resource.metadata.

    FileWithBytes is converted to a ResourceContent with a data: URI embedding
    the base64 content inline.
    """
    content: list[AgentContent] = []
    for part in parts:
        inner = part.root
        if isinstance(inner, TextPart):
            content.append(TextContent(text=inner.text))
        elif isinstance(inner, FilePart):
            file = inner.file
            if isinstance(file, FileWithUri):
                metadata: dict[str, str] = {}
                if file.name:
                    metadata["name"] = file.name
                if file.mime_type:
                    metadata["mime_type"] = file.mime_type
                content.append(
                    ResourceContent(
                        resource_id=uuid4(),
                        resource=Resource(uri=file.uri, metadata=metadata),
                    )
                )
            if isinstance(file, FileWithBytes):
                # Ideally we would upload to ExternalStorage and reference the
                # asset_id, but POST /v1/storage/assets/ requires a user Bearer
                # token — agent attestation tokens can only PUT to existing
                # assets.  Use a data: URI to preserve content inline.
                mime = file.mime_type or "application/octet-stream"
                uri = f"data:{mime};base64,{file.bytes}"
                metadata: dict[str, str] = {"mime_type": mime}
                if file.name:
                    metadata["name"] = file.name
                content.append(
                    ResourceContent(
                        resource_id=uuid4(),
                        resource=Resource(uri=uri, metadata=metadata),
                    )
                )
        elif isinstance(inner, DataPart):
            # TextContent is a lossy stand-in: the chat protocol has no
            # structured-data content type matching A2A DataPart.
            content.append(TextContent(text=json.dumps(inner.data, default=str)))
    return content


def extract_content(event: Event) -> list[AgentContent]:
    """Extract AgentContent from an A2A streaming Event.

    Handles all four Event variants:
    - Message: convert parts directly
    - Task: extract from artifacts and/or status message
    - TaskStatusUpdateEvent: extract from status message, signal state transitions
    - TaskArtifactUpdateEvent: convert artifact parts

    Returns an empty list when there is no content to forward.
    """
    if isinstance(event, Message):
        return parts_to_agent_content(event.parts)

    if isinstance(event, TaskArtifactUpdateEvent):
        return parts_to_agent_content(event.artifact.parts)

    if isinstance(event, TaskStatusUpdateEvent):
        return _extract_status_content(event.status, event.final)

    if isinstance(event, Task):
        content: list[AgentContent] = []
        if event.artifacts:
            for artifact in event.artifacts:
                content.extend(parts_to_agent_content(artifact.parts))
        return content or _extract_status_content(event.status, final=True)

    return []


_TERMINAL_STATES = {
    TaskState.completed,
    TaskState.canceled,
    TaskState.failed,
    TaskState.rejected,
}


def is_task_complete(event: Event) -> bool:
    """Return True if the event signals the task lifecycle is over.

    This checks for terminal *task* state, not just end-of-stream.
    ``input_required`` and ``auth_required`` set ``final=True`` on the
    stream event (no more events until user replies), but the task is
    still active — the session context must be kept.

    Per the A2A spec, terminal states are: completed, failed, canceled, rejected.
    """
    if isinstance(event, Message):
        return True
    if isinstance(event, TaskStatusUpdateEvent):
        return event.status.state in _TERMINAL_STATES
    return False


def _extract_status_content(status: TaskStatus, final: bool) -> list[AgentContent]:
    """Extract content from a TaskStatus based on state."""
    state = status.state

    if status.message and status.message.parts:
        return parts_to_agent_content(status.message.parts)

    if state == TaskState.working:
        return [TextContent(type="text", text="Agent is working on your request...")]

    if state == TaskState.failed:
        return [TextContent(type="text", text="Agent failed to process the request.")]

    if state == TaskState.input_required:
        return [TextContent(type="text", text="Agent needs additional input.")]

    if state == TaskState.canceled:
        return [TextContent(type="text", text="Task was canceled.")]

    if state == TaskState.rejected:
        return [TextContent(type="text", text="Task was rejected by the agent.")]

    if state == TaskState.auth_required:
        return [TextContent(type="text", text="Agent requires authentication.")]

    # completed, submitted, unknown — no message to forward
    return []
