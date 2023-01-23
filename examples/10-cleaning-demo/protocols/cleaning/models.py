from enum import Enum

from tortoise import fields, models


class ServiceType(int, Enum):
    FLOOR = 1
    WINDOW = 2
    LAUNDRY = 3
    IRON = 4
    BATHROOM = 5


class User(models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=64)
    address = fields.CharField(max_length=100)
    created_at = fields.DatetimeField(auto_now_add=True)


class Service(models.Model):
    id = fields.IntField(pk=True)
    type = fields.IntEnumField(ServiceType)


class Provider(models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=64)
    location = fields.CharField(max_length=64)
    created_at = fields.DatetimeField(auto_now_add=True)
    availability = fields.ReverseRelation["Availability"]
    services = fields.ManyToManyField("models.Service")
    markup = fields.FloatField(default=1.1)


class Availability(models.Model):
    id = fields.IntField(pk=True)
    provider = fields.OneToOneField("models.Provider", related_name="availability")
    max_distance = fields.IntField(default=10)
    time_start = fields.DatetimeField()
    time_end = fields.DatetimeField()
    min_hourly_price = fields.FloatField(default=0.0)
