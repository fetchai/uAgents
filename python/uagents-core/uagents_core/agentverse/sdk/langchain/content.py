"""Conversion of LangChain message dicts to Agentverse chat AgentContent.

Handles the JSON response from LangGraph's /runs/wait endpoint, extracting
content from AI messages and mapping LangChain content block types (text,
image, image_url, file, audio, video) to AgentContent.

This module assumes the graph uses MessagesState (or a compatible state with
a "messages" key). Graphs with custom state schemas that don't include
"messages" will produce an empty result.
  MessagesState spec (TypedDict with messages: list[AnyMessage]):
  https://reference.langchain.com/python/langgraph/graph/message/MessagesState
  Graph state can be any TypedDict, Pydantic model, or dataclass — there is
  no fixed response schema for /runs/wait.

References used for conversion logic:

HTTP endpoint spec (POST /runs/wait, POST /threads/{id}/runs/wait):
  https://docs.langchain.com/langsmith/agent-server-api/stateless-runs/create-run-wait-for-output
  https://docs.langchain.com/langsmith/agent-server-api/thread-runs/create-run-wait-for-output
  Note: the 200 response schema is untyped — the shape depends on the graph's
  state. The examples below document the common MessagesState convention.

SDK → HTTP endpoint link (no doc covers this, confirmed from source only):
  https://github.com/langchain-ai/langgraph/blob/main/libs/sdk-py/langgraph_sdk/_async/runs.py
  (RunsClient.wait builds "/runs/wait" or "/threads/{id}/runs/wait" and POSTs
  via httpx, returning the JSON body unchanged.)

Response shape: /runs/wait returns the graph's final state directly as JSON —
there is no fixed schema; it depends on the graph's state definition. The
common convention is MessagesState which gives {"messages": [...]}.
  Example: https://reference.langchain.com/python/langgraph-sdk/_async/runs/RunsClient/wait
  Tutorial: https://docs.langchain.com/langgraph-platform/stateless-runs

AIMessage parsing (we only extract from AIMessage, skip the rest of AnyMessage):
  AnyMessage union: https://reference.langchain.com/python/langchain-core/messages/utils/AnyMessage
  AIMessage (type: Literal["ai"]): https://reference.langchain.com/python/langchain-core/messages/ai/AIMessage
  AIMessage.content (str | list[str | dict]): https://reference.langchain.com/python/langchain-core/messages/base/BaseMessage/content
  Content block overview: https://reference.langchain.com/python/langchain-core/messages/content
  Content block usage guide: https://docs.langchain.com/oss/python/langchain/messages

Content block TypedDicts (all share: url, base64, file_id, mime_type, id, index, extras):
  TextContentBlock: https://reference.langchain.com/python/langchain-core/messages/content/TextContentBlock
  ImageContentBlock: https://reference.langchain.com/python/langchain-core/messages/content/ImageContentBlock
  AudioContentBlock: https://reference.langchain.com/python/langchain-core/messages/content/AudioContentBlock
  VideoContentBlock: https://reference.langchain.com/python/langchain-core/messages/content/VideoContentBlock
  FileContentBlock: https://reference.langchain.com/python/langchain-core/messages/content/FileContentBlock
  image_url is a provider-native format (OpenAI), not a standard TypedDict:
    https://docs.langchain.com/oss/python/langchain/messages

"""

from __future__ import annotations

import base64
import json
from typing import Any
from urllib.parse import unquote_to_bytes
from uuid import uuid4

from uagents_core.agentverse.sdk.common.logger import logger
from uagents_core.agentverse.sdk.common.types import Uploader
from uagents_core.contrib.protocols.chat import (
    AgentContent,
    Resource,
    ResourceContent,
    TextContent,
)


