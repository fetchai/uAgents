import uuid
import requests
from ai_engine import UAgentResponse, UAgentResponseType, KeyValue
from pydantic import Field
import os
from dotenv import load_dotenv

load_dotenv()

TRIPADVISOR_API_KEY = os.getenv("TRIPADVISOR_API_KEY")
MAP_GEOCODING_API_KEY = os.getenv("MAP_GEOCODING_API_KEY")


class HotelRequest(Model):
    address: str = Field(
        description="name of place where user wants to book a hotel. takes the response from travel advisor system."
    )
    checkIn: str = Field(
        description="date of check in, the date on which user wants to book a hotel."
    )
    checkOut: str = Field(
        description="date of check out, the date on which user will leave the hotel."
    )
    rooms: int = Field(description="number of rooms user want to book in hotel.")

class BookHotelRequest(Model):
    bookquery: str = Field(description="takes the response from the hotel booking details system.")


book_hotel_protocol = Protocol("BookHotelWithName")
hotel_booking_details_protocol = Protocol("HotelBooking")

def reform_data(api_response):
    refactored_data = []
    name=""
    price=""

    for hotel in api_response["data"]["data"]:
        name = hotel["title"]
        price = hotel["priceForDisplay"]
        refactored_data.append(f"""● Hotel: {name} - Price: {price}\n""")
    return refactored_data


def get_data(address, checkIn, checkOut, rooms) -> list or None:

    url = "https://tripadvisor16.p.rapidapi.com/api/v1/hotels/searchHotelsByLocation"

    headers = {
        "X-RapidAPI-Key": TRIPADVISOR_API_KEY,
        "X-RapidAPI-Host": "tripadvisor16.p.rapidapi.com"
    }

    geourl = "https://map-geocoding.p.rapidapi.com/json"

    geoquerystring = {"address": address}

    geoheaders = {
        "X-RapidAPI-Key": MAP_GEOCODING_API_KEY,
        "X-RapidAPI-Host": "map-geocoding.p.rapidapi.com"
    }
    print("here")
    georesponse = requests.get(geourl, headers=geoheaders, params=geoquerystring)
    georesponse = georesponse.json()
    lat = georesponse['results'][0]['geometry']['location']['lat']
    lng = georesponse['results'][0]['geometry']['location']['lng']
    print(f"{lat} {lng}")
    querystring = {"latitude":lat,"longitude":lng,"checkIn":checkIn,"checkOut":checkOut,"pageNumber":"1","rooms":rooms,"currencyCode":"INR"}
    response = requests.get(url, headers=headers, params=querystring)
    
    if response.status_code == 200:
        data = response.json()
        return reform_data(data)
    else:
        return None

@book_hotel_protocol.on_message(model=BookHotelRequest, replies=UAgentResponse)
async def book_hotel(ctx: Context, sender: str, msg: BookHotelRequest):
    ctx.logger.info(f"Received booking message from {sender}")
    name = msg.bookquery.split("-")[0]
    ctx.logger.info(f"{name}")

    print(x.text)
    await ctx.send(
                sender,
                UAgentResponse(
                    message=f"{name} booked successfully",
                    type=UAgentResponseType.FINAL,
                    public_manifest=True
                )
            )

@hotel_booking_details_protocol.on_message(model=HotelRequest, replies=UAgentResponse)
async def on_message(ctx: Context, sender: str, msg: HotelRequest):
    ctx.logger.info(f"Received message from {sender}")
    try:
        checkIn = "-".join(msg.checkIn.split(".")[::-1])
        checkOut = "-".join(msg.checkOut.split(".")[::-1])
        
        ctx.logger.info(f"{msg.address}, {checkIn}, {checkOut}, {msg.rooms}")

        response = get_data(msg.address, checkIn, checkOut, msg.rooms)
        response = "\n".join(response)
        ctx.logger.info(f"response {response}")

        if(response):
            await ctx.send(
                sender,
                UAgentResponse(
                    message=str(response),
                    type=UAgentResponseType.FINAL,
                    public_manifest=True
                )
            )
        else:
            await ctx.send(
                sender,
                UAgentResponse(
                    message="No options are available for this context",
                    type=UAgentResponseType.FINAL,
                    public_manifest=True
                )
            )
    except Exception as exc:
        ctx.logger.error(exc)
        await ctx.send(
            sender,
            UAgentResponse(
                message=str(exc),
                type=UAgentResponseType.ERROR,
                    public_manifest=True
            )
        )


agent.include(hotel_booking_details_protocol)
agent.include(book_hotel_protocol)