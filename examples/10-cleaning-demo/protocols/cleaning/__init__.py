from datetime import datetime, timedelta
from typing import List

from nexus import Context, Model, Protocol

from .models import Provider, Availability, User


PROTOCOL_NAME = "cleaning"
PROTOCOL_VERSION = "0.1.0"


class ServiceRequest(Model):
    user: str
    address: int
    time_start: datetime
    duration: timedelta
    services: List[int]
    max_price: float


class ServiceResponse(Model):
    accept: bool
    price: float


class ServiceBooking(Model):
    address: str
    time_start: datetime
    duration: timedelta
    services: List[int]
    price: float


class BookingResponse(Model):
    success: bool


cleaning_proto = Protocol(name=PROTOCOL_NAME, version=PROTOCOL_VERSION)


def in_service_region(
    address: int, availability: Availability, provider: Provider
) -> bool:
    return abs(provider.address - address) <= availability.max_distance


@cleaning_proto.on_message(model=ServiceRequest, replies=ServiceResponse)
async def handle_query_request(ctx: Context, sender: str, msg: ServiceRequest):

    provider = await Provider.filter(name=ctx.name).first()
    availability = await Availability.get(provider=provider)
    services = [int(service.type) for service in await provider.services]
    markup = provider.markup

    user, _ = await User.get_or_create(name=msg.user, address=sender)
    msg_duration_hours: float = msg.duration.total_seconds() / 3600
    print(f"Received service request from user `{user.name}`")

    if (
        set(msg.services) <= set(services)
        and in_service_region(msg.address, availability, provider)
        and availability.time_start <= msg.time_start
        and availability.time_end >= msg.time_start + msg.duration
        and availability.min_hourly_price * msg_duration_hours < msg.max_price
    ):
        accept = True
        price = markup * availability.min_hourly_price * msg_duration_hours
        print(f"I am available! Proposing price: {price}.")
    else:
        accept = False
        price = 0
        print("I am not available. Declining request.")

    await ctx.send(sender, ServiceResponse(accept=accept, price=price))


@cleaning_proto.on_message(model=ServiceBooking, replies=BookingResponse)
async def handle_book_request(ctx: Context, sender: str, msg: ServiceBooking):

    provider = await Provider.get(name=ctx.name)
    availability = await Availability.get(provider=provider)
    services = [int(service.type) for service in await provider.services]

    user = await User.get(address=sender)
    msg_duration_hours: float = msg.duration.total_seconds() / 3600
    print(f"Received booking request from user `{user.name}`")

    success = (
        set(msg.services) <= set(services)
        and availability.time_start <= msg.time_start
        and availability.time_end >= msg.time_start + msg.duration
        and msg.price <= availability.min_hourly_price * msg_duration_hours
    )

    if success:
        availability.time_start = msg.time_start + msg.duration
        await availability.save()
        print("Accepted task and updated availability.")

    # send the response
    await ctx.send(sender, BookingResponse(success=success))
