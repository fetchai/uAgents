from datetime import datetime, timezone

import requests

from uagents_core.config import AgentverseConfig

from . import output as out
from .common import DEFAULT_REQUESTS_TIMEOUT, compact_timedelta
from .types import AlmanacRegistration


def resolve(identifier: str, agentverse: AgentverseConfig | None = None):
    out.reset_sections()
    agentverse = agentverse or AgentverseConfig()

    almanac_api = f"{agentverse.url}/v2/almanac"

    try:
        response = requests.get(
            url=f"{almanac_api}/resolve/{identifier}", timeout=DEFAULT_REQUESTS_TIMEOUT
        )
        if response.ok:
            data = response.json()
            address = data["address"]
            reg = AlmanacRegistration.model_validate(data)
            out.section("Resolution")
            out.ok(f"Address: {address}")
            out.ok(f"Status: {reg.status}")
            out.ok(f"Type: {reg.type}")
            now = datetime.now(timezone.utc)
            if now > reg.expiry:
                out.err(
                    f"Registration expired {compact_timedelta(now - reg.expiry)} ago."
                )
            else:
                out.ok(
                    f"Registration valid ({compact_timedelta(reg.expiry - now)} remaining)"
                )
            out.ok(f"Endpoints: {', '.join(e.url for e in reg.endpoints)}")
        elif response.status_code == 404:
            out.section("Resolution")
            out.ok("Identifier is available (not assigned)")
        elif response.status_code == 400:
            out.section("Resolution")
            out.err("Malformed identifier")
        else:
            response.raise_for_status()
    except requests.RequestException as e:
        out.err(f"Failed to resolve identifier ({e})")
