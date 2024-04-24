# Project Name ---- WODDY

(your agent for education and learning about new words daily)

# uAgent WordsAPI Integrations Examples

# Requirements

Our challenge today is to integrate WordsAPI with uAgents.

Woddy is a website which has two user base - !. Learner 2. Teacher

1. *Learner* can search any new word and its all around information about the word like syllable, pronunciation, synonyms, results(parts of speech, types of noun) and examples using that word. It can be randomly generated also.
2. *Teacher* assign daily tasks as a new word to learn along with all the features. the student have to answer it on own first and then match the real solution provided by the agents. This will provide them some daily points.

This repository contains examples of WordsAPI integrations using five agents: ` teacher_agent`, `student_agent` ,`random_word_agent` , `search_word_agent` and  `translate_agent`.

1. `teacher_agent`: This agent assign daily task in form of new words to the students.
2. `Student_agent`: This agent helps student finding new words daily. This also helps with the pronunciation , syllables, results(part of speech , type of noun and examples) related to the given word.
3. `random_word_agent`: This agent generate randon words which are given as output to the `teacher_agent` (which he can assign) and   the generated word goes into the assigned word of the `Student_agent` .
4. `search_word_agent`: This agent searches any new word of user's choice and provide the informations(pronunciations, syllable , result, synonyms) related to the searched word.
5. `gemma_agent`: This agent using `hugging_face_API` gives summary and in detail information about the word .

## Getting Started 🚀

To use these agents, follow the steps below:

### Step 1: Obtain API Keys 🔑

Before running the agents, you need to obtain the required API keys:
 `hugging_faceAPI` :
 `rapidAPI` :

(we have given our api for testing purpose in hackathon )

#### WordsAPI

1. Visit the RapidAPI website: https://rapidapi.com/dpventures/api/wordsapi/
2. If you don't have an account, create one by signing up.
3. Once you are logged in, click on test endpoint and register for API on free-tier.
4. Once done you will see X-RapidAPI-Key in header parameter.

### Step 2: Set API Keys and address in agent scripts

1. Fill in the API Keys in the `random_word_agent` and `search_word_agent` scripts.
2. Fill in the API Keys in the `hugging_faceAPI` in the `gemma.py` file.

### Step 3: Run Project

To run the project and its agents:

```bash
cd src
python main.py 


```

this main.py will help you to run three agents at a time and you can leverage their functionality at once

```bash

python teachers.py
```

this command is to run a teacher agent which help you to monitor the students and assign them daily work tasks so they can do it
we can also schedule it periodically .

```bash
python students.py
```

students can perform random word findings , or searching any word they like , agent will help them to find anything they want in a click , it used rapid api and gives all the information about that single word so kid can learn , also we provide a gemma agent to assist with human language .

```bash
python gemma.py
```

The Gemma Agent utilizes Hugging Face's API to generate responses based on given text inputs. It is designed to provide explanations or expansions of input text using the specified Hugging Face model.

### Configuration

1. **Obtain Hugging Face API Token**: Obtain a Hugging Face API token. This token is necessary for accessing the Hugging Face model API. You can either set it as an environment variable named `HUGGING_FACE_ACCESS_TOKEN` or directly replace the default value in the code with your token.

   ```python
   API_TOKEN = os.getenv("HUGGING_FACE_ACCESS_TOKEN", "your_api_token_here")
   ```
2. **Define Model ID**: Define the model ID for the Hugging Face model you want to use. Replace the default value with the desired model ID.

   ```python
   MODEL_ID = "google/gemma-7b"
   ```

### Usage

1. **Run the Gemma Agent script**.

   ```bash
   python gemma_agent.py
   ```
2. **Enter Input Text**: Enter the text you want to get explained when prompted.

   ```bash
   Enter the text to get explained: <your_input_text_here>
   ```
3. **Use Previously Saved Words (Optional)**: Optionally, choose to use previously saved words for generating responses by typing "yes" or "no" when prompted using uagent storage.

   ```python
   word = ctx.storage.get("word")
   ```
4. **Get Explanation Anytime**: You can get explanations of any word anytime using our agent, despite having ChatGPT and together with other agents.

remaining commands like

```bash
python search_random.py
python search_word.py
```

these are our two agents which helps in parsing all information from rapid api to students and teachers
one agent particularly dedicated for one work (randomtext and searching text)

#### Functionality:

work with 5 agents to enhance your knowledge day by day :
we made these agents use in a way that together it ll help you in your everyday vocablury and knowledge
its totally end to end working and all agents working perfectly

### Creativity

We completed this whole idea in 24hours of hackathon despite of travelling 3days in row for this event and joining hackathon jst an hour after reaching,
we tried our best to think of every aspect and this is definitly a great solution for those who lack in vocabulury , the real life use cases of these agents are broad , we would ve implemented gui too but it was against the structure of hackathon directory file rules.

### code quality

we maintained every comment and structure of the code to enhance our code quality

#### Features

1. **Interactive Learning Experience**: Woddy provides a gamified learning experience with daily tasks and engaging activities, fostering active participation and retention.
2. **Comprehensive Word Information**: Unlike some platforms that focus solely on pronunciation, Woddy offers comprehensive word information including syllables, synonyms, and usage examples, enriching users' understanding of vocabulary.
3. **uses five- six different agents**: More agents leads to lack of coordination , but it is seems that woddy is better in coordinating.

#### Use cases

1. *Student Learning Journey*: Students can explore new words daily, improve pronunciation, and deepen their understanding of language nuances.
2. *Teacher-Student Interaction*: Teachers assign daily tasks to students, monitor their progress, and provide feedback to facilitate continuous learning.
3. *Language Skill Enhancement*: Woddy serves as a valuable tool for enhancing language skills, aiding users in becoming effective communicators.
4. *Engaging Learning Activities*: The platform offers engaging learning activities such as games and quizzes to make the learning process fun and interactive.

### Competitiors

1. **Vocabify**: A similar platform offering word-learning features, quizzes, and interactive exercises.
2. **WordMaster**: Another word-learning app with a focus on vocabulary building and language enhancement.

# Why this

Comprehensive Word Information: Woddy provides users with comprehensive word information, including syllables, pronunciation, synonyms, parts of speech, types of nouns, and usage examples. This depth of detail sets Woddy apart, offering users a richer learning experience compared to competitors in the market.

### Future Scope & limitations

Due to the restrictions of using the given structure only in the fetch AI problem statement, it is needed to keep up with the labled stucture and not integrate any GUI in the product for the evaluation.
Though, we can present it as a complete product with understable pages. Here is the example of the UI/ UX we have completed for now.

Now you have the agents up and running to perform a learning platform integrations using the provided APIs. Happy integrating! 🎉

## Frotend GUI : https://github.com/Rajnandini3847/IIT-Roorkee.git


![Screenshot 1](https://github.com/Rajnandini3847/IIT-Roorkee/raw/main/image/Screenshot%202024-03-16%20100924.png)

![Screenshot 2](https://github.com/Rajnandini3847/IIT-Roorkee/raw/main/image/Screenshot%202024-03-16%20100955.png)

![Screenshot 3](https://github.com/Rajnandini3847/IIT-Roorkee/raw/main/image/Screenshot%202024-03-16%20101013.png)

![Screenshot 4](https://github.com/Rajnandini3847/IIT-Roorkee/raw/main/image/Screenshot%202024-03-16%20101124.png)

Team Name = Codex
built in AgentX IIT Roorkee cognizance
Built by :- Akash Verma , Rajnandini Tiwari
