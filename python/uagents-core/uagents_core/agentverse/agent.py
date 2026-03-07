import json
from datetime import datetime, timezone
from typing import List

import requests
from pydantic import ValidationError

from uagents_core.config import AgentverseConfig
from uagents_core.contrib.protocols.chat import chat_protocol_spec
from uagents_core.protocol import ProtocolSpecification
from uagents_core.types import AgentEndpoint
from uagents_core.utils.resolver import AlmanacResolver

from .common import (
    DEFAULT_REQUESTS_TIMEOUT,
    _datetime_fmt,
    logger,
)
from .types import (
    AlmanacRegistration,
    SearchRecord,
)


def _get_almanac_registration(
    agent: str, agentverse: AgentverseConfig
) -> AlmanacRegistration | None:

    try:
        response = requests.get(
            url=f"{agentverse.almanac_api}/agents/{agent}",
            timeout=DEFAULT_REQUESTS_TIMEOUT,
        )
        if response.status_code == 404:
            logger.error("[!] agent not registered to almanac")
            return None
        else:
            response.raise_for_status()

        return AlmanacRegistration.model_validate(response.json())

    except requests.RequestException as e:
        logger.error(f"[!] failed to fetch almanac registration {e}.")
    except (KeyError, ValidationError) as e:
        logger.error(f"[!] failed to parse almanac registration {e}.")

    return None


def _get_search_record(agent: str, agentverse: AgentverseConfig) -> SearchRecord | None:
    try:
        response = requests.post(
            f"{agentverse.search_api}/agents",
            timeout=DEFAULT_REQUESTS_TIMEOUT,
            json={"search_text": f"address:{agent}", "exact_match": True},
        )
        response.raise_for_status()
        agents = [a for a in response.json()["agents"] if a["address"] == agent]
        if len(agents) != 1:
            return None

        return SearchRecord.model_validate(agents[0])

    except requests.RequestException as e:
        logger.error(f"[!] failed to fetch search record {e}.")
    except (KeyError, ValidationError) as e:
        logger.error(f"[!] failed to parse search record {e}.")

    return None


def _profile(
    reg: AlmanacRegistration, rec: SearchRecord, full_readme: bool = False
) -> dict:
    if reg is None and rec is None:
        return {}

    elif reg is None:
        logger.warning("Agent registration is missing.")
        return rec.model_dump(mode="json")

    elif rec is None:
        logger.warning("Agent profile is missing.")
        return reg.model_dump(mode="json")

    if reg.type != rec.type:
        logger.warning("Mismatched agent type.")
        type = f"{reg.type}/{rec.type}"
    else:
        type = reg.type

    if reg.status != rec.status:
        logger.warning(f"Mismatched agent status.")
        status = f"{reg.status}/{rec.status}"
    else:
        status = reg.status

    if reg.metadata != rec.metadata:
        logger.warning(f"Mismatched agent metadata.")
        metadata = f"{reg.metadata}/{rec.metadata}"
    else:
        metadata = reg.metadata

    rec_protocols = [p.digest.lstrip("proto:") for p in rec.protocols]
    if reg.protocols != rec_protocols:
        logger.warning(f"Mismatched agent protocols.")
        protocols = {"s": [p.model_dump() for p in rec.protocols], "a": reg.protocols}
    else:
        protocols = [p.model_dump() for p in rec.protocols]

    if reg.domain_name != rec.domain:
        logger.warning(f"Mismatched agent domain.")
        domain = f"{reg.domain_name}/{rec.domain}"
    else:
        domain = reg.domain_name

    return {
        "name": rec.name,
        "status": status,
        "type": type,
        "description": rec.description,
        "avatar_hred": rec.avatar_href,
        "endpoints": [e.url for e in reg.endpoints],
        "protocols": protocols,
        "metadata": metadata,
        "domain": domain,
        "handle": rec.handle,
        "created_at": _datetime_fmt(rec.created_at),
        "last_updated": _datetime_fmt(rec.last_updated),
        "expiry": _datetime_fmt(reg.expiry),
        "interactions": rec.total_interactions,
        "readme": rec.readme if full_readme else f"{rec.readme[:10]}...",
    }


