import requests
import json

bingKey = 'Ar2PnnN71Ber0cEAkzbL41ForcU9ZPl-rEdO6MnMkvQNht9C8Buz8XQrcKTWlral'

def fetchCoords(query):
    maxRes = 5
    URI = f'http://dev.virtualearth.net/REST/v1/Locations?query={query}&includeNeighborhood=true&include=true&maxResults={maxRes}&key={bingKey}'
    response = json.loads(requests.get(URI).text)
    coords = response['resourceSets'][0]['resources'][0]['point']['coordinates']
    return coords



def getLocalSpots(coords: list[str], spot: str, distance: int):
    userLoc = f"{coords[0]},{coords[1]},{distance}"
    URI = f'https://dev.virtualearth.net/REST/v1/LocalSearch/?query=Hospitals&userLocation={userLoc}&key={bingKey}'
    response = json.loads(requests.get(URI).text)
    spots = ""
    ctr = 1
    for res in response["resourceSets"][0]["resources"]:
        name = res["name"]
        address = res["Address"]["formattedAddress"]
        phone = res["PhoneNumber"]
        site = res["Website"]
        spots += f"{ctr}.  {name}, {address}\t{phone}\nWebsite: {site}\n\n"
        ctr+=1
    return spots






# localCoords = fetchCoords("Uttaranchal University, Dehradun, Prem Nagar")
localCoords = [40.785091,-73.968285]
hospitals = getLocalSpots(localCoords, "hospitals", 20000)
clinics = getLocalSpots(localCoords, "clinics", 20000)


print(hospitals)


