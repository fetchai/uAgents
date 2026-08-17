"""Tests for ChatAgent streaming replies."""

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytest.importorskip("litellm")

from uagents_core.contrib.protocols.chat import (
    EndStreamContent,
    StartStreamContent,
    TextContent,
)

from uagents.experimental.chat_agent.llm import LLM, LLMConfig, LLMParams
from uagents.experimental.chat_agent.protocol import ChatProtocol


class _FakeStream:
    def __init__(self, chunks: list[Any]):
        self._chunks = chunks

    def __aiter__(self):
        self._iter = iter(self._chunks)
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


def _chunk(text: str | None) -> Any:
    return SimpleNamespace(
        choices=[SimpleNamespace(delta=SimpleNamespace(content=text))]
    )


@pytest.mark.asyncio
async def test_process_stream_yields_content_deltas():
    llm = LLM(
        config=LLMConfig(
            provider="openai",
            model="test-model",
            url="https://example.test/v1",
            api_key="test-key",
            parameters=LLMParams(),
        ),
        tools={},
    )
    fake = _FakeStream([_chunk("Hel"), _chunk("lo"), _chunk(None)])

    with patch(
        "uagents.experimental.chat_agent.llm.acompletion",
        new_callable=AsyncMock,
        return_value=fake,
    ) as mock_complete:
        deltas = [
            d async for d in llm.process_stream([{"role": "user", "content": "hi"}])
        ]

    assert mock_complete.await_args.kwargs["stream"] is True
    assert deltas == ["Hel", "lo"]


@pytest.mark.asyncio
async def test_send_stream_emits_start_text_end():
    proto = ChatProtocol(
        llm_config=LLMConfig(
            provider="openai",
            model="test-model",
            url="https://example.test/v1",
            api_key="test-key",
            parameters=LLMParams(),
        ),
        tools={},
    )
    sent: list[Any] = []

    async def capture_send(recipient, message, timeout=None):
        sent.append(message)
        return MagicMock()

    ctx = MagicMock()
    ctx.send = AsyncMock(side_effect=capture_send)

    async def fake_stream(_messages):
        yield "A"
        yield "B"

    with patch.object(proto._llm, "process_stream", side_effect=fake_stream):
        await proto.send_stream(
            ctx, "agent1qsender", [{"role": "user", "content": "hi"}]
        )

    assert isinstance(sent[0].content[0], StartStreamContent)
    assert (
        isinstance(sent[1].content[0], TextContent) and sent[1].content[0].text == "A"
    )
    assert (
        isinstance(sent[2].content[0], TextContent) and sent[2].content[0].text == "B"
    )
    assert isinstance(sent[3].content[0], EndStreamContent)
    assert sent[0].content[0].stream_id == sent[3].content[0].stream_id


@pytest.mark.asyncio
async def test_send_reply_non_streaming_sends_single_text():
    proto = ChatProtocol(
        llm_config=LLMConfig(
            provider="openai",
            model="test-model",
            url="https://example.test/v1",
            api_key="test-key",
            parameters=LLMParams(),
            stream=False,
        ),
        tools={},
    )
    sent: list[Any] = []

    async def capture_send(recipient, message, timeout=None):
        sent.append(message)
        return MagicMock()

    ctx = MagicMock()
    ctx.send = AsyncMock(side_effect=capture_send)

    with patch.object(
        proto._llm, "complete", new_callable=AsyncMock, return_value="full reply"
    ) as mock_complete:
        await proto.send_reply(
            ctx, "agent1qsender", [{"role": "user", "content": "hi"}]
        )

    mock_complete.assert_awaited_once()
    assert len(sent) == 1
    assert isinstance(sent[0].content[0], TextContent)
    assert sent[0].content[0].text == "full reply"
    assert not any(isinstance(c, StartStreamContent) for m in sent for c in m.content)
