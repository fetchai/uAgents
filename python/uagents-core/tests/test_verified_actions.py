"""Tests for uagents_core.contrib.protocols.chat.verified_actions."""

import json

from uagents_core.contrib.protocols.chat import MetadataContent
from uagents_core.contrib.protocols.chat.verified_actions import (
    META_VERIFIED_ACTIONS_DATA,
    META_VERIFIED_ACTIONS_VERSION,
    VERIFIED_ACTIONS_VERSION,
    IntegrationAction,
    LlmAction,
    McpAction,
    UnknownAction,
    VerifiedActions,
    WebAction,
    create_verified_actions_content,
    extract_verified_actions,
    validate_tool_action,
)


def _sample_data() -> VerifiedActions:
    return VerifiedActions(
        session_id="session-1",
        actions=[
            WebAction(
                reference_id="ref-1",
                url="https://api.example.com/data",
                method="GET",
                status_code=200,
                status="success",
                duration_ms=120,
            ),
            LlmAction(
                reference_id="ref-2",
                api_url="https://api.openai.com/v1/chat/completions",
                model="gpt-4o",
                input_tokens=500,
                output_tokens=150,
                status="success",
                duration_ms=2400,
            ),
        ],
    )


class TestRoundTrip:
    def test_create_and_extract(self):
        data = _sample_data()
        content = create_verified_actions_content(data)

        assert content.type == "metadata"
        assert (
            content.metadata[META_VERIFIED_ACTIONS_VERSION] == VERIFIED_ACTIONS_VERSION
        )

        extracted = extract_verified_actions(content)
        assert extracted is not None
        assert extracted == data

    def test_all_tool_types(self):
        data = VerifiedActions(
            session_id="session-2",
            actions=[
                WebAction(
                    reference_id="r1",
                    url="https://x.com",
                    method="POST",
                    status="success",
                    duration_ms=50,
                ),
                LlmAction(
                    reference_id="r2",
                    api_url="https://llm.example.com",
                    model="m1",
                    status="success",
                    duration_ms=100,
                ),
                McpAction(
                    reference_id="r3",
                    server_url="https://mcp.example.com",
                    tool_name="search",
                    status="success",
                    duration_ms=200,
                ),
                IntegrationAction(
                    reference_id="r4",
                    integration="google_calendar",
                    tool_name="google_calendar-event-create",
                    status="error",
                    error="TimeoutError: request timed out",
                    duration_ms=5000,
                ),
            ],
        )
        content = create_verified_actions_content(data)
        extracted = extract_verified_actions(content)
        assert extracted == data

    def test_type_discriminator(self):
        data = _sample_data()
        content = create_verified_actions_content(data)
        extracted = extract_verified_actions(content)

        assert isinstance(extracted.actions[0], WebAction)
        assert isinstance(extracted.actions[1], LlmAction)


class TestForwardCompatibility:
    def test_unknown_fields_ignored(self):
        """Newer version adds fields — old code still parses successfully."""
        data = _sample_data()
        payload = json.loads(data.model_dump_json())
        payload["new_v2_field"] = "future"
        payload["actions"][0]["new_web_field"] = "extra"

        content = MetadataContent(
            metadata={
                META_VERIFIED_ACTIONS_VERSION: "2",
                META_VERIFIED_ACTIONS_DATA: json.dumps(payload),
            }
        )
        extracted = extract_verified_actions(content)
        assert extracted is not None
        assert extracted.session_id == "session-1"
        assert len(extracted.actions) == 2
        assert extracted.actions[0].url == "https://api.example.com/data"

    def test_version_available_for_comparison(self):
        """Consumer can read producer version from metadata for upgrade nudges."""
        content = MetadataContent(
            metadata={
                META_VERIFIED_ACTIONS_VERSION: "3",
                META_VERIFIED_ACTIONS_DATA: _sample_data().model_dump_json(),
            }
        )
        producer_version = content.metadata[META_VERIFIED_ACTIONS_VERSION]
        assert producer_version != VERIFIED_ACTIONS_VERSION


class TestExtractReturnsNone:
    def test_missing_version_key(self):
        content = MetadataContent(metadata={"unrelated_key": "value"})
        assert extract_verified_actions(content) is None

    def test_missing_data_payload(self):
        content = MetadataContent(metadata={META_VERIFIED_ACTIONS_VERSION: "1"})
        assert extract_verified_actions(content) is None

    def test_invalid_json(self):
        content = MetadataContent(
            metadata={
                META_VERIFIED_ACTIONS_VERSION: "1",
                META_VERIFIED_ACTIONS_DATA: "not-json",
            }
        )
        assert extract_verified_actions(content) is None

    def test_incompatible_schema(self):
        content = MetadataContent(
            metadata={
                META_VERIFIED_ACTIONS_VERSION: "99",
                META_VERIFIED_ACTIONS_DATA: json.dumps({"completely": "different"}),
            }
        )
        assert extract_verified_actions(content) is None


class TestValidateToolAction:
    def test_valid_dict(self):
        raw = {
            "type": "mcp",
            "reference_id": "ref-1",
            "server_url": "https://mcp.example.com",
            "tool_name": "search",
            "status": "success",
            "duration_ms": 890,
        }
        action = validate_tool_action(raw)
        assert action is not None
        assert isinstance(action, McpAction)
        assert action.tool_name == "search"

    def test_invalid_dict_returns_unknown_action(self):
        assert validate_tool_action({"bad": "data"}) == UnknownAction()

    def test_missing_required_field(self):
        raw = {
            "type": "web",
            "reference_id": "ref-1",
            "url": "https://x.com",
            "method": "GET",
            "status": "success",
            # missing duration_ms
        }
        assert validate_tool_action(raw) == UnknownAction()

    def test_unknown_type_returns_unknown_action(self):
        raw = {
            "type": "blockchain",
            "reference_id": "ref-1",
            "status": "success",
            "duration_ms": 100,
        }
        assert validate_tool_action(raw) == UnknownAction()
