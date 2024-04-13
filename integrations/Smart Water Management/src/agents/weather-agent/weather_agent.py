from uagents.setup import fund_agent_if_low
from uagents import Agent, Context, Model
import requests

class FarmData(Model):
    city: str
    crop_type: str
    farm_size: int
    soil_type: str
    stage_of_growth: str
    crop_density: int
    soil_moisture: int

class Message(Model):
    message: str

class QueryWeather(Model):
    farm_data: FarmData
    requester_address: str
    lon : float
    lat : float
    unit: str
    prod: str

class WeatherData(Model):
    farm_data: FarmData
    temperature: float
    humidity: float
    rainfall: float

weather_agent = Agent(
    name="Weather Data Agent",
    port=8001,
    seed="weather secret code",
    endpoint=["http://127.0.0.1:8001/submit"],
)
 
def fetch_json_from_api(url):
    try:
        response = requests.get(url)
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the JSON response
            json_data = response.json()
            return json_data
        else:
            print(f"Error: Unable to fetch data from API. Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

def calculate_average(objects):
    if not objects:
        return None
    
    # Get the fields present in the first object
    fields = objects[0].keys()
    
    # Initialize dictionary to hold sums
    field_sums = {field: 0 for field in fields}
    
    # Calculate sum of each field
    for obj in objects:
        obj.pop("wind10m")
        for field, value in obj.items():
            if field == "rh2m":
                field_sums[field] += (int)(value[:-1])
            if type(value) == str:
                if value=='rain':
                    field_sums[field] = field_sums[field] + 1
            else:
                field_sums[field] += value
    
    # Calculate average of each field
    num_objects = len(objects)
    averages = {field: field_sums[field] / num_objects for field in fields}
    
    return averages

DECIDER_ADDRESS = "agent1qw29fkzs8jesevtd4wc5du7av9l24rf6vjswaz6krk20j449ar302m958ly"
fund_agent_if_low(weather_agent.wallet.address())

@weather_agent.on_message(model=QueryWeather)
async def query_handler(ctx: Context,sender: str,msg: QueryWeather):
    query = f"http://www.7timer.info/bin/api.pl?lon={msg.lon}&lat={msg.lat}&product={msg.prod}&output=json"
    data = fetch_json_from_api(query)
    final_obj = calculate_average(data['dataseries'])
    ctx.logger.info(f'''
    ############################################################
        Received Weather Request From decision agent
        Processing Data......
        Fetching weather information....
        Fetch Completed
        Details: Temperature:  {final_obj['temp2m']}
                 Humidity: {final_obj['rh2m']}
                 Rainfall: {final_obj['prec_amount']}
    ############################################################
        ''')

    await ctx.send(sender,WeatherData(farm_data=msg.farm_data,temperature=final_obj['temp2m'],humidity=final_obj['rh2m'],rainfall=final_obj['prec_amount']*100))

if __name__ == "__main__":
    weather_agent.run()
