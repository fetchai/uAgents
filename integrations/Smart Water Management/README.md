# Introduction
The Logic Legends team presents a new water management system powered by uAgents designed to solve the problem of wastage of water in farms due to inadeduate information available to the farmers. By leveraging advanced technology and data-driven decision-making, our system ensures optimal water usage for crops at every stage of growth.

# Features
<ol>
  <li>Farm Input: Input crucial farm data such as location, crop type, farm size, soil type, and crop growth stage for precise water management.</li>
  <li>Weather Data Fetch: Using the location data provided, Weather Agent will seek the data from the 7timer API response such as temperature, humidity and rainfall.</li>
  <li>Irrigation Measurements: The amount of water reuired by the plant is fixed but this can be fulfilled by two way: 1. Irrigation 2. Rainfall. The amount of water saved due to rainfall will be predicted in advance.</li>
  <li>Pump Control: Control the irrigation pump efficiently by scheduling irrigation intervals and durations through the Pump Agent, ensuring precise water delivery to crops.</li>
</ol>

# Getting Started
To integrate our system into your environment, update the addresses of the four agents: Weather Agent, Pump Agent, Decider Agent, and User Agent. These addresses should be set in all relevant files where they are referenced. Obtain the address of any agent by accessing the respective agent's file and using the provided snippet.
<code>
  PUMP_ADDRESS = "agent123...."
</code>
To obtain the address of any agent us the followig snippent it the file of that agent.
e.g.
<code>
  print(pump_agent.address) #for pump_agent
</code>
To execute the project run all the 4 python scripts in 4 different terminal (user.py at the end). Then add fill the input details asked in the user.py.

# Overview
This project aims to solve the problem of water wastage at farms by using the weather forecast information such as amount of rainfall, humidity and temperature. This was possible because of the 7timer API for weather forecasting. This will take all the necessary information from the user and send to the decision agent which takes the decision that how much amount of water is fulfilled by rain and what should be irrigated for good nourishment of the crops. This projects leverages the uAgents library and uses its global communication channel Alamanac Contract.
The final actuator is the irrigation pump which can be controlled by the pump_agent according to the instructions received my the decision_agent.
