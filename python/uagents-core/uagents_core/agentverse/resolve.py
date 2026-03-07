import requests

from uagents_core.config import AgentverseConfig

from .common import DEFAULT_REQUESTS_TIMEOUT, _datetime_fmt, logger
from .types import AlmanacRegistration


def resolve(identifier: str, agentverse: AgentverseConfig | None = None):

    agentverse = agentverse or AgentverseConfig()

    almanac_api = f"{agentverse.url}/v2/almanac"
    logger.info(f"[-] resolving identifier {identifier}...")
    try:
        response = requests.get(
            url=f"{almanac_api}/resolve/{identifier}", timeout=DEFAULT_REQUESTS_TIMEOUT
        )
        if response.ok:
            logger.info(
                f"[+] identifier is assigned to agent {response.json()['address']}"
            )
            reg = AlmanacRegistration.model_validate(response.json())
            logger.info(f"    |--> {reg.status}")
            logger.info(f"    |--> type is {reg.type}")
            logger.info(f"    |--> expiry {_datetime_fmt(reg.expiry)}")
            logger.info(
                f"    |--> endpoints {', '.join([e.url for e in reg.endpoints])}"
            )
        elif response.status_code == 404:
            logger.info(f"[+] identifier is available.")
        elif response.status_code == 400:
            logger.error(f"[!] malformed identifier.")
        else:
            response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"[!] failed to resolve identifier {e}.")
