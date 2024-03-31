<div align='center'>
<h1>
🤖 Top News Synopsis: Country-Specific News Summaries at Your Fingertips 🤖
</h1>
</div>

## 1. 🖊️ Description
This project provides live summaries of the top news articles from a specified country. It works by integrating two APIs:
* [News-API](https://newsapi.org/)
* [Rapid-AI's Article Data Extraction and Summarization](https://rapidapi.com/kotartemiy/api/extract-news)

## 2. 🔄 Workflow
The process begins by prompting the user for a country name. It then utilizes the News API to retrieve the top article URL and feeds it into Rapid API's extract news API for scraping and summarizing.

## 3. ⚙️ How to setup the project in [Agentverse.ai](https://agentverse.ai/) and start chatting with [DeltaV](https://deltav.agentverse.ai/) ?
* Obtain API keys for both [News-API](https://newsapi.org/) and [Rapid-AI's Article Data Extraction and Summarization](https://rapidapi.com/kotartemiy/api/extract-news)
* Go to Agentverse Agents, select the `skeleton body`, and name it `scrapper and summarizer`. Copy and paste the code from `scrapper and summarizer.py` in the agents subfolder. Repeat this process for `top_country_article_url_retreiver_agent` and `top_country_article_url_retreiver_agent.py`.
* Don't forget to replace your API keys in the agents. After creating the two agents, click on the run button.
* Create services for agent communication:
  * Navigate to services and create a new service for scraper and summarizer agent:-

    <img width="1470" alt="Screenshot 2024-03-31 at 7 09 46 PM" src="https://github.com/chakka-guna-sekhar-venkata-chennaiah/from-bytes-to-bites/assets/110555361/205fb7a6-349f-45c4-b83c-397ad520c3d8">
    <img width="1470" alt="Screenshot 2024-03-31 at 7 09 50 PM" src="https://github.com/chakka-guna-sekhar-venkata-chennaiah/from-bytes-to-bites/assets/110555361/1f7b03c7-7570-4c3e-88e3-5673731dba98">

  * Repeat the same process for top_country_article_url_retriever_agent.

    <img width="1470" alt="Screenshot 2024-03-31 at 7 12 24 PM" src="https://github.com/chakka-guna-sekhar-venkata-chennaiah/from-bytes-to-bites/assets/110555361/5e34748e-7749-4612-bcb3-1a333d6e3b41">
    <img width="1470" alt="Screenshot 2024-03-31 at 7 12 26 PM" src="https://github.com/chakka-guna-sekhar-venkata-chennaiah/from-bytes-to-bites/assets/110555361/7dc9f929-8def-4387-b9eb-737ed8503c4a">

* Ensure to use the same service group for agent communication.
Once saved, the agents are ready for interaction on the DeltaV platform.
* Once click on save buttoon are agents are ready. It's time to talk with our agents using deltav platform. 
Make sure that to use same email acount for everything what we are doing. 

## 4. 🧪 Testing the agent with DeltaV
* Go to the DeltaV platform, keeping the toggle on developer mode.
* Navigate to the registered service, in this case, `scrapping`.

    <img width="1470" alt="Screenshot 2024-03-31 at 9 11 33 PM" src="https://github.com/chakka-guna-sekhar-venkata-chennaiah/from-bytes-to-bites/assets/110555361/722e5d40-773c-44f1-b2f3-68b091fd5a10">
    <img width="1470" alt="Screenshot 2024-03-31 at 9 11 41 PM" src="https://github.com/chakka-guna-sekhar-venkata-chennaiah/from-bytes-to-bites/assets/110555361/2f083065-2c29-4f97-8eca-0259793a8326">

* Interact with the agent by typing:
    ```
    Give me the today's top most article summary for the specified country?
    ```
Then you will see the output as follow:-
    <img width="1470" alt="Screenshot 2024-03-31 at 10 20 20 PM" src="https://github.com/chakka-guna-sekhar-venkata-chennaiah/from-bytes-to-bites/assets/110555361/a0102348-bac3-48d6-9c96-2bfd87dfcaa0">
* Follow the prompts to select the country and retrieve the top article URL, then view the summary. Keep in mind that the answer may vary depending on the time interval due to the live nature of the News API.
* Resultant Output will look like something!!
  
    <img width="1470" alt="Screenshot 2024-03-31 at 10 20 27 PM" src="https://github.com/chakka-guna-sekhar-venkata-chennaiah/from-bytes-to-bites/assets/110555361/e4524150-62a6-4f46-a8fd-f03f4348776c">


