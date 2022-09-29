from pydantic import BaseModel

from nexus import Agent, Bureau, Context


class Message(BaseModel):
    message: str


alice = Agent()
bob = Agent()


@alice.on_interval(period=3.0)
async def send_message(ctx: Context):
    print('Sending the message to Bob...')
    await ctx.send(bob.address, Message(message='hello there bob'))


@bob.on_interval(period=1.0)
async def interval(ctx: Context):
    print('Interval')


@bob.on_message(model=Message)
async def recv_message(ctx: Context, sender: str, msg: Message):
    print(f'Received msg from: {sender}', msg)


# since we have multiple agents in this example we add them to a bureau
bureau = Bureau()
bureau.add(alice)
bureau.add(bob)

if __name__ == '__main__':
    bureau.run()
