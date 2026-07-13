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

1. Install [uv](https://docs.astral.sh/uv/getting-started/) (or `pip install uv`).

2. Install dependencies:
   ```bash
   cd python
   uv sync
   uv run pre-commit install
   ```

3. Run tests:
   ```bash
   uv run pytest
   ```

4. Format and lint:
   ```bash
   uv run ruff check --fix && uv run ruff format
   ```

## Telemetry (Agentverse events)

Native uAgents that are registered on Agentverse automatically report telemetry
events to the Agentverse events API so their activity is visible on the
Agentverse dashboard. The following events are emitted:

- **start** — when the agent starts up
- **stop** — when the agent shuts down
- **messages** — when a message is received or sent
- **errors** — when a message handler raises an exception

Telemetry is gated by two conditions:

1. The `report_events` constructor flag (on by default), and
2. A registration check performed at startup (`GET /v2/agents/{address}`).

Events are only sent when both conditions hold, so unregistered agents never
report. Telemetry is strictly best-effort: any failure to send events is
swallowed and never interferes with agent logic.

Disable it explicitly with:

```python
from uagents import Agent

agent = Agent(name="alice", report_events=False)
```

The event schema and dispatch/registration helpers live in
[`uagents-core`](uagents-core/uagents_core/events.py); the lifecycle wiring
lives in the [`uagents`](src/uagents/agent.py) runtime.

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
