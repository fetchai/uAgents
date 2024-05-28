from uagents import Model
from pydantic import Field

class TopDestinations(Model):
  preferences: str = Field(description="The field expresses what the user prefer. Can be left empty. For example: 'beach', 'mountains, rivers', 'city', etc.")

