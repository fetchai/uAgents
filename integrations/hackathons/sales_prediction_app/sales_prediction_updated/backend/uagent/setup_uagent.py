from uagents import Agent, Context
import joblib
import pandas as pd
import os

# Initialize the agent with a name and a seed phrase for reproducibility
sales_agent = Agent(name="sales_prediction_agent", seed="sales_prediction_agent_seed")

# Construct the absolute path to the model file
current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, 'models', 'sales_model.pkl')

# Debug: Print the current working directory and the model path
print(f"Current working directory: {os.getcwd()}")
print(f"Model path: {model_path}")

# Debug: List all files in the expected model directory
model_dir = os.path.dirname(model_path)
if os.path.exists(model_dir):
    print(f"Files in model directory: {os.listdir(model_dir)}")
else:
    print(f"Model directory does not exist: {model_dir}")

if not os.path.exists(model_path):
    raise FileNotFoundError(f"Model file not found at path: {model_path}")

# Load the pre-trained sales prediction model
model = joblib.load(model_path)

# Define the task for the agent: predicting sales based on input features
@sales_agent.on_event("predict_sales")
async def predict_sales(ctx: Context, features: dict):
    # Convert the features to a DataFrame
    df = pd.DataFrame([features])
    # Predict sales using the model
    prediction = model.predict(df)[0]
    # Send the prediction as a response
    await ctx.send(prediction)

# Run the agent
if __name__ == "__main__":
    sales_agent.run()
