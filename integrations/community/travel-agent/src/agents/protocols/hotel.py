from pydantic import BaseModel
from typing import List
from uagents import Context, Protocol
from h_agent import fetch_hotel


class HotelQuery(BaseModel):
    check_in_date: str
    check_out_date: str
    query: str


class HotelResponse(BaseModel):
    names: List[str]
    rates: List[str]
    links: List[str]
    emails: List[str]


hotel_proto = Protocol()


def fetch_hotels(q: HotelQuery) -> List[List[str]]:
    hotels = fetch_hotel(q.check_in_date, q.check_out_date, q.query)
    return hotels[0], hotels[1], hotels[2], hotels[3]


@hotel_proto.on_message(HotelQuery, replies=HotelResponse)
async def handle_hotel_query(ctx: Context, sender: str, msg: HotelQuery):
    names, rates, links, emails = fetch_hotels(msg)
    await ctx.send(
        sender, HotelResponse(names=names, rates=rates, links=links, emails=emails)
    )
