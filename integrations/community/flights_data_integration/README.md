# uAgent Flight Data integration Examples 

This repository contains examples of live flight data integrations using two agents: `flight_agent` and `user_agent`.

1. `user_agent` : This agent takes flight number request from user, and responds with current flight status and location.

2. `flight_data`: This agent takes flight number from user and sends requests to[Flight Radar API](https://rapidapi.com/apidojo/api/flight-radar1) and gets location and flight details as well. The location coordinates are passed to [Reverse Geocoding](https://rapidapi.com/Noggle/api/reverse-geocoding-and-geolocation-service) to get nearest city.

## Getting Started 🚀

To use these agents, follow the steps below:

### Step 1: Getting API Keys 🔑

Before running the agents, you need to obtain the required API keys:

#### Flight_Radar_API

1. Visit the RapidAPI website: https://rapidapi.com/apidojo/api/flight-radar1
2. If you don't have an account, create one by signing up.
3. Once you are logged in, click on test endpoint and register for API on free-tier.
4. Once done you will see X-RapidAPI-Key in header parameter.

#### Reverse_Geocoding_API

1. Visit the RapidAPI website: https://rapidapi.com/Noggle/api/reverse-geocoding-and-geolocation-service 
2. If you don't have an account, create one by signing up.
3. Once you are logged in, click on test endpoint and register for API on free-tier.
4. Once done you will see X-RapidAPI-Key in header parameter.

### Step 2: Set API Keys and address in agent scripts

1. Fill in the API Keys in the `tfl_agent` scripts.
2. Replace the fligt_data agent address in user agent's script.

### Step 3: Run Project

To run the project and its agents:

```bash
cd src
python main.py
```

Now you have the agents up and running to perform live flights status integrations using the provided APIs. Happy integrating! 🎉