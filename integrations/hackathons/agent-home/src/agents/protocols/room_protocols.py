from uagents import Context, Model, Protocol
import os, sys
sys.path.append(os.getcwd())
from src.messages.models import LightsRequest, LightsResponse, ACRequest, ACResponse, WindowRequest, WindowResponse
light_proto = Protocol()

@light_proto.on_message(model=LightsRequest, replies=LightsResponse)
async def handle_lights_request(ctx: Context, sender: str, msg: LightsRequest):
    success_str=""
    success_str=""
    if ctx.storage.get("lights") == msg.on:
        success_str = f"Lights are already in the {('on' if msg.on == 1 else 'off')} state"
    
    else:
        ctx.storage.set("lights", msg.on)
        # success_str = f"Lights have been turned {msg.on}"
        success_str = f"Lights have been turned {'on' if msg.on == 1 else 'off'}"

    await ctx.send(sender, LightsResponse(success_str=success_str))


ac_proto = Protocol()

@ac_proto.on_message(model=ACRequest, replies=ACResponse)
async def handle_ac_request(ctx: Context, sender: str, msg: ACRequest):
    success_str =""
    if msg.on:
        if ctx.storage.get("ac")[0] == 0:
            success_str = "switching on the AC"
        if ctx.storage.get("ac")[1] != msg.temperature:
            ctx.storage.set("ac", (1, msg.temperature))
        success_str = f", setting it to {msg.temperature} degrees"
    
    else:
        if ctx.storage.get("ac")[0] == 1:
            success_str = "switching off the AC"
        ctx.storage.set("ac", (0, 25))

    await ctx.send(sender, ACResponse(success_str=success_str))


window_proto = Protocol()

@window_proto.on_message(model=WindowRequest, replies=WindowResponse)
async def handle_window_request(ctx: Context, sender: str, msg: WindowRequest):
    success_str=""
    # checking if windows are open or not
    state = 'closed' if msg.open == 0 else 'opened'
    if ctx.storage.get("window")[0] == msg.open:
        success_str = f"Windows are already in the {state}."
    else:
        ctx.storage.set("window", (msg.open, ctx.storage.get("window")[1]))
        success_str = f"Windows have been {state}."

    # checking if curtains are put or not
    state = 'put' if msg.put_curtains == 1 else 'not put'
    if ctx.storage.get("window")[1] == msg.put_curtains:
        success_str += f"\nCurtains are already {state}."
    else:
        ctx.storage.set("window", (ctx.storage.get("window")[0]  ,msg.put_curtains))
        success_str += f"\nCurtains have been {state}."

    await ctx.send(sender, WindowResponse(success_str=success_str))

    
    