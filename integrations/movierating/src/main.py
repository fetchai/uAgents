# main program
# import required libraries
from agent1 import agent1
from agent2 import agent2
from uagents import Bureau

#adding all users to bureau and running it
if __name__ == "__main__":
    bureau = Bureau()
    bureau.add(agent1)
    bureau.add(agent2)
    bureau.run()