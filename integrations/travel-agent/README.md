# Integrating TombaAPI with Fetch AI Agent

## Project Information

Tired of sifting through endless Google suggestions for your next trip abroad? Look no further! Our project offers a comprehensive solution for all your travel needs, from destination ideas to flight and accommodation booking. Say goodbye to travel planning headaches and hello to seamless adventures. Let's get started!

## Agents Used in our Project

1. User Agent
   - Optimizes the economic value for users while delivering best options towards user query
2. Destination Recommendation Agent
   - Offers personalized travel destinations that align with user interests which can be further used in other agents
3. Flight Booking Agent
   - Provides the best flight option for the user based on trip date and destination
4. Hotel Booking Agent
   - Provides the best accomodation choices based on the location and budget
   - Gives a list of hotel choices along with their prices and links

## TechStack Used

- Python
- Fetch.ai uAgent Library
- TombaAPI and SerpAPI

## Sample Run

The sample run of our project has been recorded and uploaded at- https://drive.google.com/file/d/1nWJnewQxP0PoMAAp3O2tk6sOVfYxMo_a/view?usp=sharing

## Getting Started

### Step 1: Obtaining API Keys

1. SerpAPI key:

   - Visit the SerpApi website at https://serpapi.com.
   - Sign up for an account or log in if you already have one.
   - Once logged in, navigate to the dashboard or API section.
   - You'll find your API key in the dashboard or API section.
   - Copy the API key to use it in your applications.

2. Tomba API key:
   - Go to the Tomba website at https://www.tomba.io/.
   - Sign up for an account or log in if you already have one.
   - After logging in, go to your account settings or API section.
   - You'll find your Tomba API key in the account settings or API section.
   - Copy the API key to use it in your applications.

### Step 2: Set API keys and address in agent scripts

    1. Fill in the API keys in the flight and hotel booking agent scripts.
    2. Check for all agent's addresses and replace them at relevant places in the script.

### Step 3: Run project

To run the project and its agents:

```
    - go to the directory-> travel-agent / src / agents
    - run -> pyhton travel.py     (in one terminal)
    - run -> python user_agent.py     (in another terminal)

    -- give the prompts in the user_agent terminal

```

Now you have the agents up and running to perform travel planning integrations using the provided APIs. Happy integrating!

## Contibutors:

```
    Shubham Sharma (https://github.com/shukabum)
    Shailesh Kumar (https://github.com/captain-peroxide)
    Sumeet Gaikwad (https://github.com/Sumeet196)
    Yogendra Pandey (https://github.com/McCartney2003)
    Shah Diya Manojkumar (https://github.com/Sumeet196)
```
