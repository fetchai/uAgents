import pandas as pd
import io
from fastapi import UploadFile
from pydantic import BaseModel
from uagents import Agent, Context, Protocol
import joblib

# Load the trained model
model = joblib.load('/Users/prathmesh/Downloads/hackathon/sales_prediction_updated 2/models/sales_prediction_model.pkl')

# Request model for sales prediction
class SalesPredictionRequest(BaseModel):
    file: UploadFile  # The uploaded CSV file

# Response model for sales predictions
class SalesPredictionResponse(BaseModel):
    message: str  # The response message containing predictions
    type: str     # The type of response

async def process_csv(file: UploadFile):
    contents = await file.read()  # Read the contents of the uploaded CSV file
    df = pd.read_csv(io.BytesIO(contents))  # Load the CSV into a DataFrame
    
    # Check if required columns are present
    if 'date' not in df.columns or 'sales_amount' not in df.columns:
        raise ValueError("CSV must contain 'date' and 'sales_amount' columns.")
    
    # Convert DataFrame to a list of dictionaries
    sales_data = df[['date', 'sales_amount']].to_dict(orient='records')
    return sales_data

def predict_sales(sales_data):
    # Prepare features for prediction
    features = [[data['sales_amount']] for data in sales_data]
    predictions = model.predict(features)  # Get predictions from the model
    return predictions.tolist()

sales_prediction_protocol = Protocol("SalesPrediction")

@sales_prediction_protocol.on_message(model=SalesPredictionRequest, replies=SalesPredictionResponse)  # Use the new response model
async def on_sales_prediction_request(ctx: Context, sender: str, msg: SalesPredictionRequest):
    ctx.logger.info(f"Received sales prediction request from {sender}.")
    try:
        sales_data = await process_csv(msg.file)  # Process the uploaded CSV file
        predictions = predict_sales(sales_data)  # Get predictions

        response_message = "Sales Predictions:\n"
        for i, prediction in enumerate(predictions):
            response_message += f"Prediction for {sales_data[i]['date']}: {prediction}\n"
        
        # Send the response back to the sender using the response model
        await ctx.send(sender, SalesPredictionResponse(message=response_message, type="FINAL"))

    except Exception as exc:
        ctx.logger.error(f"Error processing sales prediction request: {exc}")
        await ctx.send(sender, SalesPredictionResponse(message=str(exc), type="ERROR"))  # Adjusted for error response

# Create the agent and include the protocol
agent = Agent()
agent.include(sales_prediction_protocol)
agent.run()  # Start the agent
