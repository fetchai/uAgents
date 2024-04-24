# Importing agent configurations from user-defined modules
from agents.user import user  # Imports the user agent configuration
from agents.gemini_agent import Gemini_agent  # Imports the Gemini agent configuration

# Importing the Bureau class from the uagents package
from uagents import Bureau

# The main entry point of the script
if __name__ == "__main__":
    # Creating a Bureau instance with a specified endpoint and port
    # This acts as a central manager for all agents
    bureau = Bureau(endpoint="http://127.0.0.1:5000/submit", port=8000)
    
    # Adding the Gemini_agent to the Bureau's list of managed agents
    bureau.add(Gemini_agent)
    
    # Adding the user agent to the Bureau's list of managed agents
    bureau.add(user)
    
    # Starting the Bureau, which in turn starts and manages the added agents
    bureau.run()
