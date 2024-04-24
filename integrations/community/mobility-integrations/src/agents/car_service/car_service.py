# Here we demonstrate how we can create a DeltaV compatible agent responsible for getting Car Service from Static Data.
# After running this agent, it can be registered to DeltaV on Agentverse's Services tab. For registration,
# you will have to use the agent's address.
#
# third party modules used in this example
import json
import uuid

from ai_engine import KeyValue, UAgentResponse, UAgentResponseType
from pydantic import Field

# modules from booking_protocol.py
from booking_protocol import booking_proto
from car_service_data import CAMBRIDGE_CAR_SERVICE, MUNICH_CAR_SERVICE, PRAGUE_CAR_SERVICE, STUTTGART_CAR_SERVICE


class CarServiceRequest(Model):
    latitude: float = Field(
        description="Describes the latitude where the user wants a Car Service Center. this shouldn't be the user "
                    "location, but location of the place user specified.")
    longitude: float = Field(
        description="Describes the longitude where the user wants a Car Service Center. this shouldn't be the user "
                    "location, but the location of the place the user specified.")
    miles_radius: float = Field(
        description="Distance in miles, the maximum distance b/w car service center and the location provided by user.")


car_service_center_protocol = Protocol("Car Service Center")


def get_data(latitude, longitude, miles_radius) -> list or None:
    """
        Function to get the data from Car Service Center json
        Args:
            latitude (float): The latitude coordinate.
            longitude (float): The longitude coordinate.
            miles_radius (float): The radius in miles for searching Car Service Center.
        Return:
            list or None: A list of Car Service Center data.
    """
    car_service_json = []
    if int(latitude) == 50 and int(longitude) == 14:
        car_service_json = PRAGUE_CAR_SERVICE
    elif int(latitude) == 48 and int(longitude) == 11:
        car_service_json = MUNICH_CAR_SERVICE
    elif int(latitude) == 52 and int(longitude) == 0:
        car_service_json = CAMBRIDGE_CAR_SERVICE
    else:
        car_service_json = STUTTGART_CAR_SERVICE
    response = car_service_json
    return [
        car_service
        for car_service in response
        if car_service["distance"] <= miles_radius
    ]


@car_service_center_protocol.on_message(model=CarServiceRequest, replies=UAgentResponse)
async def on_message(ctx: Context, sender: str, msg: CarServiceRequest):
    ctx.logger.info(f"Received message from {sender}")
    try:
        data = get_data(msg.latitude, msg.longitude, msg.miles_radius)
        request_id = str(uuid.uuid4())
        options = []
        ctx_storage = {}
        for idx, o in enumerate(data):
            option = f"""This is Car Service Center: {o['name']} which is located {o['distance']} miles away from your location """
            options.append(KeyValue(key=idx, value=option))
            ctx_storage[idx] = option
        ctx.storage.set(request_id, ctx_storage)
        if options:
            await ctx.send(
                sender,
                UAgentResponse(
                    options=options,
                    type=UAgentResponseType.SELECT_FROM_OPTIONS,
                    request_id=request_id
                )
            )
        else:
            await ctx.send(
                sender,
                UAgentResponse(
                    message="No car service center are available for this context",
                    type=UAgentResponseType.FINAL,
                    request_id=request_id
                )
            )
    except Exception as exc:
        ctx.logger.error(exc)
        await ctx.send(
            sender,
            UAgentResponse(
                message=str(exc),
                type=UAgentResponseType.ERROR
            )
        )


agent.include(car_service_center_protocol)
agent.include(booking_proto())
