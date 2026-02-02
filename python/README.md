# uAgents Python Packages

This directory contains the Python packages for the uAgents framework.

## Packages

| Package | Description | PyPI |
|---------|-------------|------|
| **[uagents](src/uagents/)** | Main agent framework with decorators and runtime | [![PyPI](https://img.shields.io/pypi/v/uagents)](https://pypi.org/project/uagents/) |
| **[uagents-core](uagents-core/)** | Core definitions for Agentverse integration | [![PyPI](https://img.shields.io/pypi/v/uagents-core)](https://pypi.org/project/uagents-core/) |
| **[uagents-adapter](uagents-adapter/)** | Adapters for LangChain, CrewAI, MCP | [![PyPI](https://img.shields.io/pypi/v/uagents-adapter)](https://pypi.org/project/uagents-adapter/) |
| **[uagents-ai-engine](uagents-ai-engine/)** | AI Engine integration | [![PyPI](https://img.shields.io/pypi/v/uagents-ai-engine)](https://pypi.org/project/uagents-ai-engine/) |

## Installation

### Full Framework

```bash
pip install uagents
```

### Core Only (for custom integrations)

```bash
pip install uagents-core
```

## Development Setup

1. Install Poetry:
   ```bash
   pip install poetry
   ```

2. Install dependencies:
   ```bash
   cd python
   poetry install
   poetry shell
   pre-commit install
   ```

3. Run tests:
   ```bash
   pytest
   ```

4. Format and lint:
   ```bash
   ruff check --fix && ruff format
   ```

## Documentation

- **[API Documentation](docs/api/)** - Auto-generated API docs
- **[Upgrading Guide](docs/UPGRADING.md)** - Migration between versions
- **[Official Docs](https://uagents.fetch.ai/docs)** - Full documentation

## Version Compatibility

| uagents | uagents-core | Python |
|---------|--------------|--------|
| 0.23.x | >=0.4.0 | 3.10-3.13 |
| 0.22.x | 0.3.x | 3.10-3.12 |

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.
