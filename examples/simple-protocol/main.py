from pydantic import BaseModel

from nexus import Agent, Bureau, Context


class Message(BaseModel):
    message: str


alice = Agent(name='alice')
bob = Agent(name='bob')


@alice.on_interval(period=3.0)
async def send_message(ctx: Context):
    await ctx.send(bob.address, Message(message='hello there bob'))


@alice.on_message(model=Message)
async def recv_message_a(ctx: Context, sender: str, msg: Message):
    print(f'[{ctx.name:5}] From: {sender} {msg.message}')


@bob.on_message(model=Message)
async def recv_message(ctx: Context, sender: str, msg: Message):
    print(f'[{ctx.name:5}] From: {sender} {msg.message}')

    # send the response
    await ctx.send(alice.address, Message(message='hello there alice'))


# since we have multiple agents in this example we add them to a bureau (just an "office" for agents)
bureau = Bureau()
bureau.add(alice)
bureau.add(bob)

if __name__ == '__main__':
    bureau.run()
