Overview
The News Post Generator crafts dynamic social media content tailored for creators. It generates captivating titles, engaging descriptions, and relevant story URLs, accompanied by visually stunning images created using stable diffusion techniques. Once generated, the content is seamlessly posted on the desired social media platform.

Functionality

The system operates through a series of structured steps:

1. The user initiates a request for a new story post via DeltaV.
2. DeltaV interfaces with an agent within the agentverse platform.
3. The agent, known as uagent, executes the following tasks:
   a) Utilizes a news API to retrieve the latest news story.
   b) Processes the story's description through a Language Model (LLM) to adapt it to the preferred style for social media content.
   c) Further refines the description by inputting it into another LLM, creating a prompt suitable for generating a visually appealing image using stable diffusion.
   d) Feeds the generated prompts into a hosted Stable Diffusion model with the SDXL-Lightning checkpoint.
4. The resulting image, along with all pertinent information, is transferred to the offline uagent.
5. The uagent autonomously crafts a post tailored for the selected social media platform."

Steps to Run:

1. Set up an agent and execute agent.py on the agentverse platform.
2. Configure the necessary variables in agents.py and services.py.
3. Install the required Python packages by executing pip install -r requirements.txt within a virtual environment (venv).
4. Launch the server by running python manage.py runserver.
5. Host the server externally (we utilized Playit.gg for this purpose).
6. In a separate terminal, execute discordAgent.py.
7. Use DeltaV to prompt 'Generate a news post'."
