from uagents import Model
from pydantic import Field
from typing import Optional

class Flights(Model):
  from_: str = Field(alias="from", description="This field is the airport IATA code for of the airport from where the user wants to fly from. This should be airport IATA code. IATA airport code is a three-character alphanumeric geocode.")
  to: str = Field(description="This field is the airport IATA code of the destination airport! This should be airport IATA code. IATA airport code is a three-character alphanumeric geocode.")
  trip: Optional[str] = Field(description="This can be oneway or return")
  date: str = Field(description="Contains the date of flying out.")
  back_date: Optional[str] = Field(description="Optional field only for return flight. This is the date when the user wants to fly back")
  route: Optional[int] = Field(description="Selects the maximum number of stops, 0 means direct flight, 1 means with maximum 1 stop.")
  persons: int = Field(description="Describes how many persons are going to fly.")

  class Config:
    allow_population_by_field_name = True
