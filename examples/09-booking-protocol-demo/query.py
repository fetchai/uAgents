import asyncio

from protocols.query import GetTotalQueries

from uagents.query import query


RESTAURANT_ADDRESS = "agent1qw50wcs4nd723ya9j8mwxglnhs2kzzhh0et0yl34vr75hualsyqvqdzl990"

get_total_queries = GetTotalQueries()


async def main():
    env = await query(RESTAURANT_ADDRESS, get_total_queries)
    print(f"Query response: {env.decode_payload()}")


if __name__ == "__main__":
    asyncio.run(main())
