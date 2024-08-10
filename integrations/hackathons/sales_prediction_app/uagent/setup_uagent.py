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
@sales_agent.on_message(SalesPredictionRequest)  # Use the Pydantic model
async def predict_sales(ctx: Context, features: SalesPredictionRequest):
    # Convert the features to a DataFrame
    df = pd.DataFrame([features.dict()])  # Use .dict() to convert to a dictionary
    
    # Predict sales using the model
    prediction = model.predict(df)[0]
    
    # Send the prediction as a response
    await ctx.send({"prediction": prediction})

# Run the agent if this script is executed directly
if __name__ == "__main__":
    sales_agent.run()
