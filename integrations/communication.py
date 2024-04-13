import requests
from prettyprinter import pprint 
from uagents import Agent, Bureau, Context, Model

class Message(Model):
    message: str

sneha = Agent(name="sneha", seed="sneha recovery phrase")
sarvesh = Agent(name="sarvesh", seed="sarvesh recovery phrase")

@sneha.on_interval(period=3.0)
async def send_message(ctx: Context):
    await ctx.send(sarvesh.address, Message(message="Choose a genre: \n1] Search song,artist, album name \n2] For searching Artist by ID \n"))

@sneha.on_message(model=Message)
async def sneha_message_handler(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")
    genre_choice = int(msg.message.split(": ")[1]) 
    if genre_choice == 1:
        url = "https://spotify23.p.rapidapi.com/search/"
        name=input("name \n")
        type=input("enter type / gener\n")
        querystring = {"q":{name},"type":{type},"offset":"0","limit":"10","numberOfTopResults":"5"}

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
            print(f"Album: {album_name}")
            print(f"Artist(s): {album_artist}")
            print(f"Year: {album_year}")
            print()

        #pprint(response.json())
        await ctx.send(sarvesh.address, Message(message="\n\t\t*******List ends here!*******\n"))
        
    elif genre_choice == 2:
          
        url = "https://spotify23.p.rapidapi.com/artists/"

        artist=input("Enter artist ID\n")
        querystring = {"ids":{artist}}
        
        headers = {
	"X-RapidAPI-Key": "fc8fefb3b8msh5d29019bd67d5a0p12fb83jsne1ae36064299",
	"X-RapidAPI-Host": "spotify23.p.rapidapi.com"
}

        response = requests.get(url, headers=headers, params=querystring)
        file=response.json()
        for album in file['artists']:
            name=album['name']
            geners=album['genres']
            artist=album['external_urls']
            userli=album['uri']
            print(f"\n {name}\n {geners}\n{userli}\n{artist}\n")
            
        
@sarvesh.on_message(model=Message)
async def sarvesh_message_handler(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")
    genre_choice = int(input("Enter the number corresponding to the genre you choose: "))
    await ctx.send(sneha.address, Message(message=f"Chosen genre: {genre_choice}"))

bureau = Bureau()
bureau.add(sneha)
bureau.add(sarvesh)
if __name__ == "__main__":
    bureau.run()
