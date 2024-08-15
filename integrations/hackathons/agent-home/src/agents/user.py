from uagents import Agent, Context
from uagents.setup import fund_agent_if_low
import sys, os
sys.path.append(os.getcwd())
from utils.utils import plan_requests, create_message
from src.messages.models import request_keys ,request_description, LightsResponse , ACResponse , WindowResponse

# to communicate with the restaurant agent, we need to know its address
ROOM_ADDRESS = "agent1q2fx7yq8r030f23pewqxx7x8cg32fs8cjdewwf097z29kkvtn2zdsqahd6f"
 
user = Agent(
    name="user",
    port=8000,
    seed="user secret phrase",
    endpoint=["http://127.0.0.1:8000/submit"],
)
 
user.storage.set("completed", True)
fund_agent_if_low(user.wallet.address())
 
@user.on_interval(period=5)
async def interval(ctx: Context):
    completed = ctx.storage.get("completed")
 
    if completed:
        # ask user for new instructions, taking into account the user's input
        inp = input("Enter your instructions: ")
        ctx.storage.set("completed", False)
        sub_tasks:str = plan_requests(inp)    # returns a dictionary of sub-tasks with protocol as key and sub-task as value
        start_idx , end =  sub_tasks.index('{') , sub_tasks.rindex('}')
        sub_tasks = eval(sub_tasks[start_idx:end+1])


        print('sub_tasks' , sub_tasks)

        for protocol, sub_task in sub_tasks.items():
            msg = await create_message(sub_task, request_keys[protocol] ,request_description,  protocol)
            print('msg' , msg)
            await ctx.send(ROOM_ADDRESS, msg)

        ctx.storage.set("completed", True)

    else:
        ctx.logger.info("Waiting for the current request to be completed")


@user.on_message(model = LightsResponse)
async def handle_lights_response(ctx: Context, sender: str, msg: LightsResponse):
    ctx.logger.info(msg.success_str)

@user.on_message(model = ACResponse)
async def handle_ac_response(ctx: Context, sender: str, msg: ACResponse):
    ctx.logger.info(msg.success_str)

@user.on_message(model = WindowResponse)
async def handle_window_response(ctx: Context, sender: str, msg: WindowResponse):
    ctx.logger.info(msg.success_str)



 
# if __name__ == "__main__":
#     user.run()