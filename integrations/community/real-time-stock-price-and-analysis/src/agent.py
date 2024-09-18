import requests
from ai_engine import UAgentResponse, UAgentResponseType
from uagents import Agent, Context, Protocol, Model

# Yahoo Finance API parameters
RAPIDAPI_KEY = "<RAPIDAPI_KEY>"
RAPIDAPI_HOST = "yahoo-finance127.p.rapidapi.com"


async def get_stock_data(symbol):
    # Fetches historical stock data for the given symbol using the Yahoo Finance API.
    url = f"https://yahoo-finance127.p.rapidapi.com/search/{symbol}"
    headers = {"X-RapidAPI-Key": RAPIDAPI_KEY, "X-RapidAPI-Host": RAPIDAPI_HOST}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception if the request was unsuccessful
        data = response.json()

        if "quotes" in data:
            stock_data = {}
            for quote in data["quotes"]:
                date = quote["date"]
                stock_data[date] = {
                    "open": float(quote["open"]),
                    "high": float(quote["high"]),
                    "low": float(quote["low"]),
                    "close": float(quote["close"]),
                    "volume": float(quote["volume"]),
                }
            return stock_data
        elif "error" in data:
            print(f"Error fetching data for {symbol}: {data['error']}")
            return None
        else:
            print(f"Unexpected response format for {symbol}: {data}")
            return None
    except requests.exceptions.RequestException as e:  # exception statement
        print(f"Error fetching data for {symbol}: {e}")
        return None


stock_protocol = Protocol("stockProtocol")


class StockInfo(Model):
    # Model to represent stock data.
    symbol: str
    price: Optional[str]
    change: Optional[str]


@stock_protocol.on_message(model=StockInfo, replies=UAgentResponse)
async def on_message(ctx: Context, sender: str, msg: StockInfo):
    # Handles user messages containing stock ticker symbols.

    ctx.logger.info(f"Received message from {sender}: {msg.symbol}")

    try:
        # Validate and sanitize user input (e.g., check for valid symbol format)
        if not msg.symbol.isalnum():
            await ctx.send(
                sender,
                UAgentResponse(
                    message="Invalid stock symbol format", type=UAgentResponseType.ERROR
                ),
            )
            return

        data = await get_stock_data(msg.symbol.upper())

        if data:
            # Extract relevant data and format response message
            latest_date = list(data.keys())[-1]
            price = data[latest_date]["close"]
            change = str(
                float(data[latest_date]["close"])
                - float(data[list(data.keys())[-2]]["close"])
            )
            message = f"Stock information for {msg.symbol.upper()}:\n Price: {price}\n Change: {change}"
            await ctx.send(
                sender, UAgentResponse(message=message, type=UAgentResponseType.FINAL)
            )
        else:
            await ctx.send(
                sender,
                UAgentResponse(
                    message="Stock data not available", type=UAgentResponseType.FINAL
                ),
            )

    except ValueError as e:
        ctx.logger.error(f"Error parsing data for {msg.symbol}: {e}")
        await ctx.send(
            sender,
            UAgentResponse(
                message="An error occurred while parsing the data",
                type=UAgentResponseType.ERROR,
            ),
        )
    except KeyError as e:
        ctx.logger.error(f"Error accessing data for {msg.symbol}: {e}")
        await ctx.send(
            sender,
            UAgentResponse(
                message="An error occurred while accessing the data",
                type=UAgentResponseType.ERROR,
            ),
        )
    except requests.exceptions.RequestException as e:
        ctx.logger.error(f"Error fetching data for {msg.symbol}: {e}")
        await ctx.send(
            sender,
            UAgentResponse(
                message="An error occurred while fetching the data",
                type=UAgentResponseType.ERROR,
            ),
        )
    except Exception as e:
        ctx.logger.error(f"Unexpected error occurred for {msg.symbol}: {e}")
        await ctx.send(
            sender,
            UAgentResponse(
                message="An unexpected error occurred", type=UAgentResponseType.ERROR
            ),
        )


agent = Agent()
agent.include(stock_protocol, publish_manifest=True)
