# Testing Guide for uAgents Framework

This guide provides comprehensive information on testing the uAgents framework components, including the new adapter and AI-engine integrations.

## Overview

The uAgents framework includes several testable components:
- Core uAgents functionality
- uAgents adapters (MCP, LangChain, CrewAI)
- AI-Engine integration
- Network and registration features

## Test Structure

```
python/
├── tests/                          # Main test suite
│   ├── test_*.py                   # Core uAgents tests
│   ├── test_adapter_integration.py # New adapter integration tests
│   └── test_new_features_validation.py # Feature validation tests
├── uagents-adapter/tests/          # Adapter-specific tests
│   ├── test_mcp_adapter.py        # MCP adapter tests
│   └── test_common_adapter.py     # Common utilities tests
└── uagents-ai-engine/tests/       # AI-engine specific tests
    └── test_ai_engine_messages.py # Message type tests
```

## Running Tests

### Run All Tests
```bash
cd python/
python -m pytest tests/ -v
```

### Run Specific Test Categories

#### Core uAgents Tests
```bash
python -m pytest tests/test_agent.py tests/test_context.py -v
```

#### Adapter Tests
```bash
python -m pytest tests/test_adapter_integration.py -v
python -m pytest uagents-adapter/tests/ -v
```

#### AI-Engine Tests
```bash
python -m pytest uagents-ai-engine/tests/ -v
```

#### Feature Validation Tests
```bash
python -m pytest tests/test_new_features_validation.py -v
```

### Run Tests with Coverage
```bash
python -m pytest tests/ --cov=src/uagents --cov-report=html
```

## Test Categories

### 1. Unit Tests
Test individual components in isolation:
- Message model validation
- Utility function behavior
- Basic agent functionality

### 2. Integration Tests
Test component interactions:
- Adapter integration with core uAgents
- End-to-end message handling
- Protocol compatibility

### 3. Validation Tests
Ensure framework integrity:
- Project structure validation
- Import statement syntax
- Documentation completeness

## Writing New Tests

### Test File Naming
- `test_*.py` for main tests
- `test_*_integration.py` for integration tests
- `test_*_validation.py` for validation tests

### Test Class Structure
```python
import unittest
from unittest.mock import Mock, patch


class TestComponentName(unittest.TestCase):
    """Test ComponentName functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Initialize test data
        pass

    def test_specific_functionality(self):
        """Test specific functionality with descriptive name."""
        # Arrange
        # Act
        # Assert
        pass

    def test_error_handling(self):
        """Test error handling scenarios."""
        pass
```

### Mock External Dependencies
```python
@patch('module.external_dependency')
def test_with_mocked_dependency(self, mock_dependency):
    """Test functionality with mocked external dependency."""
    mock_dependency.return_value = expected_response
    # Test implementation
```

## Best Practices

### 1. Test Isolation
- Each test should be independent
- Use `setUp()` and `tearDown()` for test fixtures
- Mock external dependencies

### 2. Descriptive Names
- Test method names should describe what is being tested
- Use docstrings to explain complex test scenarios

### 3. Comprehensive Coverage
- Test both success and failure scenarios
- Test edge cases and boundary conditions
- Test error handling and validation

### 4. Performance Considerations
- Keep tests fast and focused
- Use mocks for expensive operations
- Group related tests in classes

## Testing New Components

When adding new components to the framework:

1. **Create Component Tests**
   ```bash
   mkdir -p component-name/tests/
   touch component-name/tests/__init__.py
   touch component-name/tests/test_component.py
   ```

2. **Add Integration Tests**
   - Test integration with core uAgents
   - Test message passing and protocol compatibility

3. **Update Validation Tests**
   - Add structure validation for new components
   - Update import validation if needed

4. **Document Test Coverage**
   - Update this guide with new test categories
   - Add examples for component-specific testing

## Continuous Integration

The framework uses GitHub Actions for automated testing:
- Tests run on multiple Python versions (3.10-3.13)
- Coverage reports are generated automatically
- Tests must pass before merging PRs

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure packages are installed: `pip install -e .`
   - Check PYTHONPATH for development setup

2. **Async Test Issues**
   - Use `pytest-asyncio` for async test support
   - Mark async tests with `@pytest.mark.asyncio`

3. **Mock Configuration**
   - Patch at the right level (where imported, not defined)
   - Use `autospec=True` for better mock validation

### Getting Help

- Check existing tests for examples
- Review test failures for detailed error messages
- Consult the main documentation for component behavior

## Contributing

When contributing tests:
1. Follow the existing test structure
2. Ensure tests are well-documented
3. Add integration tests for new features
4. Update this guide if needed
5. Run the full test suite before submitting