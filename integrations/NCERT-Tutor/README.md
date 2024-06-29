# Incognito Tab - Goa College of Engineering NCERT Tutor Video Demo

### You can watch a video demo of our project: [demo video](https://drive.google.com/drive/folders/175eGJjyQfFjJ36Qk0ACPx_CXWFQbdVnE?usp=drive_link)

## Vision of our project
- To simplify and improve learning attitude and aptitude
- To reach many students with all the help ncessary to ace thier exams
- To simplify and have the tedious tasks of memorizing and concept revision done easy with autonomous agents.

## Future scopes of your project
- To create a more conversational and seamless experience  by allowing the user to ask further questions about the chapter and get those included in the notes aswell by implementing the experimental [Dialogue module](https://github.com/Quantaindew/uAgents/blob/main/integrations/fetch-ai-engine/src/ai_engine/chitchat.py)
- To implement an additional feature that lets the user also practice questions with the help of flashcards , this will be an interactive experience   for the user to retain concepts and revise quicker .



  

## Project Information

### Abstract
Our project, NCERT Tutor, is designed to simplify the learning process by providing a personalized tutoring experience. It asks the user for their class, subject, and chapter they want to learn or have a doubt in, then fetches the corresponding chapter PDF from the NCERT website, summarizes the content, and creates notes along with important questions through a seamless interaction enabled via delta v. The agents in our project deployed on Agentverse is fully operational through Delta V.


### Agents used in our Project
- **Interact Agent**
  - The first pillar and the initiator of the entire sequence of the workflow based on the user input done through delta v.
  - Aims to maximize the educational value of the user while also providing the best options towards user query
  - Uses functions to summarize and create question banks and an answer key stored seperately so it's not revealed immediately.
``question.py``


### Sample Flow of our NCERT Tutor
1. User inputs their class, subject, and chapter.
2. User Agent captures the input and calls the NCERT Content Fetcher to retrieve the chapter PDF.
3. Agent fetches the PDF and passes it to the Content Summarizer.
4. Content Summarizer summarizes the content  also creates the notes in a pretty format for the user and provides a dynamic sharable link to download the content and passes it to the Agent.
5. Agent displays the sharable link to the notes along with the content to the user thus completing the  end to end user experience.

## Content of PPt:
attached ppt [here](https://drive.google.com/drive/folders/1r4pfuj_JTewEugUCTG1PW8giDpIhO7qm?usp=drive_link) 



## Technology Stack
- Python
- Fetch.ai
- uAgent Library
- Agentverse
- Mailroom
- Delta v

## Getting Started


### Installation
1. Clone the repository:

```
git clone https://github.com/fetchai/uAgents.git
```

2. Change directory into project
```
cd integrations/NCERT-Tutor
```

3.Initialize the environment by installing dependecies:

```
poetry install
```
4.Initialize the environment Run the backend server:
```
 cd src/agents/utils
 poetry shell
 uvicorn ncert:app --reload --port 8080
```
5.Initializing the environment and running the ecosystem of the agent :



```
cd src/agents/conversation
poetry shell
python ncertagent.py
```

Run the above commands in order in different terminals

#### **After The agent runs you need to take the address it prints and get a key by registering it in mailroom and replace it with the AGENT_MAILBOX_KEY in the Agent file**  


###
Reminder: that openai requires a gpt4 api key which needs to be put into the .env file in the same directory as the agent (you will find a .env-template file)
###

reminder: for the conversation agent demo to run locally , you will need to uncomment the hardcoded query 👇
``` python
@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("Question System Agent Started")
    ctx.logger.info(f"{agent.address}")

    ##Local Testing code snippet, uncomment the code below to run locally
    #intentionally added typo to test levenshtien distance algorithm
    #chapter_name = "alice in wonland"
    #chapter_num = find_chapter_number(chapter_name)
    #standard = 4
    #ctx.logger.info(f"Chapter Name : {chapter_name}, Chapter number: {chapter_num}, standard: {standard}")
    #message = send_pdf_content(ctx,agent.address, Question(question = f"Can you provide a summary of the chapter {chapter_name} from standard {standard} English?", chapter = chapter_num, subject = "english", standard = standard))
    
  # uncomment this ☝️ query to run the demo locally.

```




