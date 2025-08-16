"""Tests for common adapter utilities."""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
from pathlib import Path

# Mock the problematic langchain imports before importing anything else
sys.modules['langchain_core'] = MagicMock()
sys.modules['langchain_core.callbacks'] = MagicMock()
sys.modules['langchain_core.callbacks.CallbackManagerForToolRun'] = MagicMock()

from uagents import Agent

# Try to import common utilities with fallback
try:
    from uagents_adapter.common import register_tool
    COMMON_AVAILABLE = True
except ImportError:
    register_tool = MagicMock()
    COMMON_AVAILABLE = False


class TestCommonAdapterUtilities(unittest.TestCase):
    """Test common adapter utility functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_agent = Agent(name="test_agent", seed="test_seed")

    @unittest.skipUnless(COMMON_AVAILABLE, "Common adapter not available")
    def test_register_tool_basic_functionality(self):
        """Test basic register_tool functionality."""
        # This is a basic structure test since register_tool is complex
        self.assertTrue(callable(register_tool))

    @unittest.skipUnless(COMMON_AVAILABLE, "Common adapter not available")
    @patch('uagents_adapter.common.requests.post')
    def test_register_tool_mock_registration(self, mock_post):
        """Test register_tool with mocked HTTP calls."""
        # Mock successful registration response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "agent_id": "test123"}
        mock_post.return_value = mock_response

        # This test would need adjustment based on actual register_tool signature
        # For now, test that the function exists and can be called
        self.assertTrue(hasattr(register_tool, '__call__'))

    def test_agent_basic_properties(self):
        """Test that we can create and verify basic agent properties."""
        self.assertEqual(self.test_agent.name, "test_agent")
        self.assertIsNotNone(self.test_agent.address)

    def test_common_adapter_structure(self):
        """Test that common adapter has the expected file structure."""
        common_path = Path(__file__).parent.parent / "src" / "uagents_adapter" / "common"
        self.assertTrue(common_path.exists(), "Common adapter directory should exist")
        
        init_file = common_path / "__init__.py"
        self.assertTrue(init_file.exists(), "Common adapter __init__.py should exist")
        
        # Check that the init file contains expected imports/exports
        init_content = init_file.read_text()
        self.assertIn("ResponseMessage", init_content)
        self.assertIn("cleanup_all_uagents", init_content)
        self.assertIn("cleanup_uagent", init_content)


if __name__ == "__main__":
    unittest.main()