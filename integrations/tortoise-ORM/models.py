from uagents import Model
from tortoise import fields, models

class RoomRequest(Model):
    max_price: int

class RoomResponse(Model):
    success: bool

class Availability(models.Model):
    id = fields.IntField(pk=True)
    room_available = fields.BooleanField(default=True)
    min_price = fields.FloatField(default=0.0)

