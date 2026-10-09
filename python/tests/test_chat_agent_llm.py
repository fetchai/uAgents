"""Tests for the chat_agent LLM final-reply handling.

The final-reply turn (``LLM.complete``) runs without tools. A model that still
attempts a tool call comes back with empty content — the engine swallows the
call because no tools are declared. These tests pin the recovery contract:
one text-only nudge retry, then a visible fallback message. Never an empty
string, which would end the user's turn silently.
"""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from uagents import Model
from uagents.experimental.chat_agent.llm import (
    EMPTY_FINAL_REPLY_MESSAGE,
    EMPTY_FINAL_REPLY_NUDGE,
    LLM,
    LLMConfig,
    LLMParams,
)
from uagents.experimental.chat_agent.tools import Tool


class _Lookup(Model):
    """Look something up."""

    query: str


def _tool() -> Tool:
    return Tool(
        name="Lookup",
        description="Look something up",
        model_cls=_Lookup,
        handler=lambda *args, **kwargs: None,  # never invoked in these tests
    )


def _fake_response(text: str | None) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=text))]
    )


def _llm() -> LLM:
    config = LLMConfig(
        provider="openai",
        model="asi1-mini",
        url="https://example.test/v1",
        parameters=LLMParams(),
        api_key="test-key",
    )
    return LLM(config=config, tools={"Lookup": _tool()}, instructions=None)


def _final_messages() -> list[dict]:
    return [
        {"role": "system", "content": "produce the final reply"},
        {"role": "user", "content": "status of BTC?"},
        {"role": "assistant", "content": "", "tool_calls": []},
        {"role": "tool", "tool_call_id": "call-1", "content": "[]"},
    ]


class TestCompleteFinalReply(unittest.IsolatedAsyncioTestCase):
    async def test_plain_text_returned_without_retry(self):
        llm = _llm()
        with patch(
            "uagents.experimental.chat_agent.llm.acompletion",
            return_value=_fake_response("BTC is at 36.4, signals mixed."),
        ) as mocked:
            text = await llm.complete(_final_messages())

        self.assertEqual(text, "BTC is at 36.4, signals mixed.")
        self.assertEqual(mocked.await_count, 1)

    async def test_empty_reply_retried_once_with_nudge(self):
        llm = _llm()
        responses = [
            _fake_response(""),
            _fake_response("BTC is at 36.4, signals mixed."),
        ]

        async def fake_completion(**kwargs):
            return responses.pop(0)

        with patch(
            "uagents.experimental.chat_agent.llm.acompletion",
            side_effect=fake_completion,
        ) as mocked:
            text = await llm.complete(_final_messages())

        self.assertEqual(text, "BTC is at 36.4, signals mixed.")
        self.assertEqual(mocked.await_count, 2)
        # The retry carries the original messages plus the nudge.
        first_messages = mocked.await_args_list[0].kwargs["messages"]
        retry_messages = mocked.await_args_list[1].kwargs["messages"]
        self.assertEqual(first_messages, _final_messages())
        self.assertEqual(len(retry_messages), len(first_messages) + 1)
        self.assertEqual(retry_messages[-1]["role"], "user")
        self.assertEqual(retry_messages[-1]["content"], EMPTY_FINAL_REPLY_NUDGE)

    async def test_persistently_empty_reply_returns_fallback_message(self):
        llm = _llm()

        async def empty_completion(**kwargs):
            return _fake_response("")

        with patch(
            "uagents.experimental.chat_agent.llm.acompletion",
            side_effect=empty_completion,
        ) as mocked:
            text = await llm.complete(_final_messages())

        self.assertEqual(text, EMPTY_FINAL_REPLY_MESSAGE)
        self.assertEqual(mocked.await_count, 2)

    async def test_none_content_is_treated_as_empty(self):
        llm = _llm()
        responses = [
            _fake_response(None),
            _fake_response("Recovered answer."),
        ]

        async def fake_completion(**kwargs):
            return responses.pop(0)

        with patch(
            "uagents.experimental.chat_agent.llm.acompletion",
            side_effect=fake_completion,
        ):
            text = await llm.complete(_final_messages())

        self.assertEqual(text, "Recovered answer.")

    async def test_marker_reply_after_retry_is_sanitized(self):
        llm = _llm()
        responses = [
            _fake_response(""),
            _fake_response("<tool_call>answer metadata"),
        ]

        async def fake_completion(**kwargs):
            return responses.pop(0)

        with patch(
            "uagents.experimental.chat_agent.llm.acompletion",
            side_effect=fake_completion,
        ):
            text = await llm.complete(_final_messages())

        self.assertEqual(
            text,
            "Sorry, I had trouble processing that request. "
            "Could you try rephrasing it?",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
