# Here we demonstrate how we can create a DeltaV compatible agent responsible for finding a nearby restaurant based
# on a location given by the user. After running this agent, it can be registered to DeltaV on Agentverse's Services
# tab. For registration, you will have to use the agent's address.
#
# third party modules used in this example
import uuid

from ai_engine import KeyValue
from ai_engine import UAgentResponse, UAgentResponseType
from pydantic import Field

# placeholder for a function that can retrieve real up-to-date restaurant data
from restaurant_data import PRAGUE_RESTAURANT, MUNICH_RESTAURANT, STUTTGART_RESTAURANT
# modules from booking_protocol.py
from booking_protocol import booking_proto

restaurant_protocol = Protocol("Restaurants")


class Restaurant(Model):
    latitude: float = Field(description="Describes the latitude where the user wants a restaurant. This might not "
                                        "be the user current location, if user specified a specific location on the"
                                        " objective.")
    longitude: float = Field(
        description="Describes the longitude where the user wants a restaurant. This might not be the user current "
                    "location, if user specified a specific location on the objective.")
    miles_radius: float = Field(
        description="Distance in miles, the maximum distance b/w restaurant and the location provided by user.")
    additional_amenities: Optional[str] = Field(
        description="This field describes the cuisine type, for example: Italian, Chinese, Mexican, Lebanese,Vegan,"
                    "Vegetarian. Defaults to Italian.")
    cuisine_type: Optional[str] = Field(
        description="This field describes the additional amenities, for example: Online Ordering, Private Dining "
                    "Rooms, Special Dietary Menus, Outdoor Seating. Defaults to Online Ordering.")



cuisine_types = ['italian', 'chinese', 'vegan', 'lebanese']
additonal_amenties = ['online ordering', 'private dining Rooms', 'special dietary menus', 'outdoor seating']
removed_items = ["undefined", "unknown", "none", "null", ""]
def get_data(latitude, longitude, miles_radius, amenities=None, cuisine=None) -> list or None:
    restaurants_json = []
    if int(latitude) == 50 and int(longitude) == 14:
        restaurants_json = PRAGUE_RESTAURANT
    elif int(latitude) == 48 and int(longitude) == 11:
        restaurants_json = MUNICH_RESTAURANT
    elif int(latitude) == 48 and int(longitude) == 9:
        restaurants_json = STUTTGART_RESTAURANT
    else:
        return []
    if amenities is None:
        amenities = ""
    if cuisine is None:
        cuisine = ""

    data = restaurants_json
    response = [restaurant for restaurant in data if (not miles_radius or restaurant["distance"] <= miles_radius) and (amenities.lower() in removed_items or restaurant["additional_amenities"].lower() == amenities.lower()) and (cuisine.lower() in removed_items or restaurant["cuisine_type"].lower() == cuisine.lower())]
    return response


@restaurant_protocol.on_message(model=Restaurant, replies=UAgentResponse)
async def on_message(ctx: Context, sender: str, msg: Restaurant):
    ctx.logger.info(f"Received message from {sender}.")
    try:
        data = get_data(msg.miles_radius, msg.additional_amenities, msg.cuisine_type)
        request_id = str(uuid.uuid4())
        options = []
        ctx_storage = {}
        for idx, o in enumerate(data):
            option = f"""● This is Restaurant: {o['name']} which is located {o['distance']} miles away from location 
            ● Additional amenity is {o["additional_amenities"]} ● Cuisine type is {o["cuisine_type"]}"""
            options.append(KeyValue(key=idx, value=option))
            ctx_storage[idx] = option
        ctx.storage.set(request_id, ctx_storage)
        if options:
            await ctx.send(sender,
                           UAgentResponse(options=options, type=UAgentResponseType.SELECT_FROM_OPTIONS,
                                          request_id=request_id))
        else:
            await ctx.send(sender,
                           UAgentResponse(message="No restaurant are available for this context",
                                          type=UAgentResponseType.FINAL,
                                          request_id=request_id))

    except Exception as exc:
        ctx.logger.error(exc)
        await ctx.send(sender, UAgentResponse(message=str(exc), type=UAgentResponseType.ERROR))


agent.include(restaurant_protocol)
agent.include(booking_proto)
