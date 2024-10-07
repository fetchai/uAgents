import requests
from datetime import datetime

from uagents import Context, Protocol, Model
from ai_engine import UAgentResponse, UAgentResponseType

class USGS_ID(Model):
    id: str

usgs_eq_protocol = Protocol("USGS Earthquake Protocol")

def get_usgs_eq_details(usgs_id):
    USGS_API_URL = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&eventid={usgs_id}"

    try:
        response = requests.get(USGS_API_URL)
        response.raise_for_status()  # http error check
        data = response.json()

        properties = data.get('properties', {})
        geometry = data.get('geometry', {})
        coordinates = geometry.get('coordinates', [])

        # format time-related strings
        time_ms = properties.get('time', 0)
        updated_ms = properties.get('updated', 0)
        time_str = datetime.utcfromtimestamp(time_ms / 1000).strftime('%Y-%m-%d %H:%M:%S UTC')
        updated_str = datetime.utcfromtimestamp(updated_ms / 1000).strftime('%Y-%m-%d %H:%M:%S UTC')

        details = (
            f"Details for Earthquake {usgs_id}\n"
            f"Title: {properties.get('title', 'N/A')}\n"
            f"Magnitude: {properties.get('mag', 'N/A')}\n"
            f"Location: {properties.get('place', 'N/A')}\n"
            f"Time: {time_str}\n"
            f"Updated: {updated_str}\n"
            f"Alert Level: {properties.get('alert', 'N/A')}\n"
            f"Felt Reports: {properties.get('felt', 'N/A')}\n"
            f"Coordinates: {coordinates[1]}, {coordinates[0]} (Lat, Long)\n"
            f"Depth: {coordinates[2]} km\n"
            f"URL: {properties.get('url', 'N/A')}"
        )

        return details

    except Exception as err:
        print(f"An error occured: {err}")


@usgs_eq_protocol.on_message(model=USGS_ID, replies={UAgentResponse})
async def process_usgs_eq_details(ctx: Context, sender: str, msg: USGS_ID):
    usgs_id = msg.id
    ctx.logger.info("Grabbing USGS earthquake details for id: " + usgs_id)
    usgs_eq_details = get_usgs_eq_details(usgs_id)
    await ctx.send(
        sender, UAgentResponse(message=usgs_eq_details, type=UAgentResponseType.FINAL)
    )

agent.include(usgs_eq_protocol, publish_manifest=True)
