from uagents import Model
from typing import Optional
from pydantic import Field

class TopActivities(Model):
  city: str = Field(description="Describes the city where we want to go and find activity, for example: London. This shouldn't be based on user current location, but the city where user wants to go.")
  date: str = Field(description="Describes which date user wants to find top activities in given city")
  preferred_activities: Optional[str] = Field(description="Describes what activities the user prefers. It is optional")
