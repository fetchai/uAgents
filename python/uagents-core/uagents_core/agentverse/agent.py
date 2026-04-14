from collections import Counter
from datetime import datetime, timezone

import requests
from pydantic import ValidationError

from uagents_core.config import AgentverseConfig
from uagents_core.contrib.protocols.chat import chat_protocol_spec
from uagents_core.protocol import ProtocolSpecification
from uagents_core.types import AgentEndpoint
from uagents_core.utils.resolver import AlmanacResolver

from . import output as out
from .common import (
    DEFAULT_REQUESTS_TIMEOUT,
    _datetime_fmt,
    compact_timedelta,
)
from .types import (
    AlmanacRegistration,
    SearchRecord,
)

_IGNORED_METADATA_KEYS = frozenset({"contact_details"})


def _metadata_for_compare(meta: dict | None) -> dict:
    if meta is None:
        return {}
    return {k: v for k, v in meta.items() if k not in _IGNORED_METADATA_KEYS}


def _get_almanac_registration(
    agent: str, agentverse: AgentverseConfig
) -> AlmanacRegistration | None:
    try:
        response = requests.get(
            url=f"{agentverse.almanac_api}/agents/{agent}",
            timeout=DEFAULT_REQUESTS_TIMEOUT,
        )
        if response.status_code == 404:
            out.err("Agent not registered in the almanac")
            return None
        else:
            response.raise_for_status()

        return AlmanacRegistration.model_validate(response.json())

    except requests.RequestException as e:
        out.err(f"Failed to fetch almanac registration ({e})")
    except (KeyError, ValidationError) as e:
        out.err(f"Failed to parse almanac registration ({e})")

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
        out.err(f"Failed to fetch search record ({e})")
    except (KeyError, ValidationError) as e:
        out.err(f"Failed to parse search record ({e})")

    return None


def _profile(
    reg: AlmanacRegistration | None, rec: SearchRecord | None, full_readme: bool = False
) -> dict:
    if reg is None and rec is None:
        return {}

    elif reg is None:
        out.warn("Agent registration is missing (marketplace only).")
        return rec.model_dump(mode="json")

    elif rec is None:
        out.warn("Agent profile is missing (almanac only).")
        return reg.model_dump(mode="json")

    cross_heading_shown = False

    def cross_warn(message: str) -> None:
        nonlocal cross_heading_shown
        if not cross_heading_shown:
            out.section("Almanac vs marketplace")
            cross_heading_shown = True
        out.warn(message)

    if reg.type != rec.type:
        cross_warn("Mismatched agent type.")
        type = f"{reg.type}/{rec.type}"
    else:
        type = reg.type

    if reg.status != rec.status:
        cross_warn("Mismatched status.")
        status = f"{reg.status}/{rec.status}"
    else:
        status = reg.status

    meta_left = _metadata_for_compare(reg.metadata)
    meta_right = _metadata_for_compare(rec.metadata)
    if meta_left != meta_right:
        cross_warn("Mismatched metadata.")
        out.dict_diff(meta_left, meta_right)
        metadata = f"{reg.metadata}/{rec.metadata}"
    else:
        metadata = reg.metadata

    rec_protocols = [p.digest.lstrip("proto:") for p in rec.protocols]
    if Counter(reg.protocols) != Counter(rec_protocols):
        cross_warn("Mismatched protocols.")
        out.list_diff(reg.protocols, rec_protocols)
        protocols = {"s": [p.model_dump() for p in rec.protocols], "a": reg.protocols}
    else:
        protocols = [p.model_dump() for p in rec.protocols]

    if reg.domain_name != rec.domain:
        cross_warn("Mismatched domain.")
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
    out.section("Address resolution")
    endpoints = AlmanacResolver(agentverse_config=agentverse).sync_resolve(agent)

    if len(endpoints) == 0:
        out.err("Could not resolve agent address.")
    else:
        out.ok(f"Available at {', '.join(endpoints)}")

    out.section("Almanac")
    out.ok(f"Agent type: {reg.type}")

    now = datetime.now(timezone.utc)
    if now > reg.expiry:
        out.err(f"Registration expired {compact_timedelta(now - reg.expiry)} ago.")
    else:
        out.ok(f"Registration valid ({compact_timedelta(reg.expiry - now)} remaining)")

    if reg.status == "active":
        out.ok("Status is active")
    else:
        out.err("Status is not active")

    if reg.domain_name is not None:
        out.ok(f"Domain assigned: {reg.domain_name}")

    if len(reg.protocols) == 0:
        out.warn("No protocols registered")
    else:
        chat_proto = ProtocolSpecification.compute_digest(
            chat_protocol_spec.manifest()
        ).lstrip("proto:")
        if chat_proto in reg.protocols:
            out.ok("Chat protocol supported")
        else:
            out.err("Chat protocol not supported")

    if reg.metadata is not None:
        sanitised = {k: v for k, v in reg.metadata.items() if v is not None}
        if sanitised:
            out.info(f"Metadata: {sanitised}")

    if rec is not None:
        out.section("Marketplace")

        if len(rec.readme) > 0:
            out.ok("Readme present")
        else:
            out.warn("No readme")

        if rec.handle is not None and len(rec.handle) > 0:
            out.ok(f"Handle: {rec.handle}")
        else:
            out.warn("No handle assigned")

        if rec.total_interactions > 1:
            out.ok(f"Interactions: {rec.total_interactions}")
        else:
            out.warn("No meaningful interaction count yet")


def _check_connectivity(agent: str, endpoints: list[AgentEndpoint]):
    out.section("Endpoint connectivity")
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
                msg = f"HTTP {resp.status_code} ({resp.text})"
        except requests.exceptions.ConnectionError:
            msg = "could not connect"
        except requests.exceptions.Timeout:
            msg = "request timed out"
        except requests.exceptions.RequestException as e:
            msg = str(e)

        if responsive and success:
            out.ok(f"{url} — reachable")
        elif responsive:
            out.warn(f"{url} — responded but {msg}")
        else:
            out.err(f"{url} — not reachable ({msg})")


def check_agent(
    agent: str,
    show_profile: bool = True,
    full_readme: bool = False,
    check_connectivity: bool = True,
    include_raw_records: bool = False,
    agentverse: AgentverseConfig | None = None,
):
    out.reset_sections()
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
        if include_raw_records:
            if registration is not None:
                out.section("Full Almanac Record")
                out.print_json(registration.model_dump(mode="json"))
            if record is not None:
                out.section("Full Marketplace Record")
                mkt = record.model_dump(mode="json")
                if full_readme and mkt.get("readme"):
                    readme_raw = mkt.pop("readme")
                    out.print_json(mkt)
                    print()
                    out.section("Readme")
                    out.print_readme(readme_raw)
                else:
                    out.print_json(mkt)
        else:
            out.section("Profile")
            if full_readme and profile.get("readme"):
                profile_for_json = {k: v for k, v in profile.items() if k != "readme"}
                out.print_json(profile_for_json)
                print()
                out.section("Readme")
                out.print_readme(profile["readme"])
            else:
                out.print_json(profile)
