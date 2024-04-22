# Import necessary modules
from pydantic import Field
from ai_engine import UAgentResponse, UAgentResponseType
import json
import requests

# Define the Pydantic model for the database
class DataBase(Model):
    query: str = Field(description = "Your query")
    url: str = Field(description = "database URL over which you want to query")
    
# Create a protocol for the database
db_protocol = Protocol("DataBase")


# Function to send data to the server
def send_data_to_server(uri, query):
  # Extract various components from the URI
  dbtype = uri.split(":")[0]
  dbname_start = uri.rfind("/") + 1
  dbname_end = uri.find("?") if "?" in uri else len(uri)
  dbpassword_start = uri.find("://") + len("://")
  dbpassword_end = uri.find("@")
  port_start = uri.rfind(":") + 1
  port_end = uri.find("/", port_start)
  username_start = uri.find("//") + len("//")
  username_end = uri.find(":", username_start)
  host_start = uri.find("@") + 1
  host_end = uri.find(":", dbpassword_end + 1)

  # Extract each component using slicing
  dbname = uri[dbname_start:dbname_end]
  dbpassword = uri[dbpassword_start:dbpassword_end].split(":")[1]
  port = int(uri[port_start:port_end])
  username = uri[username_start:username_end]
  host = uri[host_start:host_end]
  
  server_address = f"https://2hz94136-8000.inc1.devtunnels.ms/execute?username={username}&password={dbpassword}&host={host}&port={port}&dbname={dbname}&query={query}&dbtype={dbtype}"
  
  try:
    print(server_address)
    response = requests.get(server_address)
    print("Response Status", response)

    # Parse JSON response from the server (assuming successful response)
    response_data = response.json()
    print(response_data)
    return response_data

  except Exception as e:
    print(f"Error sending data to server: {e}")
    return None  # Indicate failure

  
# Decorator for handling messages with the DataBase model
@db_protocol.on_message(model=DataBase, replies={UAgentResponse})
async def toss_coin(ctx: Context, sender: str, msg: DataBase):
    query = msg.query # Extract query from message
    url = msg.url # Extract URL from message
    

    # Call the function to send data to the server
    response_data = send_data_to_server(url, query)


     # Check if there is a response, otherwise set message to "Error"
    if response_data:
        message = response_data['response']
    else:
        message="Error" 
        
    # Send the response message back with UAgentResponse
    await ctx.send(
        sender, UAgentResponse(message=message, type=UAgentResponseType.FINAL)
)

# Include the database protocol with manifest publishing
agent.include(db_protocol, publish_manifest=True)