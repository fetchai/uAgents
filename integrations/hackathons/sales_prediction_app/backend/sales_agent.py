# sales_agent.py
from uagents import Agent, Context
from pydantic import BaseModel
import joblib
import pandas as pd

# Define a Pydantic model for the message
class SalesPredictionRequest(BaseModel):
    QUANTITYORDERED: float
    PRICEEACH: float
    MSRP: float

# Initialize the agent with a name and a seed phrase for reproducibility
sales_agent = Agent(name="sales_prediction_agent", seed="sales_prediction_agent_seed")

# Load the pre-trained sales prediction model
model = joblib.load('/Users/prathmesh/Downloads/hackathon/sales_prediction_updated 2/models/sales_prediction_model.pkl')

# Define the task for the agent: predicting sales based on input features
@sales_agent.on_message(SalesPredictionRequest)
async def predict_sales(ctx: Context, features: SalesPredictionRequest):
    df = pd.DataFrame([features.dict()])
    prediction = model.predict(df)[0]
    await ctx.send({"prediction": prediction})

# Run the agent if this script is executed directly
if __name__ == "__main__":
    sales_agent.run()
