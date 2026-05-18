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

from typing import Any
from uuid import uuid4

from uagents_core.contrib.protocols.chat import (
    AgentContent,
    Resource,
    ResourceContent,
    TextContent,
)


def extract_ai_content(data: dict[str, Any]) -> list[AgentContent]:
    """Extract AgentContent from all AI messages in a /runs/wait response.

    Expects ``data["messages"]`` — the MessagesState convention for /runs/wait.
    Processes every AI message in order.
    """
    messages = data.get("messages")
    if not isinstance(messages, list):
        messages = []

    content: list[AgentContent] = []
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        if msg.get("type") != "ai":
            continue

        content.extend(message_content_to_agent_content(msg.get("content", "")))

    return content


def message_content_to_agent_content(
    content: str | list[dict[str, Any]],
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

            converted = _convert_content_block(block)
            if converted is not None:
                result.append(converted)

    return result


def _convert_content_block(block: dict[str, Any]) -> AgentContent | None:
    block_type = block.get("type", "")

    if block_type == "text":
        text = block.get("text", "")
        return TextContent(text=text) if text else None

    if block_type == "image":
        return _convert_media_block(block, fallback_mime=None)

    if block_type == "image_url":
        try:
            url = block["image_url"]["url"]
            detail = block["image_url"].get("detail")
            metadata: dict[str, str] = (
                {"detail": str(detail)} if detail is not None else {}
            )
        except (KeyError, TypeError):
            return None
        return ResourceContent(
            resource_id=uuid4(),
            resource=Resource(uri=url, metadata=metadata),
        )

    if block_type in ("audio", "video", "file"):
        return _convert_media_block(block, fallback_mime=None)

    return None


def _convert_media_block(
    block: dict[str, Any],
    fallback_mime: str | None,
) -> AgentContent | None:
    """Convert image/audio/video/file content blocks to ResourceContent.

    Supports both URL-based and base64-based blocks. For base64 blocks, a
    data: URI is constructed inline (same approach as A2A FileWithBytes).
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
        uri = f"data:{mime};base64,{b64}"
        return ResourceContent(
            resource_id=uuid4(),
            resource=Resource(uri=uri, metadata=metadata),
        )

    return None
