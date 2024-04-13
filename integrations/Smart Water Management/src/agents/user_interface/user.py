from uagents.setup import fund_agent_if_low
from uagents import Agent, Context, Model

class FarmData(Model):
    city: str
    crop_type: str
    farm_size: int
    soil_type: str
    stage_of_growth: str
    crop_density: int
    soil_moisture: int


user = Agent(
    name="USER1",
    port=8003,
    seed="user secret code",
    endpoint=["http://127.0.0.1:8003/submit"],
)

fund_agent_if_low(user.wallet.address())

DECIDER_ADDRESS = "agent1qw29fkzs8jesevtd4wc5du7av9l24rf6vjswaz6krk20j449ar302m958ly"

@user.on_event("startup")
async def start(ctx: Context):
    city = input("Enter city: ")
    crop_type = input("Enter crop type: ")
    farm_size = int(input("Enter farm size: "))
    soil_type = input("Enter soil type: ")
    stage_of_growth = input("Enter stage of growth: ")
    crop_density = int(input("Enter crop density: "))
    soil_moisture = int(input("Enter soil moisture: "))
    await ctx.send(DECIDER_ADDRESS,FarmData(city=city,crop_type=crop_type,farm_size=farm_size,soil_type=soil_type,stage_of_growth=stage_of_growth,crop_density=crop_density,soil_moisture=soil_moisture))
    ctx.logger.info(
        f'''
    ###########################################################
        Following information was sent to the Decision Agent
        City: {city}
        Crop Type: {crop_type}
        Farm Size: {farm_size} 
        Soil Type: {soil_type} 
        Stage of Growth: {stage_of_growth} 
        Crop Density: {crop_density}
        Soil Moisture: {soil_moisture} 
    ###########################################################
        '''
    )
user.run()
