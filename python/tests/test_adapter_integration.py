"""Integration tests for uAgents adapter components.

These tests verify that the adapter components can be imported and 
basic functionality works as expected.
"""

import unittest
import sys
import importlib.util
from pathlib import Path
from unittest.mock import MagicMock


class TestAdapterIntegration(unittest.TestCase):
    """Test adapter component integration."""

    def test_mcp_adapter_structure(self):
        """Test that MCP adapter has the expected structure."""
        adapter_path = Path(__file__).parent.parent / "uagents-adapter" / "src"
        self.assertTrue(adapter_path.exists(), "Adapter source directory should exist")
        
        mcp_path = adapter_path / "uagents_adapter" / "mcp"
        self.assertTrue(mcp_path.exists(), "MCP module directory should exist")
        
        # Test that key files exist
        adapter_file = mcp_path / "adapter.py"
        protocol_file = mcp_path / "protocol.py"
        
        self.assertTrue(adapter_file.exists(), "MCP adapter.py should exist")
        self.assertTrue(protocol_file.exists(), "MCP protocol.py should exist")
        
        # Test that files contain expected functions/classes
        adapter_content = adapter_file.read_text()
        self.assertIn("MCPServerAdapter", adapter_content)
        self.assertIn("serialize_messages", adapter_content)
        self.assertIn("deserialize_messages", adapter_content)
        
        protocol_content = protocol_file.read_text()
        self.assertIn("CallTool", protocol_content)
        self.assertIn("ListTools", protocol_content)

    def test_ai_engine_structure(self):
        """Test that AI engine has the expected structure."""
        ai_engine_path = Path(__file__).parent.parent / "uagents-ai-engine" / "src"
        self.assertTrue(ai_engine_path.exists(), "AI engine source directory should exist")
        
        engine_path = ai_engine_path / "ai_engine"
        self.assertTrue(engine_path.exists(), "AI engine module directory should exist")
        
        # Test that key files exist
        messages_file = engine_path / "messages.py"
        types_file = engine_path / "types.py"
        
        self.assertTrue(messages_file.exists(), "AI engine messages.py should exist")
        self.assertTrue(types_file.exists(), "AI engine types.py should exist")
        
        # Test that files contain expected classes
        messages_content = messages_file.read_text()
        self.assertIn("KeyValue", messages_content)
        self.assertIn("AgentJSON", messages_content)
        self.assertIn("BaseMessage", messages_content)
        
        types_content = types_file.read_text()
        self.assertIn("UAgentResponse", types_content)
        self.assertIn("UAgentResponseType", types_content)

    def test_adapter_component_structure(self):
        """Test that all expected adapter components exist."""
        adapter_path = Path(__file__).parent.parent / "uagents-adapter" / "src" / "uagents_adapter"
        self.assertTrue(adapter_path.exists(), "uagents_adapter package should exist")
        
        expected_components = ["mcp", "langchain", "crewai", "common"]
        for component in expected_components:
            component_path = adapter_path / component
            self.assertTrue(component_path.exists(), f"{component} component should exist")
            
            # Each component should have an __init__.py
            init_file = component_path / "__init__.py"
            self.assertTrue(init_file.exists(), f"{component} should have __init__.py")

    def test_core_uagents_functionality(self):
        """Test that core uAgents functionality still works."""
        try:
            from uagents import Agent, Model
            from uagents_core.types import AgentInfo
            
            # Test basic agent creation
            agent = Agent(name="test_agent", seed="test_seed_123")
            self.assertIsNotNone(agent.address)
            self.assertEqual(agent.name, "test_agent")
            
            # Test basic model functionality
            class TestMessage(Model):
                content: str
            
            msg = TestMessage(content="Hello, World!")
            self.assertEqual(msg.content, "Hello, World!")
            
        except Exception as e:
            self.fail(f"Core uAgents functionality test failed: {e}")

    def test_module_imports_safe(self):
        """Test that modules can be imported safely without errors."""
        # Test AI engine imports
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent / "uagents-ai-engine" / "src"))
            
            # These should work
            import ai_engine
            from ai_engine import types, messages
            from ai_engine.types import UAgentResponseType, UAgentResponse
            from ai_engine.messages import KeyValue, AgentJSON
            
            # Test enum values
            self.assertEqual(UAgentResponseType.FINAL.value, "final")
            
            # Test model creation
            response = UAgentResponse(type=UAgentResponseType.FINAL)
            self.assertEqual(response.type, UAgentResponseType.FINAL)
            self.assertEqual(response.version, "v1")
            
        except Exception as e:
            self.fail(f"AI engine import test failed: {e}")


if __name__ == "__main__":
    unittest.main()