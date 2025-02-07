from time import time
from typing import Any

from pydantic import BaseModel

from uagents import Agent, Context
from uagents.experimental.mobility.protocols.base_protocol import (
    CheckIn,
    CheckOut,
    Location,
    MobilityAgentLog,
    MobilityAgentLogs,
    MobilityType,
)
from uagents.experimental.search import Agent as SearchResultAgent
from uagents.experimental.search import geosearch_agents_by_proximity
from uagents.types import AgentGeolocation


class MobilityMetadata(BaseModel):
    mobility_type: MobilityType
    coordinates: AgentGeolocation
    static_signal: str = ""
    metadata: dict[str, Any] = {}


class MobilityAgent(Agent):
    def __init__(
        self,
        location: AgentGeolocation,
        mobility_type: MobilityType,
        static_signal: str,
        logging: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.mobility = True
        self._metadata["geolocation"] = location.model_dump()
        self._metadata["mobility_type"] = mobility_type
        self._metadata["static_signal"] = static_signal
        self._proximity_agents: list[SearchResultAgent] = []
        self._checkedin_agents: dict[str, dict[str, Any]] = {}
        self._logging = logging

        # if logging is enabled, add a REST endpoint to get the logs
        if self._logging:

            @self.on_rest_get("/mobility_logs", MobilityAgentLogs)  # type: ignore
            async def _handle_log_get(_ctx: Context):
                return MobilityAgentLogs(logs=self._get_history())

    @property
    def location(self) -> dict:
        return self.metadata["geolocation"] or {}

    @property
    def mobility_type(self) -> MobilityType:
        return self.metadata["mobility_type"]

    @property
    def static_signal(self) -> str:
        return self.metadata["static_signal"]

    @property
    def proximity_agents(self) -> list[SearchResultAgent]:
        """
        List of agents that this agent has checked in with.
        (i.e. agents that are in proximity / within the radius of this agent)
        """
        return self._proximity_agents
        # only agents that were searched for appear here which is the main
        # difference to checkedin_agents where less information is stored
        # -> intrinsic information

    @property
    def checkedin_agents(self) -> dict[str, dict[str, Any]]:
        """
        List of agents that have checked in with this agent.
        (i.e. agents which radius this agent is within)
        """
        return self._checkedin_agents
        # - extrinsic information

    def checkin_agent(self, addr: str, agent: CheckIn):
        timestamp = int(time())
        self._checkedin_agents.update(
            {
                addr: {"timestamp": timestamp, "agent": agent},
            }
        )
        self._write_history(
            MobilityAgentLog(
                timestamp=timestamp,
                active_address=addr,
                passive_address=self.address,
                active_mobility_type=agent.mobility_type,
                passive_mobility_type=self.mobility_type,
                interaction="checkin",
            )
        )

    def checkout_agent(self, addr: str):
        removed = self._checkedin_agents.pop(addr)
        self._write_history(
            MobilityAgentLog(
                timestamp=int(time()),
                active_address=addr,
                passive_address=self.address,
                active_mobility_type=removed["agent"].mobility_type,
                passive_mobility_type=self.mobility_type,
                interaction="checkout",
            )
        )

    async def update_geolocation(self, location: Location) -> dict:
        """
        Call this method with new location data to update the agent's location

        returns: dict - updated location data
        """
        self._metadata["geolocation"]["latitude"] = location.latitude
        self._metadata["geolocation"]["longitude"] = location.longitude
        self._metadata["geolocation"]["radius"] = location.radius
        await self._invoke_location_update()
        return self.location

    async def _invoke_location_update(self):
        self._logger.info(
            f"Updating location {(self.location['latitude'], self.location['longitude'])}"
        )
        proximity_agents = geosearch_agents_by_proximity(
            self.location["latitude"],
            self.location["longitude"],
            self.location["radius"],
            30,
        )  # should return only active agents
        # send a check-in message to all agents that are in the current proximity
        for agent in proximity_agents:
            await self._send_checkin(agent)
        # find out which agents left proximity and send them a check-out message
        addresses_that_left_proximity = {a.address for a in self._proximity_agents} - {
            a.address for a in proximity_agents
        }
        agents_that_left_proximity = [
            a
            for a in self._proximity_agents
            if a.address in addresses_that_left_proximity
        ]
        for agent in agents_that_left_proximity:
            # send a check-out message to all agents that left the proximity
            await self._send_checkout(agent)
        self._proximity_agents = proximity_agents  # potential extra steps possible

    async def _send_checkin(self, agent: SearchResultAgent):
        """Send a check-in message to an agent (if not already in the proximity list)"""
        if agent in self._proximity_agents:
            return
        await self._build_context().send(
            agent.address,
            CheckIn(
                mobility_type=self.mobility_type,
                supported_protocols=list(self.protocols.keys()),
            ),
        )

    async def _send_checkout(self, agent: SearchResultAgent):
        """Send a check-out message to an agent"""
        await self._build_context().send(agent.address, CheckOut())

    def _write_history(self, log: MobilityAgentLog) -> bool:
        """
        Write history of agent interactions to a file
        """
        try:
            history = self.storage.get("mobility_logs") or []
            history.append(log.model_dump_json())
            self.storage.set("mobility_logs", history)
            return True
        except Exception as e:
            self._logger.error(f"Error writing history: {e}")
            return False

    def _get_history(self) -> list[MobilityAgentLog]:
        """
        Get the history of agent interactions
        """
        cache = self.storage.get("mobility_logs") or []
        return [MobilityAgentLog.model_validate_json(log) for log in cache]
