from uagents import Agent, Bureau, Context
from uagents.experimental.chat_agent import ChatAgent
from uagents_core.contrib.protocols.chat import ChatMessage, TextContent

from protocols import listen_proto, word_counter_proto

space_expert = ChatAgent(
    name="space-expert",
    instructions="You are an expert in deep space exploration.",
)

word_counter = ChatAgent(name="word-counter")

word_counter.include(word_counter_proto)

questioner = Agent(name="questioner")
questioner.include(listen_proto)


@questioner.on_event("startup")
async def ask_experts(ctx: Context):
    await ctx.send(
        space_expert.address,
        ChatMessage(
            [TextContent("What is the probability of life existing on the moon?")]
        ),
    )
    await ctx.send(
        word_counter.address,
        ChatMessage([TextContent("Count the words in this sentence.")]),
    )


bureau = Bureau()
bureau.add(space_expert)
bureau.add(word_counter)
bureau.add(questioner)

if __name__ == "__main__":
    bureau.run()
