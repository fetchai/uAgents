from datetime import datetime, timedelta
from typing import List

from geopy.geocoders import Nominatim
from geopy.distance import geodesic

from uagents import Context, Model, Protocol
from .models import Provider, Availability, User


PROTOCOL_NAME = "cleaning"
PROTOCOL_VERSION = "0.1.0"


class ServiceRequest(Model):
    user: str
    location: str
    time_start: datetime
    duration: timedelta
    services: List[int]
    max_price: float


class ServiceResponse(Model):
    accept: bool
    price: float


class ServiceBooking(Model):
    location: str
    time_start: datetime
    duration: timedelta
    services: List[int]
    price: float


class BookingResponse(Model):
    success: bool


cleaning_proto = Protocol(name=PROTOCOL_NAME, version=PROTOCOL_VERSION)


def in_service_region(
    location: str, availability: Availability, provider: Provider
) -> bool:
    geolocator = Nominatim(user_agent="micro_agents")

    user_location = geolocator.geocode(location)
    cleaner_location = geolocator.geocode(provider.location)

    if user_location is None:
        raise RuntimeError(f"user location {location} not found")

    if cleaner_location is None:
        raise RuntimeError(f"provider location {provider.location} not found")

    cleaner_coordinates = (cleaner_location.latitude, cleaner_location.longitude)
    user_coordinates = (user_location.latitude, user_location.longitude)

    service_distance = geodesic(user_coordinates, cleaner_coordinates).miles
    in_range = service_distance <= availability.max_distance

    return in_range


@cleaning_proto.on_message(model=ServiceRequest, replies=ServiceResponse)
async def handle_query_request(ctx: Context, sender: str, msg: ServiceRequest):
    provider = await Provider.filter(name=ctx.name).first()
    availability = await Availability.get(provider=provider)
    services = [int(service.type) for service in await provider.services]
    markup = provider.markup

    user, _ = await User.get_or_create(name=msg.user, address=sender)
    msg_duration_hours: float = msg.duration.total_seconds() / 3600
    ctx.logger.info(f"Received service request from user `{user.name}`")

    if (
        set(msg.services) <= set(services)
        and in_service_region(msg.location, availability, provider)
        and availability.time_start <= msg.time_start
        and availability.time_end >= msg.time_start + msg.duration
        and availability.min_hourly_price * msg_duration_hours < msg.max_price
    ):
        accept = True
        price = markup * availability.min_hourly_price * msg_duration_hours
        ctx.logger.info(f"I am available! Proposing price: {price}.")
    else:
        accept = False
        price = 0
        ctx.logger.info("I am not available. Declining request.")

    await ctx.send(sender, ServiceResponse(accept=accept, price=price))


@cleaning_proto.on_message(model=ServiceBooking, replies=BookingResponse)
async def handle_book_request(ctx: Context, sender: str, msg: ServiceBooking):
    provider = await Provider.filter(name=ctx.name).first()
    availability = await Availability.get(provider=provider)
    services = [int(service.type) for service in await provider.services]

    user = await User.get(address=sender)
    msg_duration_hours: float = msg.duration.total_seconds() / 3600
    ctx.logger.info(f"Received booking request from user `{user.name}`")

    success = (
        set(msg.services) <= set(services)
        and availability.time_start <= msg.time_start
        and availability.time_end >= msg.time_start + msg.duration
        and msg.price <= availability.min_hourly_price * msg_duration_hours
    )

    if success:
        availability.time_start = msg.time_start + msg.duration
        await availability.save()
        ctx.logger.info("Accepted task and updated availability.")

    # send the response
    await ctx.send(sender, BookingResponse(success=success))
