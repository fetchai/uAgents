import asyncio

from protocols.query import GetTotalQueries, TotalQueries

from uagents.contrib.protocols.protocol_query import ProtocolQuery, ProtocolResponse
from uagents.query import query


RESTAURANT_ADDRESS = "agent1qfpqn9jhvp9cg33f27q6jvmuv52dgyg9rfuu37rmxrletlqe7lewwjed5gy"


async def main():
    env = await query(RESTAURANT_ADDRESS, GetTotalQueries())
    msg = TotalQueries.parse_raw(env.decode_payload())
    print(f"Query response: {msg.json()}\n\n")

    env = await query(RESTAURANT_ADDRESS, ProtocolQuery())
    msg = ProtocolResponse.parse_raw(env.decode_payload())
    print("Protocol query response:", msg.json(indent=4))


if __name__ == "__main__":
    asyncio.run(main())
