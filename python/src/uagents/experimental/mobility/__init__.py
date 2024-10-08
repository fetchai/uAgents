from uagents import Agent
from uagents.registration import MobilityRegistrationPolicy
from uagents.types import AgentGeoLocation


class MobilityAgent(Agent):
    def __init__(self, location: AgentGeoLocation, **kwargs):
        self.mobility = True
        self._location = location
        super().__init__(**kwargs)
        self.update_registration_policy(
            MobilityRegistrationPolicy(
                identity=self._identity,
                location=self._location,
            )
        )

    @property
    def location(self) -> AgentGeoLocation:
        return self._location

    def move(self, lat: float, long: float):
        self._location.latitude = lat
        self._location.longitude = long
        self.invoke_location_update()

    def step(self):
        self._location.latitude += 0.1
        self._location.longitude += 0.1
        self.invoke_location_update()

    def invoke_location_update(self): ...
