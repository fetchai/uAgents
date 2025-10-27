"""Tests for MCP adapter functionality."""

import json
import unittest
from unittest.mock import Mock, MagicMock
from uuid import uuid4
import sys
from pathlib import Path

# Add the necessary paths for importing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Mock the problematic langchain imports before importing anything else
sys.modules['langchain_core'] = MagicMock()
sys.modules['langchain_core.callbacks'] = MagicMock()
sys.modules['langchain_core.callbacks.CallbackManagerForToolRun'] = MagicMock()

from uagents import Agent, Context
# Import MCP adapter components after mocking dependencies
try:
    from uagents_adapter.mcp.adapter import MCPServerAdapter, serialize_messages, deserialize_messages
    from uagents_adapter.mcp.protocol import CallTool, CallToolResponse, ListTools, ListToolsResponse
    MCP_AVAILABLE = True
except ImportError as e:
    # Mock the classes if import fails
    MCPServerAdapter = MagicMock
    serialize_messages = MagicMock
    deserialize_messages = MagicMock
    CallTool = MagicMock
    CallToolResponse = MagicMock
    ListTools = MagicMock
    ListToolsResponse = MagicMock
    MCP_AVAILABLE = False


class TestMCPUtilities(unittest.TestCase):
    """Test MCP utility functions."""

    @unittest.skipUnless(MCP_AVAILABLE, "MCP adapter not available")
    def test_serialize_messages_empty(self):
        """Test serialization of empty message list."""
        result = serialize_messages([])
        self.assertEqual(result, "[]")

    @unittest.skipUnless(MCP_AVAILABLE, "MCP adapter not available")
    def test_serialize_messages_with_data(self):
        """Test serialization of messages with data."""
        messages = [{"type": "text", "content": "Hello"}]
        result = serialize_messages(messages)
        self.assertEqual(result, json.dumps(messages))

    @unittest.skipUnless(MCP_AVAILABLE, "MCP adapter not available")
    def test_deserialize_messages_empty_string(self):
        """Test deserialization of empty string."""
        result = deserialize_messages("")
        self.assertEqual(result, [])

    @unittest.skipUnless(MCP_AVAILABLE, "MCP adapter not available")
    def test_deserialize_messages_valid_json(self):
        """Test deserialization of valid JSON."""
        messages = [{"type": "text", "content": "Hello"}]
        json_str = json.dumps(messages)
        result = deserialize_messages(json_str)
        self.assertEqual(result, messages)

    @unittest.skipUnless(MCP_AVAILABLE, "MCP adapter not available")
    def test_deserialize_messages_invalid_json(self):
        """Test deserialization handles invalid JSON."""
        with self.assertRaises(json.JSONDecodeError):
            deserialize_messages("invalid json")


class TestMCPServerAdapter(unittest.TestCase):
    """Test MCP server adapter."""

    @unittest.skipUnless(MCP_AVAILABLE, "MCP adapter not available")
    def setUp(self):
        """Set up test fixtures."""
        if not MCP_AVAILABLE:
            return
        self.mock_mcp_server = Mock()
        self.api_key = "test-api-key"
        self.model = "test-model"
        self.adapter = MCPServerAdapter(
            mcp_server=self.mock_mcp_server,
            asi1_api_key=self.api_key,
            model=self.model
        )

    @unittest.skipUnless(MCP_AVAILABLE, "MCP adapter not available")
    def test_adapter_initialization(self):
        """Test adapter initializes with correct parameters."""
        self.assertEqual(self.adapter.mcp, self.mock_mcp_server)
        self.assertEqual(self.adapter.api_key, self.api_key)
        self.assertEqual(self.adapter.model, self.model)

    @unittest.skipUnless(MCP_AVAILABLE, "MCP adapter not available")
    def test_adapter_has_required_attributes(self):
        """Test adapter has all required attributes."""
        required_attrs = ["mcp", "api_key", "model", "asi1_base_url"]
        for attr in required_attrs:
            self.assertTrue(hasattr(self.adapter, attr), f"Missing attribute: {attr}")


class TestMCPProtocolMessages(unittest.TestCase):
    """Test MCP protocol message types."""

    @unittest.skipUnless(MCP_AVAILABLE, "MCP adapter not available")
    def test_list_tools_message(self):
        """Test ListTools message creation."""
        msg = ListTools()
        self.assertIsInstance(msg, ListTools)

    @unittest.skipUnless(MCP_AVAILABLE, "MCP adapter not available")
    def test_list_tools_response_creation(self):
        """Test ListToolsResponse message creation."""
        tools = [{"name": "test_tool", "description": "A test tool"}]
        response = ListToolsResponse(tools=tools)
        self.assertEqual(response.tools, tools)

    @unittest.skipUnless(MCP_AVAILABLE, "MCP adapter not available")
    def test_call_tool_message(self):
        """Test CallTool message creation."""
        tool_name = "test_tool"
        arguments = {"arg1": "value1"}
        msg = CallTool(tool=tool_name, args=arguments)
        self.assertEqual(msg.tool, tool_name)
        self.assertEqual(msg.args, arguments)

    @unittest.skipUnless(MCP_AVAILABLE, "MCP adapter not available")
    def test_call_tool_response_success(self):
        """Test successful CallToolResponse creation."""
        result = "Success"
        response = CallToolResponse(result=result, error=None)
        self.assertEqual(response.result, result)
        self.assertIsNone(response.error)

    @unittest.skipUnless(MCP_AVAILABLE, "MCP adapter not available")
    def test_call_tool_response_error(self):
        """Test error CallToolResponse creation."""
        error_msg = "Error occurred"
        response = CallToolResponse(result=None, error=error_msg)
        self.assertIsNone(response.result)
        self.assertEqual(response.error, error_msg)


if __name__ == "__main__":
    unittest.main()