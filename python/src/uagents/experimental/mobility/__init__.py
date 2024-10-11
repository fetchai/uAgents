from pydantic.v1 import confloat

from uagents import Agent, Context, Model
from uagents.types import AgentGeolocation


class Location(Model):
    latitude: confloat(strict=True, ge=-90, le=90, allow_inf_nan=False)
    longitude: confloat(strict=True, ge=-180, le=180, allow_inf_nan=False)
    radius: confloat(strict=True, ge=0, allow_inf_nan=False)


class MobilityAgent(Agent):
    def __init__(self, **kwargs):
        self.mobility = True

        super().__init__(**kwargs)

        @self.on_rest_post("/set_location", Location, Location)
        async def _handle_location_update(_ctx: Context, req: Location):
            self._update_geolocation(AgentGeolocation(**req.model_dump()))
            return self.location

    @property
    def location(self) -> dict:
        return self.metadata["geolocation"] or {}

    def _update_geolocation(self, location: AgentGeolocation):
        self._metadata["geolocation"]["latitude"] = location.latitude
        self._metadata["geolocation"]["longitude"] = location.longitude
        self._metadata["geolocation"]["radius"] = location.radius
        self.invoke_location_update()

    def step(self):
        self.location["latitude"] += 0.00001
        self.location["longitude"] += 0.00001
        self.invoke_location_update()

    def invoke_location_update(self):
        self._logger.info("Updating location")
