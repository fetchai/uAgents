from uagents.setup import fund_agent_if_low
from uagents import Agent, Context, Model, Protocol
import math
cities ={
    "Delhi": {
        "lat": 28.704,
        "lon": 77.103
    },
    "Mumbai": {
        "lat": 19.076,
        "lon": 72.878
    },
    "Kolkata": {
        "lat": 22.573,
        "lon": 88.364
    },
    "Bangalore": {
        "lat": 12.972,
        "lon": 77.595
    },
    "Chennai": {
        "lat": 13.083,
        "lon": 80.271
    },
    "Hyderabad": {
        "lat": 17.385,
        "lon": 78.487
    },
    "Pune": {
        "lat": 18.52,
        "lon": 73.857
    },
    "Ahmedabad": {
        "lat": 23.023,
        "lon": 72.571
    },
    "Surat": {
        "lat": 21.17,
        "lon": 72.831
    },
    "Jaipur": {
        "lat": 26.912,
        "lon": 75.787
    },
    "Lucknow": {
        "lat": 26.847,
        "lon": 80.946
    },
    "Kanpur": {
        "lat": 26.45,
        "lon": 80.332
    },
    "Nagpur": {
        "lat": 21.146,
        "lon": 79.088
    },
    "Visakhapatnam": {
        "lat": 17.687,
        "lon": 83.219
    },
    "Indore": {
        "lat": 22.72,
        "lon": 75.858
    },
    "Thane": {
        "lat": 19.218,
        "lon": 72.978
    },
    "Bhopal": {
        "lat": 23.26,
        "lon": 77.413
    },
    "Agra": {
        "lat": 27.177,
        "lon": 78.008
    }
}
#incoming data; from interface agent
sugarcane_water_required = {
    "InitialStage": 3.5,
    "GrandGrowth": 4.5,
    "Maturation": 2.3
}
class FarmData(Model):
    city: str
    crop_type: str
    farm_size: int
    soil_type: str
    stage_of_growth: str
    crop_density: int
    soil_moisture: int

#incoming data; from weather-agent
class WeatherData(Model):
    farm_data: FarmData
    temperature: float
    humidity: float
    rainfall: float

#outgoing data; to weather-agent
class QueryWeather(Model):
    farm_data: FarmData
    requester_address: str
    lon : float
    lat : float
    unit: str
    prod: str

#outgoing data; to pump-agent
class PumpingInformation(Model):
    quantity: float
    routines: int
    per: str

class Message(Model):
    msg: str

decider_agent = Agent(
    name="Decision Making Agent",
    port=8002,
    seed="decision secret code",
    endpoint=["http://127.0.0.1:8002/submit"],
)

PUMP_ADDRESS = "agent1qvrjy9qqv0q9vs9894mlrsaus9gr8esp88u24eymlplx8kemgy7aj388n62"
WEATHER_ADDRESS = "agent1qtpjw3vfd0hx7a569c02pjnk3emn6vzatva3cgw5u4zhn46344pcszw5s2j"
fund_agent_if_low(decider_agent.wallet.address())

@decider_agent.on_message(model=FarmData)
async def farm_data_handler(ctx: Context, sender: str,fd: FarmData):
    ctx.logger.info(f'''
    ###############################################################
    Data received from user agent
        City: {fd.city}
        Crop Type: {fd.crop_type}
        Farm Size: {fd.farm_size} 
        Soil Type: {fd.soil_type} 
        Stage of Growth: {fd.stage_of_growth} 
        Crop Density: {fd.crop_density}
        Soil Moisture: {fd.soil_moisture} 
    ###############################################################
        ''')

    ctx.logger.info("Fetching weather information from 7timer API via weather agent")
    city = fd.city
    await ctx.send(WEATHER_ADDRESS,QueryWeather(farm_data=fd,requester_address=sender,lon=cities[city]['lon'],lat=cities[city]['lat'],unit="Metric",prod="civil"))

@decider_agent.on_message(model=WeatherData)
async def weather_data_handler(ctx: Context,sender: str,wd: WeatherData):
    fd = wd.farm_data
    ctx.logger.info(f'''
    ###############################################################                 
        Received weather data from Weather Agent
            Temperature: {wd.temperature}
            Rainfall: {wd.rainfall}
            Humidity: {wd.humidity}
        For the farm detailed below:
            City: {fd.city}
            Crop Type: {fd.crop_type}
            Farm Size: {fd.farm_size} 
            Soil Type: {fd.soil_type} 
            Stage of Growth: {fd.stage_of_growth} 
            Crop Density: {fd.crop_density}
            Soil Moisture: {fd.soil_moisture} 
    ###############################################################

    ''')
    required_water = sugarcane_water_required[fd.stage_of_growth]*fd.farm_size*fd.crop_density
    rain_water = wd.rainfall*fd.farm_size*fd.crop_density
    pump_water = max(0,required_water-rain_water)
    routines = 0
    per = "day"
    if(fd.soil_type=="sandy"):
        routines = 4
    if(fd.soil_type=="salty"):
        routines = 3
    if(fd.soil_type=="loamy"):
        routines = 2
    if(fd.soil_type=="clayey"):
        routines = 1

    await ctx.send(PUMP_ADDRESS,PumpingInformation(quantity=pump_water,routines=routines,per=per))

if __name__ == "__main__":
    decider_agent.run()