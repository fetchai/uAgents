from uagents.setup import fund_agent_if_low
from uagents import Agent, Context, Model

class PumpingInformation(Model):
    quantity: float
    routines: int
    per: str

class Message(Model):
    message: str

pump_agent = Agent(
    name="Pump Controlling Agent",
    port=8000,
    seed="pump secret code",
    endpoint=["http://127.0.0.1:8000/submit"],
)

DECIDER_ADDRESS = "agent1qw29fkzs8jesevtd4wc5du7av9l24rf6vjswaz6krk20j449ar302m958ly"
fund_agent_if_low(pump_agent.wallet.address())

@pump_agent.on_message(model=PumpingInformation)
async def message_handler(ctx: Context, sender: str, msg: PumpingInformation):
    ctx.logger.info(f"Received pumping instruction from Decision Agent")
    ctx.logger.info(
        f'''
    ##############################################################
            Irrigation Instructions: 
                Amount of water: {msg.quantity}
                Intervals: {msg.routines} per {msg.per}
    ##############################################################
        ''' 
    )
if __name__ == "__main__":
    pump_agent.run()

# print(pump_agent.address)