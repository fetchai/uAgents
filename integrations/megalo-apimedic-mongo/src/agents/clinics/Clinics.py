from ai_engine import UAgentResponse, UAgentResponseType
from pydantic import Field

clinic_protocol = Protocol("Clinic Protocol")
bingKey = 'YOUR_BINGMAPS_KEY'

#Max Radius to check in [meters]
MAX_DISTANCE = 20000 


class LocationData(Model):
    location: str = Field("Describe in which area you are looking for help: ")


#GeoDecode Location Query into Co-ordinates
def fetchCoords(query: str, maxRes: int):
    URI = f'http://dev.virtualearth.net/REST/v1/Locations?query={query}&includeNeighborhood=true&include=true&maxResults={maxRes}&key={bingKey}'
    response = json.loads(requests.get(URI).text)
    coords = response['resourceSets'][0]['resources'][0]['point']['coordinates']
    return coords


#Get local Medical institutions close to the Location query
def getLocalSpots(coords: list[str], spot: str, distance: int):
    userLoc = f"{coords[0]},{coords[1]},{distance}"
    URI = f'https://dev.virtualearth.net/REST/v1/LocalSearch/?query=Hospitals&userLocation={userLoc}&key={bingKey}'
    response = requests.get(URI).text
    return response



#Get Local Clinics and pass onto Report Agent for report & store
@clinic_protocol.on_message(model=LocationData, replies = UAgentResponse)
async def on_locationReceived(ctx: Context, sender: str, loc: LocationData):
    try:
        queryLocation = loc.location
        localCoords = fetchCoords(queryLocation, 1)
        hospitals = getLocalSpots(localCoords, "hospitals", MAX_DISTANCE)
        ctx.send(
            sender, 
            UAgentResponse(
                message=str(hospitals), 
                type=UAgentResponseType.FINAL
            ))
    except Exception as exc:
        ctx.logger.error(exc)
        await ctx.send(sender, UAgentResponse(message=str(exc), type=UAgentResponseType.ERROR))

