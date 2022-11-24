import logging
from enum import Enum

logging.basicConfig(level=logging.INFO)


class AgentNetwork(Enum):
    FETCHAI_TESTNET = 1
    FETCHAI_MAINNET = 2


AGENT_PREFIX = "agent"
LEDGER_PREFIX = "fetch"
CONTRACT_ALMANAC = "fetch1fvdmhy3y4hae35qsxgxjfy3nafvqe8grzclpeauvv2n3pt9l0uqqg375h8"
REGISTRATION_FEE = 500000000000000000
REGISTRATION_DENOM = "atestfet"
REG_UPDATE_INTERVAL_SECONDS = 60
AGENT_NETWORK = AgentNetwork.FETCHAI_TESTNET
