"""Agent's Setup."""

import requests
from cosmpy.crypto.address import Address

from uagents import Agent
from uagents.config import REGISTRATION_FEE, get_logger
from uagents.network import get_ledger, get_faucet

LOGGER = get_logger("setup")


def fund_agent_if_low(wallet_address: str):
    """
    Checks the agent's wallet balance and adds funds if it's below the registration fee.

    Args:
        wallet_address (str): The wallet address of the agent.

    Returns:
        None
    """
    ledger = get_ledger()
    faucet = get_faucet()

    agent_balance = ledger.query_bank_balance(Address(wallet_address))

    if agent_balance < REGISTRATION_FEE:
        # Add tokens to agent's wallet
        LOGGER.info("Adding funds to agent...")
        faucet.get_wealth(wallet_address)
        LOGGER.info("Adding funds to agent...complete")


def register_agent_with_mailbox(agent: Agent, email: str):
    """
    Registers the agent on a mailbox server using the provided email.

    Args:
        agent (Agent): The agent object to be registered.
        email (str): The email address associated with the agent.

    Returns:
        None
    """
    mailbox = agent.mailbox
    register_url = f"{mailbox['http_prefix']}://{mailbox['base_url']}/v1/auth/register"
    resp = requests.post(
        register_url,
        json={"email": email, "agent_address": agent.address},
        timeout=15,
    )
    if resp.status_code == 200:
        LOGGER.info("Registered agent on mailbox server")
        mailbox["api_key"] = resp.json()["api_key"]
    else:
        LOGGER.exception("Failed to register agent on mailbox server")
