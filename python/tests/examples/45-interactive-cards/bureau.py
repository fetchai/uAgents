from uagents import Agent, Bureau, Context
from uagents_core.contrib.protocols.chat import ChatMessage, TextContent

from protocols import host_proto, picker_proto

menu_host = Agent(name="menu-host")
menu_host.include(host_proto)

picker = Agent(name="picker")
picker.include(picker_proto)


@picker.on_event("startup")
async def request_menu(ctx: Context):
    await ctx.send(menu_host.address, ChatMessage([TextContent("menu")]))


bureau = Bureau()
bureau.add(menu_host)
bureau.add(picker)

if __name__ == "__main__":
    bureau.run()
