# MCP Server Adapter

The MCP Server Adapter integrates Model Control Protocol (MCP) servers and uAgents, allowing MCP Servers to be easily discoverable by other agents on the Agentverse MArketplace.

## Overview

The MCP Server Adapter provides:

- A bridge between MCP servers and uAgents
- Support for the Chat Protocol to enable conversations with ASI:One
- Tool discovery and execution through the MCP protocol

## Installation

```bash
# Install with MCP support
pip install "uagents-adapter[mcp]"
```

## Usage

Using the MCP Server Adapter involves two main components:

1. Creating a FastMCP server that implements the required interface
2. Setting up a uAgent that uses the MCPServerAdapter to connect to the MCP server

### Step 1: Create a FastMCP Server

First, create a FastMCP server implementation in a `server.py` file. The server should expose tools that can be discovered and called by AI models.

> **Important**: When creating MCP tools, always include detailed docstrings using triple quotes (`"""`) to describe what each tool in the MCP Server as these descriptions play a critical role.

Here's an example `server.py` that implements a weather service:

```python
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Create a FastMCP server instance
mcp = FastMCP("weather")

NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

async def make_nws_request(url: str) -> dict[str, Any] | None:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

def format_alert(feature: dict) -> str:
    props = feature["properties"]
    return f""" Event: {props.get('event', 'Unknown')} Area: {props.get('areaDesc', 'Unknown')} Severity: {props.get('severity', 'Unknown')} Description: {props.get('description', 'No description available')} Instructions: {props.get('instruction', 'No specific instructions provided')}"""

@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state."""

    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."
    if not data["features"]:
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location."""
    
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:
        forecast = f"""{period['name']}: Temperature: {period['temperature']}°{period['temperatureUnit']} Wind: {period['windSpeed']} {period['windDirection']} Forecast: {period['detailedForecast']}"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
```

### Step 2: Create a uAgent with MCPServerAdapter

Next, create an `agent.py` file that imports the MCP server instance and uses it with the MCPServerAdapter:

```python
from uagents import Agent
from uagents_adapter import MCPServerAdapter
from server import mcp
import os

# Create an MCP adapter with your MCP server
mcp_adapter = MCPServerAdapter(
    mcp_server=mcp, 
    asi1_api_key="your-asi1-api-key",  # Replace with your actual API key
    model="asi1-fast"  # Options: asi1-mini, asi1-extended, asi1-fast
)

# Create a uAgent
agent = Agent()

# Include protocols from the adapter
for protocol in mcp_adapter.protocols:
    agent.include(protocol, publish_manifest=True)

if __name__ == "__main__":
    # Run the MCP adapter with the agent
    mcp_adapter.run(agent)
```

### Step 3: Run Your Agent


## Troubleshooting

### Common Issues

1. **Tool execution failures**: Ensure your MCP server properly implements the required methods and handles errors gracefully.
2. **Connection issues**: Ensure your ASI:One API key is valid.

