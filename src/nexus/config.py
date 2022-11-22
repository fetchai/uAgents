import logging
from enum import Enum

logging.basicConfig(level=logging.INFO)


class AgentNetwork(Enum):
    FETCHAI_TESTNET = 1
    FETCHAI_MAINNET = 2


AGENT_PREFIX = "agent"
LEDGER_PREFIX = "fetch"
CONTRACT_ALMANAC = "fetch1gfq09zhz5kzeue3k9whl8t6fv9ke8vkq6x4s8p6pj946t50dmc7qvw5npv"
REGISTRATION_FEE = 500000000000000000
REGISTRATION_DENOM = "atestfet"
REG_UPDATE_INTERVAL_SECONDS = 60
AGENT_NETWORK = AgentNetwork.FETCHAI_TESTNET
