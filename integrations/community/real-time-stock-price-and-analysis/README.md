
# REAL-TIME STOCK PRICE & ANALYSIS 🤑

## Project Information

Invest with confidence! This agent will analyze the given stock, providing buy/hold/sell recommendations based on their price, volume, trends and technical indicator using yahoo finance api. 

### BUSINESS MODEL: 

 - The market for financial data is crowded. Standing out requires in-depth analysis and valuable insights.
- Investors need access to the latest stock prices to make informed decisions.Real-time data allows them to react quickly to market fluctuations.
 - Users are able to decide whether to buy more or sell shares based on the analysis provided by the recommender.



## Agents Used in our Project

#### Stock_Agent
   - The agent asks the user which stock they want to enquire about. then ask them if they have the stock if yes, then the agent asks them the quantity or ask them how much stock are they interested in buying .
   - The agent then fetches the data about the stock through the Yahoo Finance API, analyzes and predicts the future trend using stockProtocol agent and then gives a detailed description of the stock.

## TechStack Used 📚

- Python
- Fetch.ai uAgent Library
- Yahoo Finance

#

```
/
├── src/
│   └── main.py
├── outputs/
│   ├── 1.jpg
│   ├── 2.jpg
│   ├── 3.jpg
│   ├── 4.jpg
│   └── 5.jpg
└── readme.md
```

## Getting Started 🚀

### Step 1: Obtaining API Keys

1. Yahoo Finance key:

   - Visit the RapidApi website at https://rapidapi.com/manwilbahaa/api/yahoo-finance127
   - Sign up for an account or log in if you already have one.
   - Once logged in, navigate to the dashboard or API section.
   - You'll find your API key in the dashboard or API section.
   - Copy the API key to use it in your applications.

### Step 2: Set API keys and address in agent scripts

    1. Fill in the API keys in the stock agent scripts.
    2. Check for all agent's addresses and replace them at relevant places in the script.

### Step 3: Run project

To run the project locally:

```
git clone https://github.com/Pixathon-Saavyas/MACH-07.git
cd MACH-07/src/
pip install -r requirement.txt 
python agent.py
```

## Screenshots

![App Screenshot](/outputs/1.jpg)

![App Screenshot](/outputs/2.jpg)

![App Screenshot](/outputs/3.jpg)

![App Screenshot](/outputs/4.jpg)

![App Screenshot](/outputs/5.jpg)



## Contibutors: 👨🏻‍💻

```

   1. Sayhan Ali (https://github.com/0xSyhn) [Team Leader]
   2. Palaash Naik (https://github.com/palaashnaik)
   3. Travis Fernandes (https://github.com/travis2319)

```