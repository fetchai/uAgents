from typing import Any, Dict, List, Optional

from uagents import Context, Model, Protocol


class ProtocolQuery(Model):
    protocol_digest: Optional[str]


class ProtocolResponse(Model):
    manifests: List[Dict[str, Any]]


proto_query = Protocol(name="QueryProtocolManifests", version="0.1.0")


@proto_query.on_query(ProtocolQuery)
async def send_protocol_manifests(ctx: Context, sender: str, msg: ProtocolQuery):
    manifests = []
    if msg.protocol_digest is not None:
        if msg.protocol_digest in ctx.protocols:
            manifests = [ctx.protocols[msg.protocol_digest].manifest()]
    else:
        manifests = [proto.manifest() for proto in ctx.protocols.values()]

    await ctx.send(sender, ProtocolResponse(manifests=manifests))
