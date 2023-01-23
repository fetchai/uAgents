import logging
from enum import Enum

logging.basicConfig(level=logging.INFO)


class AgentNetwork(Enum):
    FETCHAI_TESTNET = 1
    FETCHAI_MAINNET = 2


AGENT_PREFIX = "agent"
LEDGER_PREFIX = "fetch"
USER_PREFIX = "user"
CONTRACT_ALMANAC = "fetch1tjagw8g8nn4cwuw00cf0m5tl4l6wfw9c0ue507fhx9e3yrsck8zs0l3q4w"
REGISTRATION_FEE = 500000000000000000
REGISTRATION_DENOM = "atestfet"
BLOCK_INTERVAL = 5
AGENT_NETWORK = AgentNetwork.FETCHAI_TESTNET

DEFAULT_ENVELOPE_TIMEOUT_SECONDS = 30
