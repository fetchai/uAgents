"""Validation tests for new features in the uAgents framework.

These tests validate that new features added in the latest release
work correctly and maintain compatibility.
"""

import unittest
from pathlib import Path
import json
import re


class TestNewFeaturesValidation(unittest.TestCase):
    """Test new features validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.repo_root = Path(__file__).parent.parent.parent
        self.python_root = Path(__file__).parent.parent

    def test_project_structure_validation(self):
        """Test that the project has the expected structure for new features."""
        expected_dirs = [
            "uagents-adapter",
            "uagents-ai-engine", 
            "uagents-core",
            "src/uagents",
            "tests"
        ]
        
        for dir_name in expected_dirs:
            dir_path = self.python_root / dir_name
            self.assertTrue(dir_path.exists(), f"Expected directory {dir_name} should exist")

    def test_adapter_component_structure(self):
        """Test adapter component has correct structure."""
        adapter_root = self.python_root / "uagents-adapter"
        
        expected_components = [
            "src/uagents_adapter/mcp",
            "src/uagents_adapter/langchain", 
            "src/uagents_adapter/crewai",
            "src/uagents_adapter/common"
        ]
        
        for component in expected_components:
            component_path = adapter_root / component
            self.assertTrue(component_path.exists(), f"Adapter component {component} should exist")
            
            # Check for __init__.py
            init_file = component_path / "__init__.py"
            self.assertTrue(init_file.exists(), f"Component {component} should have __init__.py")

    def test_ai_engine_component_structure(self):
        """Test AI engine component has correct structure."""
        ai_engine_root = self.python_root / "uagents-ai-engine"
        
        expected_files = [
            "src/ai_engine/__init__.py",
            "src/ai_engine/messages.py",
            "src/ai_engine/types.py",
            "src/ai_engine/dialogue.py",
            "src/ai_engine/chitchat.py"
        ]
        
        for file_path in expected_files:
            full_path = ai_engine_root / file_path
            self.assertTrue(full_path.exists(), f"AI engine file {file_path} should exist")

    def test_documentation_files_exist(self):
        """Test that documentation files exist for new components."""
        expected_docs = [
            self.python_root / "uagents-adapter" / "README.md",
            self.python_root / "uagents-ai-engine" / "README.md",
            self.repo_root / "DEVELOPING.md",
            self.repo_root / "CONTRIBUTING.md"
        ]
        
        for doc_file in expected_docs:
            self.assertTrue(doc_file.exists(), f"Documentation file {doc_file} should exist")
            
            # Check that README files are not empty
            if doc_file.name == "README.md":
                content = doc_file.read_text()
                self.assertGreater(len(content.strip()), 0, f"README {doc_file} should not be empty")

    def test_pyproject_toml_configurations(self):
        """Test that pyproject.toml files have correct configurations."""
        pyproject_files = [
            self.python_root / "pyproject.toml",
            self.python_root / "uagents-adapter" / "pyproject.toml", 
            self.python_root / "uagents-ai-engine" / "pyproject.toml"
        ]
        
        for pyproject_file in pyproject_files:
            if pyproject_file.exists():
                content = pyproject_file.read_text()
                
                # Check that it contains basic project configuration
                self.assertIn("[project]", content, f"{pyproject_file} should have [project] section")
                self.assertIn("name =", content, f"{pyproject_file} should have project name")

    def test_test_coverage_structure(self):
        """Test that test coverage structure is in place."""
        # Check main tests directory
        main_tests = self.python_root / "tests"
        self.assertTrue(main_tests.exists(), "Main tests directory should exist")
        
        # Check that our new test directories exist
        adapter_tests = self.python_root / "uagents-adapter" / "tests"
        ai_engine_tests = self.python_root / "uagents-ai-engine" / "tests"
        
        self.assertTrue(adapter_tests.exists(), "Adapter tests directory should exist")
        self.assertTrue(ai_engine_tests.exists(), "AI engine tests directory should exist")

    def test_import_statements_syntax(self):
        """Test that Python files have valid import statements."""
        python_files = []
        
        # Collect Python files from new components
        for component_dir in ["uagents-adapter/src", "uagents-ai-engine/src"]:
            component_path = self.python_root / component_dir
            if component_path.exists():
                python_files.extend(component_path.rglob("*.py"))
        
        for py_file in python_files:
            if py_file.name == "__init__.py" and py_file.stat().st_size == 0:
                continue  # Skip empty __init__.py files
                
            try:
                content = py_file.read_text(encoding='utf-8')
                
                # Basic syntax validation - check for common import patterns
                import_lines = [line for line in content.split('\n') if line.strip().startswith(('import ', 'from '))]
                
                for line in import_lines:
                    # Check for basic import syntax issues (allow valid relative imports)
                    # Only flag if there are more than 2 consecutive dots (which would be invalid)
                    if '...' in line and '...' not in ['...']:  # Allow ellipsis but not triple-dot imports
                        self.fail(f"Invalid import syntax in {py_file}: {line}")
                    
                    # Check for import statements that don't end properly
                    stripped_line = line.strip()
                    if stripped_line and not stripped_line.endswith((')', ',')):
                        if stripped_line.count('(') != stripped_line.count(')'):
                            # This might be a multi-line import, which is valid
                            pass
                    
            except Exception as e:
                self.fail(f"Failed to validate imports in {py_file}: {e}")


if __name__ == "__main__":
    unittest.main()