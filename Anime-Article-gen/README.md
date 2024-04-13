# Anime Article Generation using Anilist API and AI Agents

This project focuses on generating articles Related to anime and manga and it writes the article automatically based on the valid information. The top 10 anime or manga titles for any specified genre using the Anilist API and AI agents is just one use case of this idea we can even implement even more different concepts for articles including examples like fanfiction, latest news and so on by integrating many other APIs with this basic setup module. By leveraging the power of AI, it automates the process of creating engaging and informative content about popular anime and manga, saving time and effort for content creators.

## Use Cases and Benefits

- **Content Creation Automation**: The project automates the process of generating articles, eliminating the need for manual research and writing. This accelerates content creation workflows and allows creators to focus on other tasks.

- **Personalised content**: Users can specify the genre of interest, allowing the system to tailor the generated articles to their preferences. This personalization enhances user experience and engagement.

- **Time-Saving**: By fetching data from the Anilist API and utilizing AI agents for content generation, the project significantly reduces the time required to produce high-quality articles. This enables creators to publish content more frequently and stay ahead of schedule.

- **Quality Assurance**: The use of AI agents ensures that the generated articles are coherent, relevant, and free from grammatical errors. This maintains the quality and professionalism of the content, enhancing its credibility and reader satisfaction.

- **Passive income source**: With even more resources and working we can make an automatic article generator that weekly generates and uploads them based on weekly top 10 or any more ideas, this can be kept as a passive income source.



## Getting Started

To use this project, follow these steps:

1. **Obtain API Keys**: Sign up for an account on Anilist to obtain the necessary API key for accessing their API. Additionally, ensure you have API keys for any other services or platforms used in the project.

2. **Set Up Agent Environment**: Install the required Python packages and dependencies by running `pip install -r requirements.txt` in your project directory.

3. **Replace Placeholder Values**: Replace placeholder values such as agent addresses, seed phrases, and mailbox keys in the provided code with your actual credentials obtained from Anilist and other services.

4. **Run the Code**: Execute the main Python script to run the project. Ensure that all components are configured correctly and running smoothly.

5. **Customize and Expand**: Feel free to customize the code to suit your specific needs or expand the project with additional features or functionalities. Experiment with different AI models or APIs to enhance article generation capabilities.

# A Protoype Model for the top 10 list

We created a succesful Prototype model which gave the desired output in the delta v interface, this was the base model on which we built the rest of the project to give an Idea of Anilist API can be used for passive article generation mainly for Anime and Manga Related article. this protoype model outputs the list of top 10 most popular anime/manga of all time. this can also be integrated with more apis to give weekly statistics of popularity of anime and manga by using the ".on_interval" function.

## Example Usage

```python
# Import necessary classes and modules
from uagents import Agent, Context, Model, Protocol
from pydantic import Field
from ai_engine import UAgentResponse, UAgentResponseType

# Define models, initialize agent, and set up protocols (as shown in the provided code)
...

# Replace placeholder values with actual credentials (as shown in the provided code)
...

# Run the agent to start generating articles
if __name__ == "__main__":
    agent.run()