def _troubleshoot(
    agent: str,
    reg: AlmanacRegistration,
    rec: SearchRecord | None,
    agentverse: AgentverseConfig,
):

    logger.info("[-] checking agent address resolution...")
    endpoints = AlmanacResolver(agentverse_config=agentverse).sync_resolve(agent)

    if len(endpoints) == 0:
        logger.error("[!] couldn't resolve agent address.")
    else:
        logger.info(f"[+] agent available at {', '.join(endpoints)}.")

    logger.info("[-] checking almanac registration...")

    logger.info(f"[+]  |--> agent is registred as {reg.type}.")

    now = datetime.now(timezone.utc)
    if now > reg.expiry:
        logger.error(f"[!] |--> agent registration expired {now - reg.expiry} ago.")
    else:
        logger.info(
            f"[+]  |--> agent regisration is up to date ({reg.expiry - now} to go)."
        )

    if reg.status == "active":
        logger.info("[+]  |--> agent is active.")
    else:
        logger.error("[!] |--> agent is inactive")

    if reg.domain_name is not None:
        logger.info(f"[+]  |--> agent is assigned domain {reg.domain_name}")

    if len(reg.protocols) == 0:
        logger.warning("[!] |--> agent has no protocols!.")
    else:
        chat_proto = ProtocolSpecification.compute_digest(
            chat_protocol_spec.manifest()
        ).lstrip("proto:")
        if chat_proto in reg.protocols:
            logger.info(f"[+]  |--> agent supports the chat protocol.")
        else:
            logger.error(f"[!] |--> agent does not support the chat protocol.")

    if reg.metadata is not None:
        sanitised = {k: v for k, v in reg.metadata.items() if v is not None}
        logger.info(f"[+]  |--> agent metadata {sanitised}")

    if rec is not None:
        logger.info("[-] checking marketplace profile...")

        if len(rec.readme) > 0:
            logger.info("[+]  |--> agent provided a readme file.")
        else:
            logger.warning("[!]  |--> agent doesn't have a readme file.")

        if rec.handle is not None and len(rec.handle) > 0:
            logger.info("[+]  |--> agent is assigned a handle")
        else:
            logger.warning("[!]  |--> agent is not assigned a handle")

        if rec.total_interactions > 1:
            logger.info("[+]  |-->  agent have interactions")
        else:
            logger.warning("[!]  |-->  agent doesn't have any interactions")


def _check_connectivity(agent: str, endpoints: List[AgentEndpoint]):

    logger.info("[-] checking agents endpoints connectivity...")
    urls = [e.url for e in endpoints]

    for url in urls:
        responsive = False
        success = False
        msg = ""

        try:
            resp = requests.head(url, headers={"x-uagents-address": agent})
            responsive = True

            if resp.ok:
                success = True
            else:
                msg = f"returned code {resp.status_code} ({resp.text})"
        except requests.exceptions.ConnectionError:
            msg = "couldn't connect"
        except requests.exceptions.Timeout:
            msg = "request timed out"
        except requests.exceptions.RequestException as e:
            msg = f"error occured {e}"

        if responsive and success:
            logger.info(f"[+]  |--> url {url} is reachable.")
        elif responsive:
            logger.warning(f"[+]  |--> url {url} is reachable but {msg}.")
        else:
            logger.error(f"[!]  |--> url {url} is not reachable ({msg})")


def check_agent(
    agent: str,
    show_profile: bool = True,
    full_readme: bool = False,
    check_connectivity: bool = True,
    agentverse: AgentverseConfig | None = None,
):
    agentverse = agentverse or AgentverseConfig()
    registration = _get_almanac_registration(agent, agentverse)
    record = _get_search_record(agent, agentverse)

    if registration is not None:
        _troubleshoot(agent, registration, record, agentverse)

    profile = _profile(registration, record, full_readme=full_readme)

    if (
        check_connectivity
        and registration is not None
        and len(registration.endpoints) > 0
    ):
        _check_connectivity(agent, registration.endpoints)

    if show_profile and len(profile) > 0:
        print(json.dumps(profile, indent=2))
