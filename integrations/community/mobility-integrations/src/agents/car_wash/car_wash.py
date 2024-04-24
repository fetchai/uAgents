# Here we demonstrate how we can create a DeltaV compatible agent responsible for getting Car Wash from Static Data.
# After running this agent, it can be registered to DeltaV on Agentverse's Services tab. For registration,
# you will have to use the agent's address.
#
# third party modules used in this example
import uuid

from ai_engine import KeyValue, UAgentResponse, UAgentResponseType
from pydantic import Field

# modules from booking_protocol.py
from booking_protocol import booking_proto
from car_wash_data import MUNICH_CAR_WASH, STUTTGART_CAR_WASH, PRAGUE_CAR_WASH


class CarWashRequest(Model):
    latitude: float = Field(description="Describes the latitude where the user wants a Car Wash. If a user specified "
                                        "a location, the location MUST be the one specified by the user.")
    longitude: float = Field(description="Describes the longitude where the user wants a Car Wash. If a user "
                                         "specified a location, the location MUST be the one specified by the user.")
    miles_radius: float = Field(description="Distance in miles, the maximum distance b/w car wash and the location "
                                            "provided by user.")
    price: int = Field(description="Describe the maximum Price in euros for car Wash.")
    additional_amenities: Optional[str] = Field(description="This field describes the additional amenities, "
                                                            "for example: Handwash, Machine wash, Lounge Area, "
                                                            "Air Fresheners. Users don’t select any amenities then it "
                                                            "should be None.")


car_wash_protocol = Protocol("Car Wash")


additional_amenities = ['handwash', 'machine wash', 'lounge area', 'air fresheners']
def get_data(latitude, longitude, miles_radius, price, amenities) -> list or None:
    car_wash_json = []
    if int(latitude) == 50 and int(longitude) == 14:
        car_wash_json = PRAGUE_CAR_WASH
    elif int(latitude) == 48 and int(longitude) == 11:
        car_wash_json = MUNICH_CAR_WASH
    elif int(latitude) == 52 and int(longitude) == 0:
        car_wash_json = STUTTGART_CAR_WASH
    else:
        return []

    response = car_wash_json
    if amenities == None:
        amenities=''
    if amenities.lower() not in additional_amenities:
        return [
            car_wash
            for car_wash in response
            if car_wash["distance"] <= miles_radius
               and car_wash["price"] <= price
        ]
    else:
        return [
            car_wash
            for car_wash in response
            if car_wash["distance"] <= miles_radius
               and car_wash["price"] <= price
               and car_wash["additional_amenities"] == amenities
        ]


@car_wash_protocol.on_message(model=CarWashRequest, replies=UAgentResponse)
async def on_message(ctx: Context, sender: str, msg: CarWashRequest):
    ctx.logger.info(f"Received message from {sender}.")
    try:
        data = get_data(msg.miles_radius, msg.additional_amenities, msg.price)
        request_id = str(uuid.uuid4())
        options = []
        ctx_storage = {}
        for idx, o in enumerate(data):
            option = f"""● This is Car Wash: {o['name']} which is located at {o['distance']} miles away from the location
            \n● Price is €{o["price"]}\n● Additional amenity is {o["additional_amenities"]} """
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
                    message="No car wash are available for this context",
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


agent.include(car_wash_protocol)
agent.include(booking_proto())
