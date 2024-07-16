import os, sys
sys.path.append(os.getcwd())
from src.agents.user import user
from src.agents.room_agent import room
from uagents import Bureau


bureau = Bureau()   # This will allow us to run agents together in the same script
bureau.add(user)
bureau.add(room)

if __name__ == "__main__":
    bureau.run()