from uagents import Agent, Context
import matplotlib.pyplot as plt
import requests
import datetime
from dateutil.relativedelta import relativedelta
from dotenv.main import load_dotenv
import os

agent = Agent(name="Data Visualization Agent")
load_dotenv()


@agent.on_event("startup")
async def graph_agent(ctx: Context):
    current_date = datetime.datetime.now()
    prev_month_date = current_date - relativedelta(months=1)
    new_data = dict()
    api_key = os.getenv('API_KEY')
    secret_key = os.getenv('SECRET_KEY')
    url = "https://amplitude.com/api/2/funnels"
    params = {
    'e': ['{"event_type": "stake_click"}', '{"event_type": "stake_txn_click"}', '{"event_type": "unstake_txn_click"}', '{"event_type": "redelegate_txn_click"}'],
    "start": int(prev_month_date.strftime("%Y%m%d")),
    "end": int(current_date.strftime("%Y%m%d"))

}
    response = response = requests.get(url, auth=(api_key, secret_key), params=params)
    data = response.json()
    for x,y  in enumerate(data["data"][0]["events"]):
        new_data[y]=[j for h,i in enumerate(data["data"][0]["dayFunnels"]["series"])  for j in [i[x]] if h%2==0] 
    y = [j for i,j in enumerate(data["data"][0]["dayFunnels"]["formattedXValues"]) if i%2==0]

    fig, ax = plt.subplots(figsize=(15, 8), layout='constrained')
    for key,val in new_data.items():
        ax.plot(y, val, label=key)  # Plot some data on the axes.
    ax.legend(loc="upper left")
    plt.show()


if __name__ == "__main__":
    agent.run()
