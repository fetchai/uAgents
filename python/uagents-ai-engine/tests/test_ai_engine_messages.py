"""Tests for AI-Engine message types and functionality."""

import unittest
from datetime import datetime, timezone
from uuid import uuid4

from ai_engine.messages import KeyValue as MessagesKeyValue, AgentJSON
from ai_engine.types import KeyValue, UAgentResponse, UAgentResponseType as ResponseType


class TestKeyValue(unittest.TestCase):
    """Test KeyValue models from both messages and types."""

    def test_messages_key_value_creation_string_key(self):
        """Test KeyValue creation with string key from messages module."""
        kv = MessagesKeyValue(key="test_key", value="test_value")
        self.assertEqual(kv.key, "test_key")
        self.assertEqual(kv.value, "test_value")

    def test_messages_key_value_creation_int_key(self):
        """Test KeyValue creation with integer key from messages module."""
        kv = MessagesKeyValue(key=42, value="test_value")
        self.assertEqual(kv.key, 42)
        self.assertEqual(kv.value, "test_value")

    def test_types_key_value_creation(self):
        """Test KeyValue creation from types module (only string keys)."""
        kv = KeyValue(key="test_key", value="test_value")
        self.assertEqual(kv.key, "test_key")
        self.assertEqual(kv.value, "test_value")


class TestAgentJSON(unittest.TestCase):
    """Test AgentJSON model."""

    def test_agent_json_creation(self):
        """Test AgentJSON creation with required fields."""
        agent_json = AgentJSON(type="text")
        self.assertEqual(agent_json.type, "text")

    def test_agent_json_with_options_type(self):
        """Test AgentJSON creation with options type."""
        agent_json = AgentJSON(type="options")
        self.assertEqual(agent_json.type, "options")

    def test_agent_json_with_date_type(self):
        """Test AgentJSON creation with date type."""
        agent_json = AgentJSON(type="date")
        self.assertEqual(agent_json.type, "date")


class TestUAgentResponseType(unittest.TestCase):
    """Test UAgentResponseType enum."""

    def test_response_type_values(self):
        """Test that all expected response type values exist."""
        # Test that we can access the enum values
        self.assertTrue(hasattr(ResponseType, 'FINAL'))
        self.assertTrue(hasattr(ResponseType, 'ERROR'))
        self.assertTrue(hasattr(ResponseType, 'VALIDATION_ERROR'))
        self.assertTrue(hasattr(ResponseType, 'SELECT_FROM_OPTIONS'))
        self.assertTrue(hasattr(ResponseType, 'FINAL_OPTIONS'))

    def test_response_type_string_values(self):
        """Test the string values of response types."""
        self.assertEqual(ResponseType.FINAL.value, "final")
        self.assertEqual(ResponseType.ERROR.value, "error")
        self.assertEqual(ResponseType.VALIDATION_ERROR.value, "validation_error")
        self.assertEqual(ResponseType.SELECT_FROM_OPTIONS.value, "select_from_options")
        self.assertEqual(ResponseType.FINAL_OPTIONS.value, "final_options")


class TestUAgentResponse(unittest.TestCase):
    """Test UAgentResponse model."""

    def test_uagent_response_minimal(self):
        """Test UAgentResponse creation with minimal required fields."""
        response = UAgentResponse(
            type=ResponseType.FINAL,
            request_id="test-123",
            agent_address="agent123",
            message="Hello"
        )
        
        self.assertEqual(response.version, "v1")  # Default value
        self.assertEqual(response.type, ResponseType.FINAL)
        self.assertEqual(response.request_id, "test-123")
        self.assertEqual(response.agent_address, "agent123")
        self.assertEqual(response.message, "Hello")

    def test_uagent_response_with_options(self):
        """Test UAgentResponse with options."""
        options = [KeyValue(key="opt1", value="Option 1")]
        response = UAgentResponse(
            type=ResponseType.SELECT_FROM_OPTIONS,
            request_id="test-123",
            agent_address="agent123",
            message="Choose an option",
            options=options
        )
        
        self.assertEqual(response.options, options)

    def test_uagent_response_error_type(self):
        """Test UAgentResponse with error type."""
        response = UAgentResponse(
            type=ResponseType.ERROR,
            request_id="test-123",
            agent_address="agent123",
            message="An error occurred"
        )
        
        self.assertEqual(response.type, ResponseType.ERROR)

    def test_uagent_response_none_values(self):
        """Test UAgentResponse with None values for optional fields."""
        response = UAgentResponse(
            type=ResponseType.FINAL,
            request_id=None,
            agent_address=None,
            message=None
        )
        
        self.assertIsNone(response.request_id)
        self.assertIsNone(response.agent_address)
        self.assertIsNone(response.message)

    def test_uagent_response_with_verbose_fields(self):
        """Test UAgentResponse with verbose message and options."""
        verbose_options = [KeyValue(key="verbose1", value="Verbose Option 1")]
        response = UAgentResponse(
            type=ResponseType.FINAL,
            request_id="test-123",
            agent_address="agent123",
            message="Simple message",
            verbose_message="This is a more detailed verbose message",
            verbose_options=verbose_options
        )
        
        self.assertEqual(response.verbose_message, "This is a more detailed verbose message")
        self.assertEqual(response.verbose_options, verbose_options)


if __name__ == "__main__":
    unittest.main()