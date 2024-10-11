from datetime import datetime
from typing import Any, Literal

from pydantic.v1 import confloat

from uagents import Agent, Context, Model
from uagents.experimental.mobility.protocols.base_protocol import CheckIn, CheckOut
from uagents.experimental.search import Agent as SearchResultAgent
from uagents.experimental.search import geosearch_agents_by_protocol
from uagents.types import AgentGeolocation


class Location(Model):
    latitude: confloat(strict=True, ge=-90, le=90, allow_inf_nan=False)
    longitude: confloat(strict=True, ge=-180, le=180, allow_inf_nan=False)
    radius: confloat(ge=0, allow_inf_nan=False)


MobililtyType = Literal[
    "traffic_lights", "traffic_sign", "vehicle", "bike", "pedestrian"
]


class MobilityAgent(Agent):
    def __init__(
        self, location: AgentGeolocation, mobility_type: MobililtyType, **kwargs
    ):
        super().__init__(**kwargs)
        self.mobility = True
        self._metadata["geolocation"] = location.model_dump()
        self._metadata["mobility_type"] = mobility_type
        self._proximity_agents: list[SearchResultAgent] = []
        self._checkedin_agents: dict[str, dict[str, Any]] = {}

        @self.on_rest_post("/set_location", Location, Location)
        async def _handle_location_update(_ctx: Context, req: Location):
            self._update_geolocation(AgentGeolocation(**req.model_dump()))
            return self.location

    @property
    def location(self) -> dict:
        return self.metadata["geolocation"] or {}

    @property
    def mobility_type(self) -> MobililtyType:
        return self.metadata["mobility_type"]

    @property
    def proximity_agents(self) -> list[SearchResultAgent]:
        # agents where this agent checked in
        return self._proximity_agents

    @property
    def checkedin_agents(self) -> dict[str, CheckIn]:
        # agents that checked in with this agent
        return self._checkedin_agents

    def checkin_agent(self, addr: str, agent: CheckIn):
        self._checkedin_agents.update(
            {addr: {"timestamp": datetime.now(), "agent": CheckIn}}
        )

    def checkout_agent(self, addr: str):
        del self._checkedin_agents[addr]

    def activate_agent(self, agent: SearchResultAgent):
        for activated in self._proximity_agents:
            if activated.address == agent.address:
                return

        self._proximity_agents.append(agent)

    def deactivate_agent(self, agent: SearchResultAgent):
        self._proximity_agents.remove(agent)

    async def _update_geolocation(self, location: AgentGeolocation):
        self._metadata["geolocation"]["latitude"] = location.latitude
        self._metadata["geolocation"]["longitude"] = location.longitude
        self._metadata["geolocation"]["radius"] = location.radius
        await self.invoke_location_update()

    async def step(self):
        self.location["latitude"] += 0.00001
        self.location["longitude"] += 0.00001
        await self.invoke_location_update()

    async def invoke_location_update(self):
        self._logger.info("Updating location")
        proximity_agents = geosearch_agents_by_protocol(
            self.location["latitude"],
            self.location["longitude"],
            self.location["radius"],
            "<proto:digest>",
            30,
        )
        # send a check-in message to all agents that are in the current proximity
        for agent in proximity_agents:
            await self._send_checkin(agent)
        agents_that_left_proximity = set(self._proximity_agents) - set(proximity_agents)
        for agent in agents_that_left_proximity:
            # send a check-out message to all agents that left the proximity
            await self._send_checkout(agent)
        self._proximity_agents = proximity_agents  # potential extra steps possible

    async def _send_checkin(self, agent: SearchResultAgent):
        ctx = self._build_context()
        if agent in self._proximity_agents:
            return
        # only send check-in to agents that are not already in the proximity list
        await ctx.send(
            agent.address,
            CheckIn(
                mobility_type=self.mobility_type,
                supported_protocols=list(self.protocols.keys()),
            ),
        )

    async def _send_checkout(self, agent: SearchResultAgent):
        ctx = self._build_context()
        # send checkout message to all agents that left the proximity
        await ctx.send(agent.address, CheckOut())

    async def register(self):
        """
        Overwrite the register method to include the geolocation in the metadata
        """
        await self._registration_policy.register(
            self.address, list(self.protocols.keys()), self._endpoints, self._metadata
        )
