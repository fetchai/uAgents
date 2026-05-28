"""Conversion of A2A streaming events to Agentverse chat AgentContent.

This module processes events from on_message_send_stream, converting A2A Part
and Task types to chat protocol AgentContent. It also determines when a task's
lifecycle is over so the caller can clean up session state.

References used for conversion logic:

A2A protocol spec (Part, TaskState, Artifact, streaming events):
  https://a2aproject.github.io/A2A/latest/specification/

Part (Section 4.1.6 — must contain exactly one of: text, raw, url, data):
  https://a2aproject.github.io/A2A/latest/specification/#416-part

TaskState (Section 4.1.9 — terminal states: completed, failed, canceled, rejected):
  https://a2aproject.github.io/A2A/latest/specification/#419-taskstate

Streaming events (Section 4.2 — TaskStatusUpdateEvent, TaskArtifactUpdateEvent):
  https://a2aproject.github.io/A2A/latest/specification/#42-streaming-events

A2A Python SDK types (Pydantic models with snake_case fields, camelCase JSON aliases):
  Part = RootModel[TextPart | FilePart | DataPart]
  FilePart.file: FileWithBytes | FileWithUri
  FileWithUri: uri (str), mime_type (str | None), name (str | None)
  FileWithBytes: bytes (str, base64), mime_type (str | None), name (str | None)
  TaskState enum: submitted, working, input_required, completed, canceled,
    failed, rejected, auth_required, unknown
  TaskStatus: state (TaskState), message (Message | None)
  Event = Message | Task | TaskStatusUpdateEvent | TaskArtifactUpdateEvent
    (type alias from a2a.server.events.event_queue)
"""

from __future__ import annotations

import base64
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

from uagents_core.agentverse.sdk.common.types import Uploader
from uagents_core.contrib.protocols.chat import (
    AgentContent,
    Resource,
    ResourceContent,
    TextContent,
)


async def parts_to_agent_content(
    parts: list[Part], upload: Uploader | None = None
) -> list[AgentContent]:
    """Convert a list of A2A ``Part`` objects to chat protocol ``AgentContent``.

    Handles TextPart, FilePart (both URI and base64-bytes variants), and
    DataPart.

    FileWithUri maps directly to ResourceContent — the URI is passed through
    and name/mimeType are forwarded into Resource.metadata.

    FileWithBytes is uploaded via the provided ``upload`` callable first.
    Falls back to a data: URI if upload is not provided or returns None.
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
            elif isinstance(file, FileWithBytes):
                mime = file.mime_type or "application/octet-stream"
                metadata: dict[str, str] = {"mime_type": mime}
                if file.name:
                    metadata["name"] = file.name

                uri = (
                    await upload(base64.b64decode(file.bytes), mime)
                    if upload
                    else None
                )
                if uri is None:
                    uri = f"data:{mime};base64,{file.bytes}"

                content.append(
                    ResourceContent(
                        resource_id=uuid4(),
                        resource=Resource(uri=uri, metadata=metadata),
                    )
                )
        elif isinstance(inner, DataPart):
            content.append(TextContent(text=json.dumps(inner.data, default=str)))

    return content


async def extract_content(
    event: Event, upload: Uploader | None = None
) -> list[AgentContent]:
    """Extract AgentContent from an A2A streaming Event.

    Handles all four Event variants:
    - Message: convert parts directly
    - Task: extract from artifacts and/or status message
    - TaskStatusUpdateEvent: extract from status message, signal state transitions
    - TaskArtifactUpdateEvent: convert artifact parts

    Returns an empty list when there is no content to forward.
    """
    if isinstance(event, Message):
        return await parts_to_agent_content(event.parts, upload)

    if isinstance(event, TaskArtifactUpdateEvent):
        return await parts_to_agent_content(event.artifact.parts, upload)

    if isinstance(event, TaskStatusUpdateEvent):
        return await _extract_status_content(event.status, event.final, upload)

    if isinstance(event, Task):
        content: list[AgentContent] = []
        if event.artifacts:
            for artifact in event.artifacts:
                content.extend(
                    await parts_to_agent_content(artifact.parts, upload)
                )
        return content or await _extract_status_content(
            event.status, final=True, upload=upload
        )

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


async def _extract_status_content(
    status: TaskStatus, final: bool, upload: Uploader | None = None
) -> list[AgentContent]:
    """Extract content from a TaskStatus based on state."""
    state = status.state

    if status.message and status.message.parts:
        return await parts_to_agent_content(status.message.parts, upload)

    if state == TaskState.working:
        return [TextContent(text="Agent is working on your request...")]

    if state == TaskState.failed:
        return [TextContent(text="Agent failed to process the request.")]

    if state == TaskState.input_required:
        return [TextContent(text="Agent needs additional input.")]

    if state == TaskState.canceled:
        return [TextContent(text="Task was canceled.")]

    if state == TaskState.rejected:
        return [TextContent(text="Task was rejected by the agent.")]

    if state == TaskState.auth_required:
        return [TextContent(text="Agent requires authentication.")]

    # completed, submitted, unknown — no message to forward
    return []