class SummariseData:
    """Lazy log formatter that truncates long string values in nested dicts."""

    __slots__ = ("_data", "_max_len")

    def __init__(self, data: dict[str, Any], max_len: int = 200):
        self._data = data
        self._max_len = max_len

    def __str__(self) -> str:
        return json.dumps(self._trim(self._data), indent=2, default=str)

    def _trim(self, obj):
        if isinstance(obj, str):
            return f"{obj[:self._max_len]}..." if len(obj) > self._max_len else obj
        if isinstance(obj, dict):
            return {k: self._trim(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._trim(item) for item in obj]
        return obj


def _turn_messages_since_last_human(messages: list[Any]) -> list[Any]:
    last_human_idx = -1
    for i, msg in enumerate(messages):
        if isinstance(msg, dict) and msg.get("type") == "human":
            last_human_idx = i
    if last_human_idx < 0:
        return messages
    return messages[last_human_idx + 1 :]


async def extract_ai_content(
    data: dict[str, Any], upload: Uploader | None = None
) -> list[AgentContent]:
    """Extract AgentContent from the current turn in a /runs/wait response.

    Expects ``data["messages"]`` — the MessagesState convention for /runs/wait.
    Threaded runs return the full conversation history; only the latest reply
    for the current user message is returned.
    """
    logger.debug("LangGraph response: %s", SummariseData(data))

    messages = data.get("messages")
    if not isinstance(messages, list):
        messages = []

    turn_messages = _turn_messages_since_last_human(messages)

    for msg in reversed(turn_messages):
        if not isinstance(msg, dict):
            continue
        if msg.get("type") not in ("ai", "tool"):
            continue
        content = await message_content_to_agent_content(msg.get("content", ""), upload)
        if content:
            return content

    return []

async def message_content_to_agent_content(
    content: str | list[dict[str, Any]], upload: Uploader | None = None
) -> list[AgentContent]:
    """Convert a single LangChain message's ``content`` field to AgentContent.

    Handles both the simple string form and the list-of-blocks form used for
    multimodal and provider-specific content.
    """
    result: list[AgentContent] = []

    if isinstance(content, str) and content:
        result.append(TextContent(text=content))
    elif isinstance(content, list):
        for block in content:
            if not isinstance(block, dict):
                continue

            converted = await _convert_content_block(block, upload)
            if converted is not None:
                result.append(converted)

    return result


async def _convert_content_block(
    block: dict[str, Any], upload: Uploader | None = None
) -> AgentContent | None:
    block_type = block.get("type", "")

    if block_type == "text":
        text = block.get("text", "")
        return TextContent(text=text) if text else None

    if block_type in ("image", "audio", "video", "file"):
        return await _convert_media_block(block, upload, fallback_mime=None)

    if block_type == "image_url":
        try:
            url = block["image_url"]["url"]
            detail = block["image_url"].get("detail")
            metadata: dict[str, str] = (
                {"detail": str(detail)} if detail is not None else {}
            )
            return await _convert_data_url(url, upload, metadata)
        except (KeyError, TypeError):
            return TextContent(text="[image_url: malformed block]")

    return None


async def _convert_data_url(
    url: str, upload: Uploader | None, metadata: dict[str, str]
) -> ResourceContent:
    """Convert an image_url URL to ResourceContent, uploading data: URIs when possible."""
    uri = url

    if url.startswith("data:") and upload is not None:
        try:
            header, data = url.removeprefix("data:").split(",", 1)
            parts = header.split(";")
            mime = parts[0] or "text/plain"
            if "base64" in parts[1:]:
                content = base64.b64decode(data)
            else:
                content = unquote_to_bytes(data)
            uri = await upload(content, mime) or url
        except (ValueError, base64.binascii.Error):
            pass

    return ResourceContent(
        resource_id=uuid4(),
        resource=Resource(uri=uri, metadata=metadata),
    )


async def _convert_media_block(
    block: dict[str, Any],
    upload: Uploader | None,
    fallback_mime: str | None,
) -> AgentContent | None:
    """Convert image/audio/video/file content blocks to ResourceContent.

    For base64 blocks, attempts upload via the provided callable first.
    Falls back to a data: URI if upload is not provided or returns None.
    """
    metadata: dict[str, str] = {}
    for key in ("mime_type", "file_id", "id", "index"):
        val = block.get(key)
        if val is not None:
            metadata[key] = str(val)

    url = block.get("url")
    if url:
        return ResourceContent(
            resource_id=uuid4(),
            resource=Resource(uri=url, metadata=metadata),
        )

    b64 = block.get("base64")
    if b64:
        mime = metadata.get("mime_type") or fallback_mime or "application/octet-stream"
        metadata["mime_type"] = mime

        uri = await upload(base64.b64decode(b64), mime) if upload else None
        if uri is None:
            uri = f"data:{mime};base64,{b64}"

        return ResourceContent(
            resource_id=uuid4(),
            resource=Resource(uri=uri, metadata=metadata),
        )

    return None
