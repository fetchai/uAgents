from pydantic import Field
from ai_engine import UAgentResponse, UAgentResponseType

class Spotify(Model):
    Singer: str =Field(description="Enter Singer")
    genre: str=Field(description="Enter A Genre")



Spotify_protocol = Protocol("Spotify")


@Spotify_protocol.on_message(model=Spotify, replies={UAgentResponse})
async def Search(ctx: Context, sender: str, msg: Spotify):
    
     
    url = "https://spotify23.p.rapidapi.com/search/"    
    querystring = {"q":{msg.Singer},"type":{msg.genre},"offset":"0","limit":"10","numberOfTopResults":"5"}

    headers = {
	"X-RapidAPI-Key": "fc8fefb3b8msh5d29019bd67d5a0p12fb83jsne1ae36064299",
	"X-RapidAPI-Host": "spotify23.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    file=response.json()
        
    for album in file['albums']['items']:
            album_name = album['data']['name']
            album_artist = ', '.join(artist['profile']['name'] for artist in album['data']['artists']['items'])
            album_year = album['data']['date']['year']
            message = f"Album: {album_name}\nArtist(s): {album_artist}\nYear: {album_year}"
            await ctx.send(
        sender, UAgentResponse(message=message, type=UAgentResponseType.FINAL)
    )
            break
agent.include(Spotify_protocol, publish_manifest=True)