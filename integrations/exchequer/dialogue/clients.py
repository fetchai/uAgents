"""Client library constants."""

import json
import os

clients = {}

with open(
    os.path.join(os.path.dirname(__file__), "clients.json"), encoding="UTF-8"
) as f:
    clients = json.load(f)

if not clients:
    raise ValueError("No clients found in clients.json")


def get_client(name: str) -> dict:
    """
    Get the client ID and token by name.

    Args:
        name (str): Identifier of the client

    Returns:
        dict: Dict containing the ID and token of an account
    """
    return clients[name]
